"""
digital_signature.py - RSA Digital Signature Module
=====================================================
Secure File Encryption System | Information Security Project

CONCEPT: Digital Signatures
- Proves AUTHENTICITY: Confirms who created or approved the file.
- Proves INTEGRITY: Confirms the file has not been tampered with.
- Non-Repudiation: The signer cannot later deny having signed the file.

HOW IT WORKS (RSA-PSS):
1. The signer computes a SHA-256 hash of the file.
2. The hash is encrypted with the signer's PRIVATE key → this is the signature.
3. The verifier decrypts the signature with the signer's PUBLIC key → gets hash.
4. The verifier independently hashes the received file.
5. If both hashes match → Signature VALID → file is authentic.

ALGORITHM: RSA-PSS (Probabilistic Signature Scheme) with SHA-256
- PSS adds a random salt, making each signature unique even for the same file.
- Far more secure than the older PKCS#1 v1.5 signature scheme.
"""

import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature


def sign_file(file_path: str, private_key_path: str) -> tuple[bool, str]:
    """
    Signs a file using RSA-PSS with SHA-256.
    Creates a companion .sig file alongside the original.

    Args:
        file_path:        Path to the file to be signed.
        private_key_path: Path to the RSA private key PEM file.

    Returns:
        (True, sig_path) on success, (False, error_message) on failure.
    """
    try:
        # Step 1: Load the RSA Private Key
        with open(private_key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )

        # Step 2: Read the full file content
        with open(file_path, "rb") as f:
            data = f.read()

        # Step 3: Sign using RSA-PSS with SHA-256
        # The library internally hashes the data with SHA-256, then signs the hash.
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH  # Maximum security
            ),
            hashes.SHA256()
        )

        # Step 4: Save the raw signature bytes to a .sig file
        sig_path = file_path + ".sig"
        with open(sig_path, "wb") as f:
            f.write(signature)

        return True, sig_path

    except FileNotFoundError as e:
        return False, f"File not found: {str(e)}"
    except ValueError as e:
        return False, f"Invalid key file — ensure it is a valid PEM private key."
    except Exception as e:
        return False, f"Signing failed: {str(e)}"


def verify_signature(file_path: str, sig_path: str, public_key_path: str) -> tuple[bool, str]:
    """
    Verifies an RSA-PSS signature against a file.

    Args:
        file_path:       Path to the original file to verify.
        sig_path:        Path to the .sig signature file.
        public_key_path: Path to the RSA public key PEM file.

    Returns:
        (True, success_message) if valid, (False, error_message) if invalid.
    """
    try:
        # Step 1: Load RSA Public Key
        with open(public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(
                f.read(), backend=default_backend()
            )

        # Step 2: Read the file and the signature
        with open(file_path, "rb") as f:
            data = f.read()

        with open(sig_path, "rb") as f:
            signature = f.read()

        # Step 3: Verify — raises InvalidSignature if tampered
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return True, "✔  SIGNATURE VALID — File is authentic and unmodified."

    except InvalidSignature:
        return False, "✖  SIGNATURE INVALID — File may have been modified, or wrong key used."
    except FileNotFoundError as e:
        return False, f"File not found: {str(e)}"
    except ValueError:
        return False, "Invalid key file — ensure it is a valid PEM public key."
    except Exception as e:
        return False, f"Verification error: {str(e)}"
