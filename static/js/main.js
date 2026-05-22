/* ═══════════════════════════════════════════════════════════════
   main.js — Hybrid Shield Frontend Logic
   ═══════════════════════════════════════════════════════════════ */

// ─── Tab Navigation ─────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        item.classList.add('active');
        const tab = item.dataset.tab;
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        document.getElementById('tab-' + tab).classList.add('active');
        // Always refresh keys data on tab switch
        if (tab === 'keys') loadKeys();
        if (tab === 'mfa') checkMfaStatus();
        loadKeySelect();
    });
});


// ─── Status Helper ──────────────────────────────────────────
function showStatus(id, type, msg) {
    const el = document.getElementById(id);
    el.className = 'status-bar visible ' + type;
    el.innerHTML = (type === 'success' ? '✔' : type === 'error' ? '✖' : '▸') + '  ' + msg;
}

// ─── File Drop Zones ────────────────────────────────────────
document.querySelectorAll('.file-drop').forEach(zone => {
    const input = zone.querySelector('input[type="file"]');
    const nameEl = zone.querySelector('.file-name');

    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', e => {
        e.preventDefault(); zone.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            input.files = e.dataTransfer.files;
            nameEl.textContent = e.dataTransfer.files[0].name;
        }
    });
    input.addEventListener('change', () => {
        if (input.files.length) nameEl.textContent = input.files[0].name;
    });
});

// ─── Key Management ─────────────────────────────────────────
async function loadKeys() {
    const res = await fetch('/api/keys');
    const data = await res.json();
    const tbody = document.getElementById('key-table-body');
    if (!tbody) return;
    tbody.innerHTML = '';
    data.keys.forEach(k => {
        tbody.innerHTML += `<tr>
            <td class="key-id">${k.id}</td>
            <td class="key-label">${k.label}</td>
            <td>${k.algorithm}</td>
            <td>${k.bits}</td>
            <td>${k.created_at}</td>
            <td>
                <button class="btn btn-secondary" style="padding:4px 10px;font-size:11px" onclick="downloadKey(${k.id},'public')">Pub</button>
                <button class="btn btn-secondary" style="padding:4px 10px;font-size:11px" onclick="downloadKey(${k.id},'private')">Priv</button>
                <button class="btn btn-danger" style="padding:4px 10px;font-size:11px" onclick="deleteKey(${k.id})">✕</button>
            </td>
        </tr>`;
    });
}

async function generateKey() {
    const label = document.getElementById('key-label').value.trim();
    if (!label) return alert('Please enter a label for the key.');
    const fd = new FormData();
    fd.append('label', label);
    const res = await fetch('/api/generate-keys', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.success) {
        showStatus('key-status', 'success', data.message);
        document.getElementById('key-label').value = '';
        loadKeys();
        loadKeySelect();
    } else {
        showStatus('key-status', 'error', data.message);
    }
}

function downloadKey(id, type) {
    window.open(`/api/download-key/${id}/${type}`, '_blank');
}

async function deleteKey(id) {
    if (!confirm('Remove this key from the registry?')) return;
    const fd = new FormData();
    fd.append('key_id', id);
    await fetch('/api/delete-key', { method: 'POST', body: fd });
    loadKeys();
    loadKeySelect();
}

// ─── Populate key selectors ─────────────────────────────────
async function loadKeySelect() {
    console.log('[loadKeySelect] Starting...');
    try {
        const res = await fetch('/api/keys');
        const data = await res.json();
        console.log('[loadKeySelect] API returned', data.keys ? data.keys.length : 0, 'keys');
        const selects = document.querySelectorAll('.key-select');
        console.log('[loadKeySelect] Found', selects.length, 'select elements');
        selects.forEach((sel, idx) => {
            const currentVal = sel.value;
            // Build new HTML
            let html = '<option value="">— Select Key —</option>';
            if (data.keys && data.keys.length > 0) {
                for (let i = 0; i < data.keys.length; i++) {
                    const k = data.keys[i];
                    html += '<option value="' + k.id + '">' + k.label + ' (' + k.algorithm + '-' + k.bits + ')</option>';
                }
            }
            sel.innerHTML = html;
            console.log('[loadKeySelect] Select #' + idx + ' now has', sel.options.length, 'options');
            // Restore previous selection if still valid
            if (currentVal) sel.value = currentVal;
        });
    } catch (e) {
        console.error('[loadKeySelect] ERROR:', e);
    }
}

