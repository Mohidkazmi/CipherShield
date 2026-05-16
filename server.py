"""
server.py - FastAPI Web Backend
================================
Secure File Encryption System | Information Security Project

This module exposes all cryptographic operations as REST API endpoints.
The frontend (HTML/JS) communicates with these endpoints via AJAX calls.
"""

import os
import io
import tempfile
import shutil
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import hybrid_crypto
import digital_signature
import key_manager
from hashing import hash_sha256, hash_md5, hash_file_sha256
from encrypt import encrypt_file, decrypt_file

app = FastAPI(title="Hybrid Shield — Secure File Encryption System")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# On Vercel, we can only write to /tmp
if os.environ.get("VERCEL") == "1":
    UPLOAD_DIR = "/tmp/uploads"
else:
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "keys"), exist_ok=True)

# Static files & templates using absolute paths
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# ─── Helper: save upload to temp file ──────────────────────────────────────────

def _save_upload(upload: UploadFile, folder: str = UPLOAD_DIR) -> str:
    """Saves an uploaded file to disk and returns its path."""
    path = os.path.join(folder, upload.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return path



# ─── Pages ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


# ─── RSA Key Generation ───────────────────────────────────────────────────────

@app.post("/api/generate-keys")
async def api_generate_keys(label: str = Form("Default Key")):
    """Generates an RSA key pair and registers it in the Key Manager."""
    try:
        folder = os.path.join(UPLOAD_DIR, "keys")
        os.makedirs(folder, exist_ok=True)

        priv_pem, pub_pem = hybrid_crypto.generate_rsa_keys()
        priv_path, pub_path = hybrid_crypto.save_keys(priv_pem, pub_pem, folder)
        entry = key_manager.add_key(label, priv_path, pub_path)
        return JSONResponse({
            "success": True,
            "message": f"RSA-2048 Key Pair '{label}' generated!",
            "key": entry
        })
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.get("/api/keys")
async def api_list_keys():
    """Returns all registered keys."""
    return JSONResponse({"keys": key_manager.list_keys()})


@app.post("/api/delete-key")
async def api_delete_key(key_id: int = Form(...)):
    ok = key_manager.delete_key(key_id)
    return JSONResponse({"success": ok})


@app.get("/api/download-key/{key_id}/{key_type}")
async def api_download_key(key_id: int, key_type: str):
    """Downloads a public or private key file."""
    entry = key_manager.get_key(key_id)
    if not entry:
        return JSONResponse({"success": False, "message": "Key not found"}, status_code=404)
    path = entry["pub_path"] if key_type == "public" else entry["priv_path"]
    if not os.path.exists(path):
        return JSONResponse({"success": False, "message": "Key file missing from disk"}, status_code=404)
    return FileResponse(path, filename=os.path.basename(path))


# ─── Hybrid Encryption ────────────────────────────────────────────────────────

@app.post("/api/hybrid-encrypt")
async def api_hybrid_encrypt(file: UploadFile = File(...), key_id: int = Form(...)):
    """Encrypts a file using Hybrid RSA + AES-GCM."""
    try:
        entry = key_manager.get_key(key_id)
        if not entry:
            return JSONResponse({"success": False, "message": "Key not found"}, status_code=404)

        file_path = _save_upload(file)
        ok, result = hybrid_crypto.hybrid_encrypt(file_path, entry["pub_path"])
        os.remove(file_path)  # Clean up original upload

        if ok:
            return FileResponse(result, filename=os.path.basename(result),
                                media_type="application/octet-stream")
        else:
            return JSONResponse({"success": False, "message": result}, status_code=400)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.post("/api/hybrid-decrypt")
async def api_hybrid_decrypt(file: UploadFile = File(...), key_id: int = Form(...)):
    """Decrypts a .hyb file using Hybrid RSA + AES-GCM."""
    try:
        entry = key_manager.get_key(key_id)
        if not entry:
            return JSONResponse({"success": False, "message": "Key not found"}, status_code=404)

        file_path = _save_upload(file)
        ok, result = hybrid_crypto.hybrid_decrypt(file_path, entry["priv_path"])
        os.remove(file_path)

        if ok:
            return FileResponse(result, filename=os.path.basename(result),
                                media_type="application/octet-stream")
        else:
            return JSONResponse({"success": False, "message": result}, status_code=400)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


# ─── Digital Signatures ───────────────────────────────────────────────────────

@app.post("/api/sign-file")
async def api_sign_file(file: UploadFile = File(...), key_id: int = Form(...)):
    """Signs a file using RSA-PSS."""
    try:
        entry = key_manager.get_key(key_id)
        if not entry:
            return JSONResponse({"success": False, "message": "Key not found"}, status_code=404)

        file_path = _save_upload(file)
        ok, result = digital_signature.sign_file(file_path, entry["priv_path"])
        os.remove(file_path)

        if ok:
            return FileResponse(result, filename=os.path.basename(result),
                                media_type="application/octet-stream")
        else:
            return JSONResponse({"success": False, "message": result}, status_code=400)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.post("/api/verify-signature")
async def api_verify_sig(
    file: UploadFile = File(...),
    signature: UploadFile = File(...),
    key_id: int = Form(...)
):
    """Verifies a digital signature."""
    try:
        entry = key_manager.get_key(key_id)
        if not entry:
            return JSONResponse({"success": False, "message": "Key not found"}, status_code=404)

        file_path = _save_upload(file)
        sig_path = _save_upload(signature)
        ok, msg = digital_signature.verify_signature(file_path, sig_path, entry["pub_path"])
        os.remove(file_path)
        os.remove(sig_path)
        return JSONResponse({"success": ok, "message": msg})
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


# ─── Hashing ──────────────────────────────────────────────────────────────────

@app.post("/api/hash-text")
async def api_hash_text(text: str = Form(...), algorithm: str = Form("sha256")):
    if algorithm == "sha256":
        h = hash_sha256(text)
    else:
        h = hash_md5(text)
    return JSONResponse({"hash": h, "algorithm": algorithm.upper()})


@app.post("/api/hash-file")
async def api_hash_file(file: UploadFile = File(...)):
    file_path = _save_upload(file)
    h = hash_file_sha256(file_path)
    os.remove(file_path)
    return JSONResponse({"hash": h, "filename": file.filename})


# ─── AES Symmetric (Legacy) ──────────────────────────────────────────────────

@app.post("/api/aes-encrypt")
async def api_aes_encrypt(file: UploadFile = File(...), password: str = Form(...)):
    try:
        file_path = _save_upload(file)
        ok, result = encrypt_file(file_path, password)
        os.remove(file_path)
        if ok:
            return FileResponse(result, filename=os.path.basename(result),
                                media_type="application/octet-stream")
        return JSONResponse({"success": False, "message": result}, status_code=400)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)


@app.post("/api/aes-decrypt")
async def api_aes_decrypt(file: UploadFile = File(...), password: str = Form(...)):
    try:
        file_path = _save_upload(file)
        ok, result = decrypt_file(file_path, password)
        os.remove(file_path)
        if ok:
            return FileResponse(result, filename=os.path.basename(result),
                                media_type="application/octet-stream")
        return JSONResponse({"success": False, "message": result}, status_code=400)
    except Exception as e:
        return JSONResponse({"success": False, "message": str(e)}, status_code=500)
