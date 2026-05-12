"""
encrypt.py - File Encryption and Decryption Module
====================================================
CipherShield | Information Security Project

CONCEPT: What is Encryption?
- Encryption converts readable data (plaintext) into an unreadable format (ciphertext).
- Only someone with the correct key can decrypt it back to the original.
- This is REVERSIBLE — unlike hashing.

CONCEPT: What is AES?
- AES (Advanced Encryption Standard) is a symmetric encryption algorithm.
- It uses the SAME key for both encryption and decryption.
- Fernet (from the 'cryptography' library) implements AES-128 in CBC mode with HMAC.
- It is currently the industry standard for secure symmetric encryption.

CONCEPT: Symmetric Encryption
- Same key encrypts and decrypts data.
- Fast and efficient — suitable for encrypting large files.
- The challenge: both parties must securely share the key.
"""

import os
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64


# ─── Key Derivation ────────────────────────────────────────────────────────────

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derives a secure 32-byte key from a user password using PBKDF2.

    Why PBKDF2?
    - Passwords are weak. PBKDF2 stretches them into strong cryptographic keys.
    - 'Salt' ensures the same password produces a different key each time.
    - 100,000 iterations make brute-force attacks very slow.

    Returns:
        A URL-safe base64-encoded 32-byte key (required by Fernet).
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),      # Hash function used internally
        length=32,                       # Output key length (32 bytes = 256 bits)
        salt=salt,                       # Random salt to prevent rainbow-table attacks
        iterations=50_000,              # Number of hashing rounds (slows brute-force)
        backend=default_backend()
    )
    # Fernet requires URL-safe base64-encoded key
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


# ─── File Encryption ───────────────────────────────────────────────────────────

def encrypt_file(file_path: str, password: str) -> tuple[bool, str]:
    """
    Encrypts a file using AES encryption (via Fernet).

    Process:
    1. Generate a random 16-byte salt.
    2. Derive a key from the password + salt using PBKDF2.
    3. Read the original file bytes.
    4. Encrypt the bytes using Fernet (AES).
    5. Save: [salt (16 bytes)] + [encrypted data] as a .enc file.

    Args:
        file_path: Path to the file to encrypt.
        password: User-provided password.

    Returns:
        (True, output_path) on success, or (False, error_message) on failure.
    """
    try:
        # Step 1: Generate a random salt (different each time = different key each time)
        salt = os.urandom(16)

        # Step 2: Derive encryption key from password + salt
        key = derive_key(password, salt)
        fernet = Fernet(key)

        # Step 3: Read original file
        with open(file_path, 'rb') as f:
            original_data = f.read()

        # Step 4: Encrypt the data
        encrypted_data = fernet.encrypt(original_data)

        # Step 5: Save salt + encrypted data to .enc file
        output_path = file_path + ".enc"
        with open(output_path, 'wb') as f:
            f.write(salt + encrypted_data)  # First 16 bytes = salt, rest = cipher

        return True, output_path

    except FileNotFoundError:
        return False, "Error: File not found. Please select a valid file."
    except PermissionError:
        return False, "Error: Permission denied. Cannot read the selected file."
    except Exception as e:
        return False, f"Encryption failed: {str(e)}"


# ─── File Decryption ───────────────────────────────────────────────────────────

def decrypt_file(file_path: str, password: str) -> tuple[bool, str]:
    """
    Decrypts a .enc file using AES decryption (via Fernet).

    Process:
    1. Read the file: first 16 bytes = salt, rest = encrypted data.
    2. Re-derive the key from password + salt.
    3. Attempt decryption using Fernet.
    4. Save the decrypted file (remove .enc extension).

    Args:
        file_path: Path to the .enc file.
        password: User-provided password (must match encryption password).

    Returns:
        (True, output_path) on success, or (False, error_message) on failure.
    """
    try:
        # Step 1: Read encrypted file
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Extract salt (first 16 bytes) and cipher text (rest)
        salt = file_data[:16]
        encrypted_data = file_data[16:]

        # Step 2: Re-derive key using the same salt
        key = derive_key(password, salt)
        fernet = Fernet(key)

        # Step 3: Decrypt — raises InvalidToken if password is wrong
        decrypted_data = fernet.decrypt(encrypted_data)

        # Step 4: Save decrypted file (remove .enc extension if present)
        if file_path.endswith(".enc"):
            output_path = file_path[:-4]  # Remove last 4 characters (.enc)
        else:
            output_path = file_path + ".decrypted"

        # Avoid overwriting existing files
        if os.path.exists(output_path):
            output_path = output_path + ".restored"

        with open(output_path, 'wb') as f:
            f.write(decrypted_data)

        return True, output_path

    except InvalidToken:
        # This happens when the wrong password is entered
        return False, "Error: Wrong password! Decryption failed.\nThe file could not be decrypted with the provided password."
    except FileNotFoundError:
        return False, "Error: Encrypted file not found."
    except Exception as e:
        return False, f"Decryption failed: {str(e)}"


# ─── Key File Authentication (Alternative to Passwords) ─────────────────────────

def generate_key_file(output_path: str) -> bool:
    """
    Generates a cryptographically secure 32-byte key and saves it to a file.
    This eliminates the need for humans to remember passwords.
    """
    try:
        key = Fernet.generate_key()
        with open(output_path, 'wb') as f:
            f.write(key)
        return True
    except Exception:
        return False

def encrypt_file_with_key(file_path: str, key_path: str) -> tuple[bool, str]:
    """
    Encrypts a file using a pre-generated key file.
    Notice that we DO NOT need a salt here, because the key is already 
    a perfectly random 32-byte string (unlike weak human passwords).
    """
    try:
        with open(key_path, 'rb') as f:
            key = f.read()
            
        fernet = Fernet(key)
        
        with open(file_path, 'rb') as f:
            original_data = f.read()
            
        encrypted_data = fernet.encrypt(original_data)
        
        output_path = file_path + ".enc"
        with open(output_path, 'wb') as f:
            f.write(encrypted_data)
            
        return True, output_path

    except FileNotFoundError:
        return False, "Error: File or Key not found."
    except ValueError:
        return False, "Error: The selected key file is invalid."
    except Exception as e:
        return False, f"Encryption failed: {str(e)}"

def decrypt_file_with_key(file_path: str, key_path: str) -> tuple[bool, str]:
    """Decrypts a file using a pre-generated key file."""
    try:
        with open(key_path, 'rb') as f:
            key = f.read()
            
        fernet = Fernet(key)
        
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
            
        decrypted_data = fernet.decrypt(encrypted_data)
        
        if file_path.endswith(".enc"):
            output_path = file_path[:-4]
        else:
            output_path = file_path + ".decrypted"
            
        if os.path.exists(output_path):
            output_path = output_path + ".restored"
            
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
            
        return True, output_path

    except InvalidToken:
        return False, "Error: Wrong key file! Decryption failed."
    except FileNotFoundError:
        return False, "Error: File or Key not found."
    except ValueError:
        return False, "Error: The selected key file is invalid."
    except Exception as e:
        return False, f"Decryption failed: {str(e)}"