// ─── Hybrid Encrypt/Decrypt ─────────────────────────────────
async function hybridEncrypt() {
    const file = document.getElementById('hyb-file').files[0];
    const keyId = document.getElementById('hyb-key').value;
    if (!file) return showStatus('hyb-status', 'error', 'Select a file first.');
    if (!keyId) return showStatus('hyb-status', 'error', 'Select a key first.');

    showStatus('hyb-status', 'info', 'Encrypting with RSA + AES-256-GCM...');
    const fd = new FormData();
    fd.append('file', file);
    fd.append('key_id', keyId);
    try {
        const res = await fetch('/api/hybrid-encrypt', { method: 'POST', body: fd });
        if (res.ok) {
            const blob = await res.blob();
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = file.name + '.hyb';
            a.click();
            showStatus('hyb-status', 'success', 'Encrypted! File downloaded as ' + file.name + '.hyb');
        } else {
            const err = await res.json();
            showStatus('hyb-status', 'error', err.message);
        }
    } catch (e) { showStatus('hyb-status', 'error', e.message); }
}

async function hybridDecrypt() {
    const file = document.getElementById('hyb-file').files[0];
    const keyId = document.getElementById('hyb-key').value;
    if (!file) return showStatus('hyb-status', 'error', 'Select a .hyb file first.');
    if (!keyId) return showStatus('hyb-status', 'error', 'Select a key first.');

    showStatus('hyb-status', 'info', 'Decrypting with Private Key...');
    const fd = new FormData();
    fd.append('file', file);
    fd.append('key_id', keyId);
    try {
        const res = await fetch('/api/hybrid-decrypt', { method: 'POST', body: fd });
        if (res.ok) {
            const blob = await res.blob();
            const name = file.name.replace('.hyb', '');
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = name;
            a.click();
            showStatus('hyb-status', 'success', 'Decrypted! File downloaded as ' + name);
        } else {
            const err = await res.json();
            showStatus('hyb-status', 'error', err.message);
        }
    } catch (e) { showStatus('hyb-status', 'error', e.message); }
}

// ─── Digital Signatures ─────────────────────────────────────
async function signFile() {
    const file = document.getElementById('sig-file').files[0];
    const keyId = document.getElementById('sig-key').value;
    if (!file) return showStatus('sig-status', 'error', 'Select a file to sign.');
    if (!keyId) return showStatus('sig-status', 'error', 'Select a key for signing.');

    showStatus('sig-status', 'info', 'Generating RSA-PSS Signature...');
    const fd = new FormData();
    fd.append('file', file);
    fd.append('key_id', keyId);
    try {
        const res = await fetch('/api/sign-file', { method: 'POST', body: fd });
        if (res.ok) {
            const blob = await res.blob();
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = file.name + '.sig';
            a.click();
            showStatus('sig-status', 'success', 'Signed! Signature file downloaded.');
        } else {
            const err = await res.json();
            showStatus('sig-status', 'error', err.message);
        }
    } catch (e) { showStatus('sig-status', 'error', e.message); }
}

