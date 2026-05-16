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
});
