import os
import json
import pyotp
import qrcode
from cryptography.fernet import Fernet

VAULT_FILE = "mfa_vault.json"

def generate_mfa_seed() -> str:
    """Generates a random Base32 seed for Google Authenticator."""
    return pyotp.random_base32()

def get_provisioning_uri(seed: str, username: str="User") -> str:
    """Gets the URI used to generate the QR Code."""
    return pyotp.totp.TOTP(seed).provisioning_uri(name=username, issuer_name="CipherShield")

def generate_qr_code(uri: str, output_path: str="mfa_qr.png") -> bool:
    """Generates a QR code image from the provisioning URI."""
    try:
        qr = qrcode.make(uri)
        qr.save(output_path)
        return True
    except Exception as e:
        print(f"QR Error: {e}")
        return False

def setup_vault(seed: str, first_code: str) -> tuple[bool, str]:
    """
    Verifies the first code, and if successful, generates a Master Key
    and stores it securely in the vault file alongside the encrypted seed.
    In a real app, the seed itself would be encrypted by a hardware TPM,
    but for this project, we store it in a JSON file to simulate the Vault.
    """
    totp = pyotp.TOTP(seed)
    if not totp.verify(first_code):
        return False, "Invalid MFA Code. Setup failed."
    
    # Generate the perfect 32-byte Master Key
    master_key = Fernet.generate_key().decode('utf-8')
    
    vault_data = {
        "mfa_seed": seed,
        "master_key": master_key
    }
    
    try:
        with open(VAULT_FILE, 'w') as f:
            json.dump(vault_data, f)
        return True, "Vault configured successfully!"
    except Exception as e:
        return False, f"Failed to save vault: {e}"

def is_vault_configured() -> bool:
    return os.path.exists(VAULT_FILE)

def unlock_vault(mfa_code: str) -> tuple[bool, str]:
    """
    Attempts to unlock the vault using the 6-digit MFA code.
    Returns (True, MasterKey) if successful, (False, ErrorMsg) if not.
    """
    if not is_vault_configured():
        return False, "Vault is not configured."
        
    try:
        with open(VAULT_FILE, 'r') as f:
            vault_data = json.load(f)
            
        seed = vault_data.get("mfa_seed")
        master_key = vault_data.get("master_key")
        
        if not seed or not master_key:
            return False, "Vault is corrupted."
            
        totp = pyotp.TOTP(seed)
        if totp.verify(mfa_code):
            return True, master_key.encode('utf-8')
        else:
            return False, "Invalid MFA Code. Vault remains locked."
            
    except Exception as e:
        return False, f"Vault error: {e}"

def encrypt_with_vault(file_path: str, mfa_code: str) -> tuple[bool, str]:
    """Unlocks vault and encrypts the file."""
    ok, key_or_msg = unlock_vault(mfa_code)
    if not ok:
        return False, key_or_msg
        
    try:
        fernet = Fernet(key_or_msg)
        with open(file_path, 'rb') as f:
            data = f.read()
        encrypted = fernet.encrypt(data)
        out_path = file_path + ".enc"
        with open(out_path, 'wb') as f:
            f.write(encrypted)
        return True, out_path
    except Exception as e:
        return False, f"Vault encryption failed: {e}"

def decrypt_with_vault(file_path: str, mfa_code: str) -> tuple[bool, str]:
    """Unlocks vault and decrypts the file."""
    ok, key_or_msg = unlock_vault(mfa_code)
    if not ok:
        return False, key_or_msg
        
    try:
        fernet = Fernet(key_or_msg)
        with open(file_path, 'rb') as f:
            data = f.read()
        decrypted = fernet.decrypt(data)
        out_path = file_path[:-4] if file_path.endswith(".enc") else file_path + ".decrypted"
        if os.path.exists(out_path):
            out_path += ".restored"
        with open(out_path, 'wb') as f:
            f.write(decrypted)
        return True, out_path
    except pyotp.errors.InvalidToken:
        return False, "Invalid Vault Token."
    except Exception as e:
        return False, f"Vault decryption failed: {e}"
