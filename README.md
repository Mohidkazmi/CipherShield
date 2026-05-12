# CipherShield - Secure File Encryptor

**CipherShield** is a complete, beginner-friendly Information Security project built with Python and Tkinter. It demonstrates fundamental cryptography concepts through a practical, interactive GUI application.

## Features
- **File Encryption & Decryption:** Securely encrypt any file using AES-128 in CBC mode (via the `cryptography` Fernet module). Features PBKDF2HMAC password stretching and salting.
- **Hashing:** Generate SHA-256 and MD5 hashes from text. Understand the difference between two-way encryption and one-way hashing.
- **Classical Ciphers:** Explore historical encryption methods like the Caesar Cipher and Vigenère Cipher.
- **Password Strength Checker:** Analyzes password strength based on length, letters, numbers, and symbols.
- **Modern GUI:** A clean, dark-themed interface built using Python's native Tkinter.

## Setup Instructions

1. **Prerequisites**
   - Python 3.7 or higher installed.

2. **Clone / Download the Project**
   - Open a terminal and navigate to the project directory.

3. **Set Up Virtual Environment**
   - It is highly recommended to use a virtual environment:
     ```bash
     python -m venv venv
     ```
   - Activate the virtual environment:
     - On macOS/Linux: `source venv/bin/activate`
     - On Windows: `venv\Scripts\activate`

4. **Install Dependencies**
   - Install the required `cryptography` library inside the virtual environment:
     ```bash
     pip install -r requirements.txt
     ```

5. **Run the Application**
   - Execute the main file:
     ```bash
     python main.py
     ```

## Code Structure

- `main.py`: Entry point to launch the application.
- `gui.py`: Contains the Tkinter interface and connects UI events to backend functions.
- `encrypt.py`: Logic for AES file encryption and decryption, including key derivation.
- `hashing.py`: Implementation of SHA-256 and MD5 hashing algorithms.
- `ciphers.py`: Code for Caesar and Vigenère classical ciphers.
- `utils.py`: Helper functions for password strength checking, clipboard interaction, etc.

## Educational Concepts Covered
- **Symmetric Encryption (AES):** Why the same key is used for both encryption and decryption, and how a password is securely transformed into a cryptographic key.
- **Hashing vs Encryption:** Why hashing is irreversible while encryption is designed to be reversed.
- **Hash Collisions:** Why MD5 is considered broken compared to SHA-256.
- **Classical Ciphers:** The foundational basics of substitution ciphers and their vulnerabilities (like brute-forcing Caesar).