async function verifySignature() {
    const file = document.getElementById('verify-file').files[0];
    const sig = document.getElementById('verify-sig').files[0];
    const keyId = document.getElementById('sig-key').value;
    if (!file || !sig) return showStatus('sig-status', 'error', 'Select both the file and its .sig signature.');
    if (!keyId) return showStatus('sig-status', 'error', 'Select the signer\'s key.');

    showStatus('sig-status', 'info', 'Verifying Signature...');
    const fd = new FormData();
    fd.append('file', file);
    fd.append('signature', sig);
    fd.append('key_id', keyId);
    try {
        const res = await fetch('/api/verify-signature', { method: 'POST', body: fd });
        const data = await res.json();
        showStatus('sig-status', data.success ? 'success' : 'error', data.message);
    } catch (e) { showStatus('sig-status', 'error', e.message); }
}

// ─── Hashing ────────────────────────────────────────────────
async function hashText() {
    const text = document.getElementById('hash-input').value.trim();
    const algo = document.getElementById('hash-algo').value;
    if (!text) return showStatus('hash-status', 'error', 'Enter some text to hash.');
    const fd = new FormData();
    fd.append('text', text);
    fd.append('algorithm', algo);
    const res = await fetch('/api/hash-text', { method: 'POST', body: fd });
    const data = await res.json();
    document.getElementById('hash-output').textContent = data.hash;
    showStatus('hash-status', 'success', data.algorithm + ' hash computed.');
}

async function hashFile() {
    const file = document.getElementById('hash-file').files[0];
    if (!file) return showStatus('hash-status', 'error', 'Select a file to hash.');
    showStatus('hash-status', 'info', 'Computing SHA-256 file hash...');
    const fd = new FormData();
    fd.append('file', file);
    const res = await fetch('/api/hash-file', { method: 'POST', body: fd });
    const data = await res.json();
    document.getElementById('hash-output').textContent = data.hash;
    showStatus('hash-status', 'success', 'SHA-256 hash of "' + data.filename + '" computed.');
}

function copyHash() {
    const h = document.getElementById('hash-output').textContent;
    if (h) { navigator.clipboard.writeText(h); showStatus('hash-status', 'success', 'Copied to clipboard!'); }
}

// ─── AES Symmetric ──────────────────────────────────────────
async function aesEncrypt() {
    const file = document.getElementById('aes-file').files[0];
    const pwd = document.getElementById('aes-password').value;
    if (!file) return showStatus('aes-status', 'error', 'Select a file.');
    if (!pwd) return showStatus('aes-status', 'error', 'Enter a password.');
    showStatus('aes-status', 'info', 'Encrypting with AES-256...');
    const fd = new FormData();
    fd.append('file', file);
    fd.append('password', pwd);
    try {
        const res = await fetch('/api/aes-encrypt', { method: 'POST', body: fd });
        if (res.ok) {
            const blob = await res.blob();
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = file.name + '.enc';
            a.click();
            showStatus('aes-status', 'success', 'Encrypted! File downloaded.');
        } else {
            const err = await res.json();
            showStatus('aes-status', 'error', err.message);
        }
    } catch (e) { showStatus('aes-status', 'error', e.message); }
}

async function aesDecrypt() {
    const file = document.getElementById('aes-file').files[0];
    const pwd = document.getElementById('aes-password').value;
    if (!file) return showStatus('aes-status', 'error', 'Select a .enc file.');
    if (!pwd) return showStatus('aes-status', 'error', 'Enter the password.');
    showStatus('aes-status', 'info', 'Decrypting with AES-256...');
    const fd = new FormData();
    fd.append('file', file);
    fd.append('password', pwd);
    try {
        const res = await fetch('/api/aes-decrypt', { method: 'POST', body: fd });
        if (res.ok) {
            const blob = await res.blob();
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = file.name.replace('.enc', '');
            a.click();
            showStatus('aes-status', 'success', 'Decrypted! File downloaded.');
        } else {
            const err = await res.json();
            showStatus('aes-status', 'error', err.message);
        }
    } catch (e) { showStatus('aes-status', 'error', e.message); }
}

