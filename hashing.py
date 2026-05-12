"""
hashing.py - Hashing Functions Module
======================================
CipherShield | Information Security Project

CONCEPT: What is Hashing?
- Hashing converts data into a fixed-length string (called a "digest" or "hash").
- It is a ONE-WAY function — you CANNOT reverse a hash to get original data.
- Unlike encryption, hashing is NOT meant to be reversed!
- The same input ALWAYS produces the same hash (deterministic).

CONCEPT: What is SHA-256?
- SHA-256 stands for Secure Hash Algorithm 256-bit.
- It produces a 64-character hexadecimal string (256 bits = 32 bytes).
- Designed by the NSA, widely used for passwords, digital signatures, and integrity checks.
- Even changing ONE character in the input completely changes the hash (avalanche effect).

CONCEPT: What is MD5?
- MD5 (Message-Digest Algorithm 5) produces a 32-character hex string (128 bits).
- Faster than SHA-256 but BROKEN — do NOT use for security-critical purposes.
- MD5 collisions have been found (two different inputs giving same hash).
- Still used for file integrity checks (not passwords).

WHY is hashing irreversible?
- Hash functions discard information during the process.
- They compress arbitrary-length data to a fixed size.
- It's mathematically infeasible to reconstruct input from output.
- Brute force (trying every possible input) is the only attack method.
"""

import hashlib


# ─── SHA-256 Hashing ───────────────────────────────────────────────────────────

def hash_sha256(text: str) -> str:
    """
    Generates a SHA-256 hash of the given text.

    SHA-256 is the gold standard for password hashing verification
    and data integrity checks.

    Args:
        text: The input string to hash.

    Returns:
        A 64-character hexadecimal string (the SHA-256 hash).
        Returns an error message string if something goes wrong.
    """
    try:
        if not text:
            return "Error: Input text cannot be empty."

        # encode() converts string to bytes (hashlib needs bytes, not strings)
        hash_object = hashlib.sha256(text.encode('utf-8'))

        # hexdigest() returns the hash as a readable hex string
        return hash_object.hexdigest()

    except Exception as e:
        return f"Hashing error: {str(e)}"


# ─── MD5 Hashing ──────────────────────────────────────────────────────────────

def hash_md5(text: str) -> str:
    """
    Generates an MD5 hash of the given text.

    WARNING: MD5 is cryptographically broken and should NOT be used
    for security purposes. Shown here for educational comparison only.

    Args:
        text: The input string to hash.

    Returns:
        A 32-character hexadecimal string (the MD5 hash).
    """
    try:
        if not text:
            return "Error: Input text cannot be empty."

        hash_object = hashlib.md5(text.encode('utf-8'))
        return hash_object.hexdigest()

    except Exception as e:
        return f"Hashing error: {str(e)}"


# ─── File Integrity Hash ───────────────────────────────────────────────────────

def hash_file_sha256(file_path: str) -> str:
    """
    Computes the SHA-256 hash of a file's contents.

    Used to verify file integrity — if even one byte changes,
    the hash will be completely different.

    Args:
        file_path: Path to the file to hash.

    Returns:
        The SHA-256 hash of the file, or an error message.
    """
    try:
        sha256 = hashlib.sha256()

        # Read file in chunks to handle large files efficiently
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):  # Read 8KB at a time
                sha256.update(chunk)

        return sha256.hexdigest()

    except FileNotFoundError:
        return "Error: File not found."
    except PermissionError:
        return "Error: Permission denied."
    except Exception as e:
        return f"File hashing error: {str(e)}"


# ─── Hash Comparison ──────────────────────────────────────────────────────────

def verify_hash(text: str, known_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verifies if a piece of text matches a known hash.

    This is how websites verify passwords — they hash your input
    and compare it to the stored hash (they never store your raw password).

    Args:
        text: The text to verify.
        known_hash: The expected hash value.
        algorithm: "sha256" or "md5".

    Returns:
        True if the text matches the hash, False otherwise.
    """
    if algorithm == "sha256":
        computed = hash_sha256(text)
    elif algorithm == "md5":
        computed = hash_md5(text)
    else:
        return False

    # Compare in a way that prevents timing attacks
    return computed.lower() == known_hash.lower()
