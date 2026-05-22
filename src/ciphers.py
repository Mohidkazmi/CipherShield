"""
ciphers.py - Classical Cipher Demonstrations
=============================================
CipherShield | Information Security Project

CONCEPT: Classical Ciphers
- Classical ciphers are historical encryption techniques from before computers.
- They are NOT secure by modern standards but help understand the foundations of cryptography.
- Learning them helps understand WHY modern encryption (like AES) was developed.

CAESAR CIPHER:
- One of the oldest encryption methods, used by Julius Caesar ~58 BC.
- Shifts each letter by a fixed number (the "key").
- Example: "HELLO" with shift 3 → "KHOOR"
- Weakness: Only 25 possible keys — easily broken by brute force.

VIGENÈRE CIPHER:
- Invented in the 16th century, once called "Le Chiffre Indéchiffrable" (the unbreakable cipher).
- Uses a KEYWORD to shift each letter differently (polyalphabetic cipher).
- Example: "HELLO" with key "KEY" → each letter shifted by K(10), E(4), Y(24), K(10), E(4)
- Stronger than Caesar but still breakable using frequency analysis.
"""


# ─── Caesar Cipher ────────────────────────────────────────────────────────────

def caesar_encrypt(text: str, shift: int) -> str:
    """
    Encrypts text using the Caesar Cipher.

    Logic:
    - For each letter, shift it forward by 'shift' positions in the alphabet.
    - Wraps around using modulo 26 (Z + 1 → A).
    - Non-letter characters (spaces, numbers, symbols) remain unchanged.

    Args:
        text: The plaintext to encrypt.
        shift: Number of positions to shift (0–25).

    Returns:
        The encrypted ciphertext string.
    """
    result = []

    for char in text:
        if char.isalpha():
            # Determine base ASCII value: 'A' = 65 for uppercase, 'a' = 97 for lowercase
            base = ord('A') if char.isupper() else ord('a')

            # Shift the character and wrap around using modulo 26
            shifted = (ord(char) - base + shift) % 26 + base
            result.append(chr(shifted))
        else:
            # Keep non-alphabetic characters unchanged
            result.append(char)

    return ''.join(result)


def caesar_decrypt(text: str, shift: int) -> str:
    """
    Decrypts text that was encrypted with Caesar Cipher.

    Logic:
    - Decryption is the same as encryption but with a NEGATIVE shift.
    - Shifting back by 'shift' positions reverses the encryption.

    Args:
        text: The ciphertext to decrypt.
        shift: The same shift used during encryption.

    Returns:
        The decrypted plaintext string.
    """
    # Decrypting = encrypting with negative shift (shift backward)
    return caesar_encrypt(text, -shift)


def caesar_brute_force(ciphertext: str) -> list[str]:
    """
    Demonstrates why Caesar Cipher is weak — brute force all 25 possible keys.

    Since there are only 25 possible shifts, an attacker can try all of them
    and find the meaningful one. This is why single-key substitution ciphers
    are NOT secure.

    Args:
        ciphertext: The encrypted text to crack.

    Returns:
        A list of all 25 possible decryptions.
    """
    results = []
    for shift in range(1, 26):
        decrypted = caesar_decrypt(ciphertext, shift)
        results.append(f"Shift {shift:2d}: {decrypted}")
    return results


# ─── Vigenère Cipher ──────────────────────────────────────────────────────────

def vigenere_encrypt(text: str, key: str) -> str:
    """
    Encrypts text using the Vigenère Cipher.

    Logic:
    - The key is repeated to match the length of the text.
    - Each letter of the text is shifted by the corresponding key letter's position.
    - Key 'A' = shift 0, 'B' = shift 1, ..., 'Z' = shift 25.

    Example:
        Text: HELLO, Key: KEY
        H + K(10) = R
        E + E(4)  = I
        L + Y(24) = J
        L + K(10) = V
        O + E(4)  = S
        Result: RIJVS

    Args:
        text: The plaintext to encrypt.
        key: The keyword (letters only, case-insensitive).

    Returns:
        The encrypted ciphertext, or error message if key is invalid.
    """
    if not key or not key.isalpha():
        return "Error: Vigenère key must contain only letters."

    key = key.upper()       # Normalize key to uppercase
    result = []
    key_index = 0           # Tracks current position in the key

    for char in text:
        if char.isalpha():
            # Get shift value from current key character (A=0, B=1, ..., Z=25)
            shift = ord(key[key_index % len(key)]) - ord('A')

            base = ord('A') if char.isupper() else ord('a')
            encrypted_char = chr((ord(char) - base + shift) % 26 + base)
            result.append(encrypted_char)

            # Only advance key index for alphabetic characters
            key_index += 1
        else:
            result.append(char)

    return ''.join(result)


def vigenere_decrypt(text: str, key: str) -> str:
    """
    Decrypts text encrypted with Vigenère Cipher.

    Logic:
    - The same key is used, but shifts are applied in REVERSE.
    - Subtract the key shift instead of adding it.

    Args:
        text: The ciphertext to decrypt.
        key: The keyword used during encryption.

    Returns:
        The decrypted plaintext string.
    """
    if not key or not key.isalpha():
        return "Error: Vigenère key must contain only letters."

    key = key.upper()
    result = []
    key_index = 0

    for char in text:
        if char.isalpha():
            # Reverse the shift for decryption
            shift = ord(key[key_index % len(key)]) - ord('A')

            base = ord('A') if char.isupper() else ord('a')
            decrypted_char = chr((ord(char) - base - shift) % 26 + base)
            result.append(decrypted_char)

            key_index += 1
        else:
            result.append(char)

    return ''.join(result)