// ─── Init ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadKeys();
    loadKeySelect();
    
    // Register drag & drop file name listener specifically for dynamic fields
    const mfaInput = document.getElementById('mfa-file');
    if (mfaInput) {
        mfaInput.addEventListener('change', () => {
            const nameEl = document.getElementById('mfa-file-name');
            if (mfaInput.files.length && nameEl) {
                nameEl.textContent = mfaInput.files[0].name;
            }
        });
    }
});

// ─── Password Strength Evaluator ────────────────────────────
function evaluatePasswordStrength() {
    const password = document.getElementById('aes-password').value;
    const badge = document.getElementById('strength-badge');
    const tipsContainer = document.getElementById('strength-tips');
    
    const chkLen8 = document.getElementById('chk-len-8');
    const chkLen12 = document.getElementById('chk-len-12');
    const chkCases = document.getElementById('chk-cases');
    const chkDigits = document.getElementById('chk-digits');
    const chkSymbols = document.getElementById('chk-symbols');
    
    if (!password) {
        badge.textContent = 'No Password';
        badge.style.color = '#888888';
        badge.style.background = 'rgba(255,255,255,0.05)';
        
        for (let i = 1; i <= 5; i++) {
            document.getElementById('strength-segment-' + i).style.background = '#222';
        }
        
        [chkLen8, chkLen12, chkCases, chkDigits, chkSymbols].forEach(el => {
            el.innerHTML = '❌ ' + el.innerHTML.slice(2);
            el.style.color = 'var(--fg2)';
        });
        
        tipsContainer.innerHTML = '<li>• Enter a password to check its strength.</li>';
        return;
    }
    
    const checks = {
        length_8:     password.length >= 8,
        length_12:    password.length >= 12,
        uppercase:    /[A-Z]/.test(password),
        lowercase:    /[a-z]/.test(password),
        digits:       /\d/.test(password),
        symbols:      /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)
    };
    
    const cases = checks.uppercase && checks.lowercase;
    
    let score = 0;
    if (checks.length_8) score++;
    if (checks.length_12) score++;
    if (cases) score++;
    if (checks.digits) score++;
    if (checks.symbols) score++;
    
    const updateCheckItem = (el, isValid, text) => {
        if (isValid) {
            el.innerHTML = '✓ ' + text;
            el.style.color = 'var(--success)';
        } else {
            el.innerHTML = '❌ ' + text;
            el.style.color = 'var(--fg2)';
        }
    };
    
    updateCheckItem(chkLen8, checks.length_8, 'At least 8 characters');
    updateCheckItem(chkLen12, checks.length_12, 'At least 12 characters');
    updateCheckItem(chkCases, cases, 'Upper & Lowercase');
    updateCheckItem(chkDigits, checks.digits, 'At least 1 number');
    updateCheckItem(chkSymbols, checks.symbols, 'At least 1 symbol');
    
    const strengthMap = {
        0: { text: 'Very Weak',   color: '#FF3B3B' },
        1: { text: 'Weak',        color: '#FF6B35' },
        2: { text: 'Fair',        color: '#FFB300' },
        3: { text: 'Medium',      color: '#7BC67E' },
        4: { text: 'Strong',      color: '#4CAF50' },
        5: { text: 'Very Strong', color: '#00C853' }
    };
    
    const rating = strengthMap[score] || strengthMap[0];
    badge.textContent = rating.text;
    badge.style.color = rating.color;
    badge.style.background = rating.color + '22';
    
    for (let i = 1; i <= 5; i++) {
        const seg = document.getElementById('strength-segment-' + i);
        if (i <= score) {
            seg.style.background = rating.color;
        } else {
            seg.style.background = '#222';
        }
    }
    
    let tipsHtml = '';
    if (!checks.length_8) tipsHtml += '<li>• Use at least 8 characters.</li>';
    if (!checks.length_12) tipsHtml += '<li>• Use 12+ characters for a stronger password.</li>';
    if (!checks.uppercase) tipsHtml += '<li>• Add uppercase letters (A-Z).</li>';
    if (!checks.lowercase) tipsHtml += '<li>• Add lowercase letters (a-z).</li>';
    if (!checks.digits) tipsHtml += '<li>• Include numbers (0-9).</li>';
    if (!checks.symbols) tipsHtml += '<li>• Add symbols like !@#$%^&*.</li>';
    
    if (tipsHtml === '') {
        tipsHtml = '<li style="color:var(--success)">✓ Excellent password! All criteria met.</li>';
    }
    tipsContainer.innerHTML = tipsHtml;
}

