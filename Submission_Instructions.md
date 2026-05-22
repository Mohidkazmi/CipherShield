# HYBRID SHIELD — FLawless Submission & Live Demo Guide

To secure **full marks** for your final submission, this guide provides a step-by-step roadmap to present your source code, capture perfect screenshots, and execute a flawless live demonstration during evaluation.

---

## 📂 YOUR SUBMISSION BUNDLE

Your project directory now contains all necessary academic and presentation assets:

1. **Research Paper**: 
   * [Research_Report.md](file:///Users/mohidkazmi/Documents/IS_PROJECT/Research_Report.md) (Standard Markdown formatting)
   * [Research_Report.docx](file:///Users/mohidkazmi/Documents/IS_PROJECT/Research_Report.docx) (Microsoft Word compiled with custom typography, padded tables, and callouts)
2. **Source Code**: Clean, modular Python implementation of AES-256 GCM, RSA-2048, RSA-PSS, PBKDF2, and FastAPI templates.
3. **Presentation Slides**: 
   * [Presentation_Slides.pptx](file:///Users/mohidkazmi/Documents/IS_PROJECT/Presentation_Slides.pptx) (Microsoft PowerPoint slides in widescreen 16:9 format with custom Navy corporate color blocks, bullet cards, visual structure grids, and comparative benchmarks)
4. **Submission Guide**: This [Submission_Instructions.md](file:///Users/mohidkazmi/Documents/IS_PROJECT/Submission_Instructions.md) file.

---

## 🚀 PART 1: LIVE DEMONSTRATION WORKFLOW

Follow this exact workflow to deliver a seamless, zero-fail live demonstration.

### Step 1: Start the Web Dashboard
1. Open a terminal and navigate to the project directory:
   ```bash
   cd /Users/mohidkazmi/Documents/IS_PROJECT
   ```
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Launch the entry point script:
   ```bash
   python main.py
   ```
4. **What Happens:** The FastAPI Uvicorn server will boot on port 8000 and automatically open your default web browser to the dashboard: `http://127.0.0.1:8000`.

---

### Step 2: Demonstrating the "Hybrid Engine" (Confidentiality)
1. **Navigate to "Key Registry" Tab**:
   * Type `"Demo Vault Key"` in the Label input and click **[Generate RSA Key Pair]**.
   * Show that the key successfully populates the active key registry with the key ID, bit-rate (2048 bits), and creation timestamp.
2. **Navigate to "Hybrid Vault" Tab**:
   * Click **Choose File** and select any test document (e.g., a PDF, image, or text file).
   * Choose the generated key pair from the key dropdown menu.
   * Click **[Run Hybrid Encryption]**.
   * **What to highlight:** Uvicorn processes the request in milliseconds. The browser downloads the encrypted `.hyb` file.
   * **Explain the visual layout:** Point out that this `.hyb` bundle encapsulates the 256-bit AES key (encrypted via RSA-2048 OAEP) alongside the 12-byte GCM nonce and the encrypted ciphertext payload.
3. **Run Decryption**:
   * Upload the downloaded `.hyb` file.
   * Choose the corresponding private key from the dropdown and click **[Run Hybrid Decryption]**.
   * **What to highlight:** The original file is downloaded back successfully with zero corruption.

---

### Step 3: Demonstrating Digital Signatures (Non-Repudiation)
1. **Navigate to "Digital Signatures" Tab**:
   * Upload a plaintext test file.
   * Select your generated key pair and click **[Sign File]**.
   * **What Happens:** Uvicorn downloads a companion signature file named `[original_filename].sig` containing the RSA-PSS bytes.
2. **Verify Integrity & Tampering (Show stopper detail!):**
   * Upload the original plaintext file, the `.sig` companion, and select your public key. Click **[Verify Signature]**.
   * **Result:** UI shows `✔ SIGNATURE VALID — File is authentic and unmodified.`
   * **Simulate an attack:** Open the original plaintext file, append a single period or character, save it, and re-upload it for verification.
   * **Result:** The system will instantly flag `✖ SIGNATURE INVALID — File may have been modified!` proving the RSA-PSS non-repudiation and integrity guarantee works.

---

### Step 4: Demonstrating the MFA Vault Integration
1. **Navigate to "MFA Vault" Tab**:
   * Trigger the setup seed. The screen will render a QR code.
   * Open **Google Authenticator** (or any authenticator app) on your phone, click the `+` icon, and scan the QR code.
   * Enter the dynamic 6-digit verification code from your phone and click **[Unlock Vault]**.
   * **What to highlight:** Dynamic Time-Based (TOTP) token gating protects the underlying Master Key, simulating hardware-level key isolation.

---

### Step 5: Demonstrating Password stretching (KDF)
1. **Navigate to "Symmetric Encryption" Tab**:
   * Enter a weak password like `12345`.
   * Point out the **Password Strength indicator** (powered by `utils.py`) dynamically changing to **Very Weak (Red)** and suggesting improvements.
   * Type in a strong pass `P@ssw0rd_12345!` to show the indicator shift to **Very Strong (Green)**.
   * Perform symmetric lock and show the Salt prepended inside the final `.enc` output.

---

## 📸 PART 2: SCREENSHOT GUIDE

To secure full marks on presentation materials, compile 5 clean screenshots of the running dashboard:

1. **Screenshot 1 (Key Registry Manager)**:
   * Show a generated key pair actively registered in the grid with active download options. 
   * *Highlight:* Clean dark-themed CSS and professional layout.
2. **Screenshot 2 (Hybrid File Vault - Success state)**:
   * Capture the screen immediately after clicking **[Run Hybrid Encryption]** showing the browser download bar and success notification pop-ups.
3. **Screenshot 3 (Signature Failure Audit)**:
   * Capture the signature verification screen showing the red warning alert triggered when trying to verify a tampered test document.
4. **Screenshot 4 (MFA Vault Scan)**:
   * Capture the QR code setup overlay next to the TOTP code entry form.
5. **Screenshot 5 (Password Strength Metrics)**:
   * Capture the password strength checking widget showing the dynamic bullet-point list of password tips and the green/red color changes.

---

## 🏆 DESIGN TRICKS TO IMPRESS EVALUATORS

* **Draw a Parallel with HTTPS**: Explain that your hybrid logic operates exactly like modern HTTPS/TLS: asymmetric handshakes establish dynamic, symmetric session locks.
* **Explain AEAD (Galois GCM)**: Evaluators love academic depth. Mention that your GCM implementation avoids the legacy Padding Oracle attacks of older CBC modes by rejecting tampered ciphertexts prior to processing.
* **Point Out PBKDF2 Iterations**: Highlight that stretching human passwords with 50,000 hashing rounds protects against high-speed GPU hash cracking.
