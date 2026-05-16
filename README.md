# Hybrid Shield - Secure File Encryption System

**A Comprehensive Information Security Final Project**

**Hybrid Shield** is a professional-grade cryptographic suite that implements a **Secure File Encryption System using Hybrid Cryptography**. It combines the high speed of Symmetric encryption (AES) with the secure key-distribution capabilities of Asymmetric encryption (RSA). 

This project was built from the ground up to demonstrate a deep, practical understanding of modern cryptographic standards, data integrity, and non-repudiation.

---

## 🌟 Core Cryptographic Features (The "Hybrid" Engine)

The system solves the fundamental **Key Distribution Problem** using a hybrid approach (similar to how HTTPS/TLS and PGP operate).

1. **AES-256 GCM (Symmetric Encryption)**
   - Used to encrypt the actual file data.
   - **Why GCM?** Galois/Counter Mode is an *Authenticated Encryption* mode. It provides both **Confidentiality** (encryption) and **Integrity** (an authentication tag). If a single bit of the encrypted file is altered by an attacker, the decryption will immediately fail, preventing tampering attacks.

2. **RSA-2048 (Asymmetric Encryption)**
   - Used exclusively to encrypt the 256-bit AES session key.
   - Utilizes **OAEP Padding** with SHA-256 (Optimal Asymmetric Encryption Padding) to prevent chosen-ciphertext attacks.

3. **Digital Signatures (Non-Repudiation)**
   - Implements **RSA-PSS** (Probabilistic Signature Scheme) with SHA-256.
   - A user can sign a file with their Private Key. Any recipient can verify the signature using the sender's Public Key, proving exactly who sent the file and that it hasn't been modified.

---

## 🛠️ Complete Feature Set

- **Hybrid File Vault:** 3-step wizard to encrypt files into secure `.hyb` bundles containing both the RSA-encrypted session key and the AES-encrypted data.
- **Key Registry Manager:** A local Key Management System (KMS) to generate, store metadata, and manage multiple RSA key pairs.
- **Data Integrity Prover:** A testing tool that encrypts a file, decrypts it, and compares the SHA-256 hashes before and after to prove mathematical zero-data-loss.
- **Legacy Symmetric Vault:** Password-based encryption using PBKDF2HMAC (Key Derivation) with 390,000 iterations to stretch weak passwords into strong keys.
- **MFA Integration:** A Time-Based One-Time Password (TOTP) vault integration compatible with Google Authenticator.
- **Classical Ciphers Lab:** Educational demonstrations of historical substitution ciphers (Caesar and Vigenère).

---

## 🚀 Setup Instructions

1. **Prerequisites**
   - Python 3.8 or higher installed on your system.

2. **Clone / Download the Project**
   - Open a terminal and navigate to the project folder.

3. **Set Up a Virtual Environment (Recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   venv\Scripts\activate     # On Windows
   ```

4. **Install Dependencies**
   - Install the required cryptographic libraries:
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Dashboard**
   ```bash
   python main.py
   ```

---

## 📂 Architecture & Code Structure

- `main.py` — Application entry point.
- `gui.py` — A 7-tab, dark-themed, responsive dashboard built in native Tkinter.
- `hybrid_crypto.py` — **[CORE]** The RSA + AES-GCM hybrid encryption engine.
- `digital_signature.py` — **[CORE]** RSA-PSS signature generation and verification.
- `key_manager.py` — Key registry database logic.
- `encrypt.py` — Legacy PBKDF2 + AES-CBC (Fernet) logic.
- `mfa_vault.py` — TOTP generation and verification.
- `hashing.py` — Implementations for SHA-256 and MD5.

---

## 🎓 Academic Concepts Mastered

By reviewing this codebase, the following Information Security concepts are demonstrated:
- **The Key Distribution Problem:** Solved via Hybrid Cryptography.
- **Confidentiality:** Provided by AES-256.
- **Integrity:** Provided by AES-GCM authentication tags and SHA-256 hashing.
- **Authenticity & Non-Repudiation:** Provided by RSA-PSS Digital Signatures.
- **Key Derivation Functions (KDF):** Provided by PBKDF2HMAC with random salts.
- **Cryptographic Padding:** OAEP for encryption, PSS for signatures.