// ─── MFA Vault functions ────────────────────────────────────
async function checkMfaStatus() {
    try {
        const res = await fetch('/api/mfa/status');
        const data = await res.json();
        const unconfigured = document.getElementById('mfa-unconfigured-view');
        const configured = document.getElementById('mfa-configured-view');
        if (data.configured) {
            unconfigured.style.display = 'none';
            configured.style.display = 'block';
        } else {
            unconfigured.style.display = 'block';
            configured.style.display = 'none';
            document.getElementById('mfa-qr-container').style.display = 'none';
        }
    } catch (e) {
        showStatus('mfa-status', 'error', 'Failed to check vault status: ' + e.message);
    }
}

async function generateMFA() {
    const username = document.getElementById('mfa-username').value.trim();
    if (!username) return alert('Please enter a username or label for the vault.');
    
    showStatus('mfa-status', 'info', 'Generating MFA Seed & QR Code...');
    const fd = new FormData();
    fd.append('username', username);
    
    try {
        const res = await fetch('/api/mfa/generate', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.success) {
            document.getElementById('mfa-qr-image').src = 'data:image/png;base64,' + data.qr_code;
            document.getElementById('mfa-seed-text').textContent = data.seed;
            document.getElementById('mfa-qr-container').style.display = 'block';
            showStatus('mfa-status', 'success', 'MFA provisioning details generated successfully!');
        } else {
            showStatus('mfa-status', 'error', data.message);
        }
    } catch (e) {
        showStatus('mfa-status', 'error', 'Error generating MFA: ' + e.message);
    }
}

async function setupVault() {
    const seed = document.getElementById('mfa-seed-text').textContent;
    const code = document.getElementById('mfa-setup-code').value.trim();
    if (!seed) return alert('Generate a seed first.');
    if (!code || code.length !== 6 || isNaN(code)) return alert('Please enter a valid 6-digit OTP code.');
    
    showStatus('mfa-status', 'info', 'Verifying security seed and locking vault...');
    const fd = new FormData();
    fd.append('seed', seed);
    fd.append('code', code);
    
    try {
        const res = await fetch('/api/mfa/setup', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.success) {
            alert(data.message);
            document.getElementById('mfa-setup-code').value = '';
            checkMfaStatus();
            showStatus('mfa-status', 'success', 'Vault initialized and sealed with MFA!');
        } else {
            showStatus('mfa-status', 'error', data.message);
        }
    } catch (e) {
        showStatus('mfa-status', 'error', 'Error during vault configuration: ' + e.message);
    }
}

async function resetMFA() {
    if (!confirm('Warning: Resetting your vault security will overwrite your master key and require setting up a new Google Authenticator seed. Are you sure you want to proceed?')) return;
    
    showStatus('mfa-status', 'info', 'Resetting vault file on the server...');
    try {
        const res = await fetch('/api/mfa/reset', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            document.getElementById('mfa-unconfigured-view').style.display = 'block';
            document.getElementById('mfa-configured-view').style.display = 'none';
            document.getElementById('mfa-qr-container').style.display = 'none';
            document.getElementById('mfa-setup-code').value = '';
            document.getElementById('mfa-seed-text').textContent = '';
            showStatus('mfa-status', 'success', 'Vault security has been reset on the server! You can now configure a new MFA key.');
        } else {
            showStatus('mfa-status', 'error', 'Reset failed: ' + data.message);
        }
    } catch (e) {
        showStatus('mfa-status', 'error', 'Reset error: ' + e.message);
    }
}

