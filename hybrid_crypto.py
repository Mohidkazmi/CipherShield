"""
hybrid_crypto.py - Hybrid Cryptography Engine
===============================================
Secure File Encryption System | Information Security Project

CONCEPT: Why Hybrid Cryptography?
-  PROBLEM with Asymmetric (RSA) alone: RSA is slow and can only encrypt
   small amounts of data (limited by key size).
-  PROBLEM with Symmetric (AES) alone: How do you securely share the key?
   If the key is intercepted, all data is compromised.
-  SOLUTION — Hybrid: Use AES to encrypt the (large) data quickly, and then
   use RSA to encrypt only the (small) AES key securely.

ENCRYPTION PROCESS:
  1. Generate a random 256-bit AES session key (one-time use).
  2. Encrypt the file data with AES-256-GCM (fast, authenticated).
  3. Encrypt the AES key with the recipient's RSA-2048 Public Key (OAEP).
  4. Bundle into one .hyb file: [MAGIC][enc_key_len][enc_key][nonce][ciphertext]

DECRYPTION PROCESS:
  1. Parse the .hyb bundle.
  2. Decrypt the AES key using the RSA Private Key.
  3. Use the recovered AES key to decrypt the file data.

ALGORITHMS:
  - RSA-2048 with OAEP padding (SHA-256) for key encapsulation.
  - AES-256-GCM for authenticated symmetric encryption.
    (GCM provides both confidentiality AND integrity — any tampering is detected.)
"""

import os
import struct
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

# File format identifier — first 6 bytes of every .hyb file
MAGIC_BYTES = b"HYBV01"
RSA_KEY_SIZE = 2048


# ─── RSA Key Generation ────────────────────────────────────────────────────────

def generate_rsa_keys() -> tuple[bytes, bytes]:
    """
    Generates a 2048-bit RSA key pair.

    Returns:
        (private_pem_bytes, public_pem_bytes)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,       # Standard public exponent
        key_size=RSA_KEY_SIZE,       # 2048-bit key
        backend=default_backend()
    )

    # Serialize Private Key (PKCS8 format, no password protection)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize Public Key (SubjectPublicKeyInfo format)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem, public_pem


def save_keys(private_pem: bytes, public_pem: bytes,
              folder: str = ".") -> tuple[str, str]:
    """Saves RSA keys as PEM files to the specified folder."""
    priv_path = os.path.join(folder, "private_key.pem")
    pub_path  = os.path.join(folder, "public_key.pem")

    with open(priv_path, "wb") as f:
        f.write(private_pem)
    with open(pub_path, "wb") as f:
        f.write(public_pem)

    return priv_path, pub_path


def get_key_info(pem_path: str) -> dict:
    """Returns basic metadata about a PEM key file."""
    try:
        with open(pem_path, "rb") as f:
            data = f.read()

        if b"PRIVATE" in data:
            key = serialization.load_pem_private_key(
                data, password=None, backend=default_backend()
            )
            pub = key.public_key()
            return {
                "type": "Private Key",
                "algorithm": "RSA",
                "bits": pub.key_size,
                "path": pem_path
            }
        else:
            key = serialization.load_pem_public_key(
                data, backend=default_backend()
            )
            return {
                "type": "Public Key",
                "algorithm": "RSA",
                "bits": key.key_size,
                "path": pem_path
            }
    except Exception as e:
        return {"type": "Unknown", "error": str(e), "path": pem_path}


# ─── Hybrid Encryption ─────────────────────────────────────────────────────────

def hybrid_encrypt(file_path: str, public_key_path: str) -> tuple[bool, str]:
    """
    Encrypts a file using RSA + AES-256-GCM hybrid encryption.

    Bundle format (written to .hyb file):
      [MAGIC_BYTES 6]
      [enc_key_len  4 bytes big-endian]
      [enc_aes_key  enc_key_len bytes]   ← RSA-OAEP encrypted AES key
      [nonce        12 bytes]            ← AES-GCM nonce
      [ciphertext   remaining bytes]     ← AES-GCM encrypted data + 16-byte auth tag

    Returns:
        (True, output_path) or (False, error_message)
    """
    try:
        # 1. Load RSA Public Key
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(
                f.read(), backend=default_backend()
            )

        # 2. Generate a random 256-bit AES session key (one-time use)
        aes_key = AESGCM.generate_key(bit_length=256)
        aesgcm  = AESGCM(aes_key)

        # 3. Read the plaintext file
        with open(file_path, "rb") as f:
            plaintext = f.read()

        # 4. Encrypt data with AES-256-GCM
        nonce      = os.urandom(12)                        # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)  # includes 128-bit auth tag

        # 5. Encrypt the AES key with RSA-OAEP
        encrypted_aes_key = public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # 6. Write .hyb bundle
        output_path = file_path + ".hyb"
        with open(output_path, "wb") as f:
            f.write(MAGIC_BYTES)
            f.write(struct.pack(">I", len(encrypted_aes_key)))
            f.write(encrypted_aes_key)
            f.write(nonce)          # Always 12 bytes, no length prefix needed
            f.write(ciphertext)

        return True, output_path

    except FileNotFoundError as e:
        return False, f"File not found: {str(e)}"
    except ValueError as e:
        return False, f"Invalid public key file: {str(e)}"
    except Exception as e:
        return False, f"Hybrid Encryption Failed: {str(e)}"


# ─── Hybrid Decryption ─────────────────────────────────────────────────────────

def hybrid_decrypt(file_path: str, private_key_path: str) -> tuple[bool, str]:
    """
    Decrypts a .hyb file using the RSA private key + AES-256-GCM.

    Returns:
        (True, output_path) or (False, error_message)
    """
    try:
        # 1. Load RSA Private Key
        with open(private_key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )

        # 2. Read and parse the .hyb bundle
        with open(file_path, "rb") as f:
            # Verify magic bytes
            magic = f.read(len(MAGIC_BYTES))
            if magic != MAGIC_BYTES:
                return False, "Not a valid .hyb file (magic bytes mismatch)."

            # Read encrypted AES key
            enc_key_len       = struct.unpack(">I", f.read(4))[0]
            encrypted_aes_key = f.read(enc_key_len)

            # Read nonce (always 12 bytes)
            nonce = f.read(12)

            # Rest is ciphertext (includes AES-GCM authentication tag)
            ciphertext = f.read()

        # 3. Decrypt AES key with RSA Private Key
        aes_key = private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        # 4. Decrypt data with AES-256-GCM
        # If data was tampered, this raises an exception (integrity guarantee)
        aesgcm    = AESGCM(aes_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        # 5. Determine output path
        if file_path.endswith(".hyb"):
            output_path = file_path[:-4]
        else:
            output_path = file_path + ".decrypted"

        if os.path.exists(output_path):
            base, ext   = os.path.splitext(output_path)
            output_path = base + "_restored" + ext

        with open(output_path, "wb") as f:
            f.write(plaintext)

        return True, output_path

    except FileNotFoundError as e:
        return False, f"File not found: {str(e)}"
    except ValueError as e:
        return False, f"Decryption failed — wrong private key or corrupted file."
    except Exception as e:
        # AES-GCM tag failure also raises here
        return False, f"Hybrid Decryption Failed: {str(e)}"
