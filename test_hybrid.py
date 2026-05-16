import os
from hybrid_crypto import generate_rsa_keys, save_keys, hybrid_encrypt, hybrid_decrypt
from digital_signature import sign_file, verify_signature

def test_hybrid_and_signatures():
    print("--- Starting Hybrid Crypto & Signature Test ---")
    
    # 1. Generate Keys
    print("\n1. Generating RSA Keys...")
    priv, pub = generate_rsa_keys()
    priv_path, pub_path = save_keys(priv, pub)
    print(f"Keys saved: {priv_path}, {pub_path}")
    
    # 2. Create Test File
    test_file = "hybrid_test.txt"
    original_content = b"This is a secret message for hybrid encryption testing! " * 10
    with open(test_file, "wb") as f:
        f.write(original_content)
    print(f"\n2. Test file created: {test_file}")
    
    # 3. Encrypt
    print("\n3. Encrypting (Hybrid RSA+AES-GCM)...")
    success, enc_path = hybrid_encrypt(test_file, pub_path)
    if not success:
        print(f"Encryption failed: {enc_path}")
        return
    print(f"Encrypted file: {enc_path}")
    
    # 4. Decrypt
    print("\n4. Decrypting...")
    success, dec_path = hybrid_decrypt(enc_path, priv_path)
    if not success:
        print(f"Decryption failed: {dec_path}")
        return
    print(f"Decrypted file: {dec_path}")
    
    # 5. Verify Content
    with open(dec_path, "rb") as f:
        decrypted_content = f.read()
        
    if decrypted_content == original_content:
        print("SUCCESS: Decrypted content matches original!")
    else:
        print("FAILURE: Content mismatch!")

    # 6. Test Digital Signatures
    print("\n5. Testing Digital Signatures (RSA-PSS)...")
    print("Signing original file...")
    success, sig_path = sign_file(test_file, priv_path)
    if not success:
        print(f"Signing failed: {sig_path}")
    else:
        print(f"Signature file created: {sig_path}")
        
        print("Verifying signature...")
        success, msg = verify_signature(test_file, sig_path, pub_path)
        if success:
            print(msg)
        else:
            print(f"Verification failed: {msg}")

    # Cleanup
    print("\nCleaning up...")
    for f in [test_file, enc_path, dec_path, priv_path, pub_path, sig_path]:
        if os.path.exists(f):
            os.remove(f)
            print(f"Removed {f}")
            
    print("--- Test Complete ---")

if __name__ == "__main__":
    test_hybrid_and_signatures()