async function mfaEncrypt() {
    const file = document.getElementById('mfa-file').files[0];
    const code = document.getElementById('mfa-op-code').value.trim();
    if (!file) return showStatus('mfa-status', 'error', 'Select a file first.');
    if (!code || code.length !== 6 || isNaN(code)) return showStatus('mfa-status', 'error', 'Enter your current 6-digit OTP.');
    
    showStatus('mfa-status', 'info', 'Authorizing and encrypting file...');
    const fd = new FormData();
    fd.append('file', file);
    fd.append('code', code);
    
    try {
        const res = await fetch('/api/mfa/encrypt', { method: 'POST', body: fd });
        if (res.ok) {
            const blob = await res.blob();
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = file.name + '.enc';
            a.click();
            document.getElementById('mfa-op-code').value = '';
            showStatus('mfa-status', 'success', 'Encrypted! File secured inside dynamic MFA vault and downloaded.');
        } else {
            const err = await res.json();
            showStatus('mfa-status', 'error', err.message);
        }
    } catch (e) {
        showStatus('mfa-status', 'error', 'Encryption failed: ' + e.message);
    }
}

async function mfaDecrypt() {
    const file = document.getElementById('mfa-file').files[0];
    const code = document.getElementById('mfa-op-code').value.trim();
    if (!file) return showStatus('mfa-status', 'error', 'Select a .enc file first.');
    if (!code || code.length !== 6 || isNaN(code)) return showStatus('mfa-status', 'error', 'Enter your current 6-digit OTP.');
    
    showStatus('mfa-status', 'info', 'Authorizing and decrypting file...');
    const fd = new FormData();
    fd.append('file', file);
    fd.append('code', code);
    
    try {
        const res = await fetch('/api/mfa/decrypt', { method: 'POST', body: fd });
        if (res.ok) {
            const blob = await res.blob();
            const name = file.name.replace('.enc', '');
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = name;
            a.click();
            document.getElementById('mfa-op-code').value = '';
            showStatus('mfa-status', 'success', 'Decrypted! File recovered from vault and downloaded as ' + name);
        } else {
            const err = await res.json();
            showStatus('mfa-status', 'error', err.message);
        }
    } catch (e) {
        showStatus('mfa-status', 'error', 'Decryption failed: ' + e.message);
    }
}

// ─── Classical Ciphers functions ────────────────────────────
async function caesarEncrypt() {
    const text = document.getElementById('caesar-text').value.trim();
    const shift = parseInt(document.getElementById('caesar-shift').value);
    if (!text) return showStatus('classical-status', 'error', 'Enter Caesar text first.');
    if (isNaN(shift)) return showStatus('classical-status', 'error', 'Enter a valid shift integer.');
    
    showStatus('classical-status', 'info', 'Applying Caesar shift cipher...');
    const fd = new FormData();
    fd.append('text', text);
    fd.append('shift', shift);
    
    try {
        const res = await fetch('/api/classical/caesar/encrypt', { method: 'POST', body: fd });
        const data = await res.json();
        document.getElementById('brute-force-box').style.display = 'none';
        document.getElementById('classical-output').textContent = data.result;
        showStatus('classical-status', 'success', 'Caesar Encryption completed.');
    } catch (e) {
        showStatus('classical-status', 'error', e.message);
    }
}

async function caesarDecrypt() {
    const text = document.getElementById('caesar-text').value.trim();
    const shift = parseInt(document.getElementById('caesar-shift').value);
    if (!text) return showStatus('classical-status', 'error', 'Enter Caesar text first.');
    if (isNaN(shift)) return showStatus('classical-status', 'error', 'Enter a valid shift integer.');
    
    showStatus('classical-status', 'info', 'Reversing Caesar shift...');
    const fd = new FormData();
    fd.append('text', text);
    fd.append('shift', shift);
    
    try {
        const res = await fetch('/api/classical/caesar/decrypt', { method: 'POST', body: fd });
        const data = await res.json();
        document.getElementById('brute-force-box').style.display = 'none';
        document.getElementById('classical-output').textContent = data.result;
        showStatus('classical-status', 'success', 'Caesar Decryption completed.');
    } catch (e) {
        showStatus('classical-status', 'error', e.message);
    }
}

async function caesarBruteForce() {
    const text = document.getElementById('caesar-text').value.trim();
    if (!text) return showStatus('classical-status', 'error', 'Enter Caesar ciphertext to crack.');
    
    showStatus('classical-status', 'info', 'Executing visual brute-force cracking sequence...');
    const fd = new FormData();
    fd.append('text', text);
    
    try {
        const res = await fetch('/api/classical/caesar/brute-force', { method: 'POST', body: fd });
        const data = await res.json();
        
        document.getElementById('classical-output').textContent = "Brute force cracking finished. Analyze possibilities below.";
        const resultsBox = document.getElementById('brute-force-results');
        resultsBox.innerHTML = '';
        
        data.results.forEach(line => {
            resultsBox.innerHTML += `<div style="padding: 4px; border-bottom: 1px solid rgba(255,255,255,0.03);">${line}</div>`;
        });
        document.getElementById('brute-force-box').style.display = 'block';
        showStatus('classical-status', 'success', 'Caesar brute force completed. 25 combinations checked.');
    } catch (e) {
        showStatus('classical-status', 'error', e.message);
    }
}

async function vigenereEncrypt() {
    const text = document.getElementById('vigenere-text').value.trim();
    const key = document.getElementById('vigenere-key').value.trim();
    if (!text) return showStatus('classical-status', 'error', 'Enter Vigenère text first.');
    if (!key) return showStatus('classical-status', 'error', 'Enter alphabetic keyword.');
    
    showStatus('classical-status', 'info', 'Applying Vigenère polyalphabetic cipher...');
    const fd = new FormData();
    fd.append('text', text);
    fd.append('key', key);
    
    try {
        const res = await fetch('/api/classical/vigenere/encrypt', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.success) {
            document.getElementById('brute-force-box').style.display = 'none';
            document.getElementById('classical-output').textContent = data.result;
            showStatus('classical-status', 'success', 'Vigenère Encryption completed.');
        } else {
            showStatus('classical-status', 'error', data.message);
        }
    } catch (e) {
        showStatus('classical-status', 'error', e.message);
    }
}

async function vigenereDecrypt() {
    const text = document.getElementById('vigenere-text').value.trim();
    const key = document.getElementById('vigenere-key').value.trim();
    if (!text) return showStatus('classical-status', 'error', 'Enter Vigenère text first.');
    if (!key) return showStatus('classical-status', 'error', 'Enter keyword.');
    
    showStatus('classical-status', 'info', 'Reversing Vigenère cipher...');
    const fd = new FormData();
    fd.append('text', text);
    fd.append('key', key);
    
    try {
        const res = await fetch('/api/classical/vigenere/decrypt', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.success) {
            document.getElementById('brute-force-box').style.display = 'none';
            document.getElementById('classical-output').textContent = data.result;
            showStatus('classical-status', 'success', 'Vigenère Decryption completed.');
        } else {
            showStatus('classical-status', 'error', data.message);
        }
    } catch (e) {
        showStatus('classical-status', 'error', e.message);
    }
}

function copyClassicalOutput() {
    const output = document.getElementById('classical-output').textContent;
    if (output && output !== "Output results will appear here...") {
        navigator.clipboard.writeText(output);
        showStatus('classical-status', 'success', 'Copied output to clipboard!');
    } else {
        showStatus('classical-status', 'error', 'Nothing to copy.');
    }
}
