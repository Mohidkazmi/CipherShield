import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import math
import mfa_vault

from encrypt import encrypt_file, decrypt_file, generate_key_file, encrypt_file_with_key, decrypt_file_with_key
from hashing import hash_sha256, hash_md5, hash_file_sha256
from ciphers import caesar_encrypt, caesar_decrypt, vigenere_encrypt, vigenere_decrypt
from utils import check_password_strength, copy_to_clipboard, shorten_path, get_file_size_str
import digital_signature
import key_manager
import hybrid_crypto

# ══════════════════════════════════════════════════════════════════════════════
#  DESIGN TOKENS
# ══════════════════════════════════════════════════════════════════════════════
BG          = "#0d0f17"          # deep navy-black canvas
PANEL       = "#13151f"          # card/panel background
PANEL2      = "#1a1d2b"          # slightly lighter panel
BORDER      = "#252840"          # subtle border
ACCENT      = "#5b6ef5"          # electric indigo
ACCENT2     = "#9b6ef5"          # violet complement
CYAN        = "#4fd6e3"          # cyber cyan highlight
FG          = "#e8eaf6"          # primary text
FG2         = "#8b90b8"          # secondary text
SUCCESS     = "#69e4a5"          # mint green
WARN        = "#f6c667"          # amber
ERROR       = "#f06680"          # coral red
ENTRY_BG    = "#0b0d14"
FONT_TITLE  = ("Courier", 22, "bold")
FONT_HEAD   = ("Courier", 13, "bold")
FONT_LABEL  = ("Courier", 10)
FONT_SMALL  = ("Courier", 9)
FONT_MONO   = ("Courier", 10)
FONT_ENTRY  = ("Courier", 11)
CORNER      = 10   # canvas rounded-rect radius


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER WIDGETS
# ══════════════════════════════════════════════════════════════════════════════

def rounded_rect(canvas, x1, y1, x2, y2, r=CORNER, **kw):
    """Draw a rounded rectangle on a Canvas."""
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2, x2-r,y2,
           x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


class GlowButton(tk.Canvas):
    """Pixel-perfect rounded button with hover glow."""

    def __init__(self, parent, text, command, width=160, height=38,
                 bg_col=ACCENT, text_col=FG, font=FONT_LABEL, radius=8, **kw):
        super().__init__(parent, width=width, height=height,
                         bg=parent["bg"] if "bg" in parent.keys() else BG,
                         highlightthickness=0, cursor="hand2", **kw)
        self._cmd  = command
        self._btn_width, self._btn_height = width, height
        self._r    = radius
        self._bg   = bg_col
        self._text = text
        self._font = font
        self._tc   = text_col
        self._hover= False
        self._draw()
        self.bind("<Enter>",    self._on_enter)
        self.bind("<Leave>",    self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self):
        self.delete("all")
        col = self._brighten(self._bg, 30) if self._hover else self._bg
        # shadow
        rounded_rect(self, 3, 3, self._btn_width-1, self._btn_height-1, self._r,
                     fill="#000000", outline="")
        # body
        rounded_rect(self, 0, 0, self._btn_width-3, self._btn_height-3, self._r,
                     fill=col, outline=self._brighten(col, 40), width=1)
        # label
        self.create_text(self._btn_width//2-1, self._btn_height//2-1,
                         text=self._text, fill=self._tc,
                         font=self._font, anchor="center")

    def _brighten(self, hex_col, amt):
        hex_col = hex_col.lstrip("#")
        r,g,b = (int(hex_col[i:i+2],16) for i in (0,2,4))
        r,g,b = min(255,r+amt), min(255,g+amt), min(255,b+amt)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _on_enter(self, _): self._hover=True;  self._draw()
    def _on_leave(self, _): self._hover=False; self._draw()
    def _on_click(self, _): self._cmd()


class SectionCard(tk.Frame):
    """Raised card with a coloured left-bar accent."""

    def __init__(self, parent, title="", accent=ACCENT, **kw):
        super().__init__(parent, bg=PANEL, relief="flat",
                         highlightbackground=BORDER, highlightthickness=1, **kw)
        if title:
            hdr = tk.Frame(self, bg=PANEL)
            hdr.pack(fill="x", padx=0, pady=0)
            tk.Frame(hdr, bg=accent, width=4).pack(side="left", fill="y")
            tk.Label(hdr, text=title, bg=PANEL, fg=accent,
                     font=FONT_HEAD, pady=8, padx=12).pack(side="left")


class StatusBar(tk.Label):
    """Animated status label at the bottom of a tab."""

    def __init__(self, parent, **kw):
        super().__init__(parent, text="", bg=PANEL2, fg=FG2,
                         font=FONT_SMALL, anchor="w", padx=12, pady=6, **kw)

    def ok(self, msg):  self.configure(text=f"✔  {msg}", fg=SUCCESS)
    def err(self, msg): self.configure(text=f"✖  {msg}", fg=ERROR)
    def info(self, msg):self.configure(text=f"▸  {msg}", fg=CYAN)
    def clear(self):    self.configure(text="")


class CyberEntry(tk.Frame):
    """Entry with a glowing bottom border that lights up on focus."""

    def __init__(self, parent, show=None, width=38, **kw):
        super().__init__(parent, bg=PANEL, **kw)
        self._line_idle   = BORDER
        self._line_active = ACCENT
        self.entry = tk.Entry(self, bg=ENTRY_BG, fg=FG, font=FONT_ENTRY,
                              insertbackground=CYAN, relief="flat",
                              show=show, width=width,
                              highlightthickness=0)
        self.entry.pack(fill="x", ipady=6, padx=2, pady=(0,0))
        self._bar = tk.Frame(self, bg=self._line_idle, height=2)
        self._bar.pack(fill="x")
        self.entry.bind("<FocusIn>",  lambda _: self._bar.configure(bg=self._line_active))
        self.entry.bind("<FocusOut>", lambda _: self._bar.configure(bg=self._line_idle))

    def get(self):        return self.entry.get()
    def delete(self,a,b): self.entry.delete(a,b)
    def insert(self,i,s): self.entry.insert(i,s)
    def bind(self, *a, **kw): self.entry.bind(*a, **kw)


# ══════════════════════════════════════════════════════════════════════════════
#  ANIMATED SIDEBAR NAV
# ══════════════════════════════════════════════════════════════════════════════

NAV_ITEMS = [
    ("☯", "Hybrid Crypto"),
    ("✍", "Digital Signatures"),
    ("🔑", "Key Manager"),
    ("⬡", "File Encryption"),
    ("◈", "Data Integrity"),
    ("⬢", "Hashing"),
    ("◇", "Ciphers"),
    ("◎", "About"),
]


class SideNav(tk.Frame):
    def __init__(self, parent, on_select, **kw):
        super().__init__(parent, bg=PANEL, width=210, **kw)
        self.pack_propagate(False)
        self._on_select = on_select
        self._buttons   = []
        self._selected  = 0

        # Logo area
        logo = tk.Frame(self, bg=PANEL)
        logo.pack(fill="x", pady=(28, 24), padx=16)
        tk.Label(logo, text="⬡", bg=PANEL, fg=ACCENT,
                 font=("Courier", 28, "bold")).pack(side="left", padx=(0, 8))
        lv = tk.Frame(logo, bg=PANEL)
        lv.pack(side="left")
        tk.Label(lv, text="CIPHER", bg=PANEL, fg=FG,
                 font=("Courier", 14, "bold")).pack(anchor="w")
        tk.Label(lv, text="SHIELD", bg=PANEL, fg=ACCENT2,
                 font=("Courier", 14, "bold")).pack(anchor="w")

        # Divider
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=12, pady=(0, 12))

        # Nav buttons
        for i, (icon, label) in enumerate(NAV_ITEMS):
            btn = self._make_nav_btn(i, icon, label)
            btn.pack(fill="x", padx=10, pady=3)
            self._buttons.append(btn)

        # Bottom badge
        tk.Frame(self, bg=PANEL).pack(expand=True, fill="both")
        badge = tk.Frame(self, bg=PANEL2,
                         highlightbackground=BORDER, highlightthickness=1)
        badge.pack(fill="x", padx=12, pady=16)
        tk.Label(badge, text="InfoSec Project", bg=PANEL2, fg=FG2,
                 font=FONT_SMALL, pady=8).pack()

        self._highlight(0)

    def _make_nav_btn(self, idx, icon, label):
        f = tk.Frame(self, bg=PANEL, cursor="hand2")
        f._idx = idx
        ico = tk.Label(f, text=icon, bg=PANEL, fg=FG2,
                       font=("Courier", 14), padx=14, pady=10)
        ico.pack(side="left")
        lbl = tk.Label(f, text=label, bg=PANEL, fg=FG2,
                       font=FONT_LABEL, anchor="w")
        lbl.pack(side="left", fill="x", expand=True)
        f._ico, f._lbl = ico, lbl

        def on_enter(_): 
            if f._idx != self._selected:
                f.configure(bg=PANEL2); ico.configure(bg=PANEL2); lbl.configure(bg=PANEL2)
        def on_leave(_):
            if f._idx != self._selected:
                f.configure(bg=PANEL); ico.configure(bg=PANEL); lbl.configure(bg=PANEL)
        def on_click(_):
            self._highlight(f._idx)
            self._on_select(f._idx)

        for w in (f, ico, lbl):
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)
        return f

    def _highlight(self, idx):
        for i, f in enumerate(self._buttons):
            if i == idx:
                f.configure(bg=ACCENT)
                f._ico.configure(bg=ACCENT, fg=FG)
                f._lbl.configure(bg=ACCENT, fg=FG)
            else:
                f.configure(bg=PANEL)
                f._ico.configure(bg=PANEL, fg=FG2)
                f._lbl.configure(bg=PANEL, fg=FG2)
        self._selected = idx


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

class CipherShieldApp:
    def __init__(self, root):
        self.root = root
        root.title("CipherShield  –  Secure Cryptography Suite")
        root.configure(bg=BG)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{sw}x{sh}")
        root.resizable(True, True)
        self._build_ui()

    # ── Layout skeleton ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Top chrome bar
        chrome = tk.Frame(self.root, bg=PANEL, height=46)
        chrome.pack(fill="x", side="top")
        chrome.pack_propagate(False)
        tk.Label(chrome, text="  CIPHERSHIELD  —  Secure Cryptography Suite",
                 bg=PANEL, fg=FG2, font=FONT_SMALL).pack(side="left", padx=8)
        tk.Label(chrome, text="v2.0  ●  AES-256  ●  SHA-256",
                 bg=PANEL, fg=FG2, font=FONT_SMALL).pack(side="right", padx=16)

        # Main body
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True)

        # Sidebar
        self.nav = SideNav(body, self._switch_tab)
        self.nav.pack(side="left", fill="y")

        # Thin separator line
        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y")

        # Content area
        self.content = tk.Frame(body, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        # Build all tabs (hidden initially)
        self._tabs = []
        builders = [
            self._build_hybrid_tab,
            self._build_signature_tab,
            self._build_key_manager_tab,
            self._build_encryption_tab,
            self._build_dataloss_tab,
            self._build_hashing_tab,
            self._build_ciphers_tab,
            self._build_about_tab,
        ]
        for b in builders:
            tab = tk.Frame(self.content, bg=BG)
            b(tab)
            self._tabs.append(tab)

        self._switch_tab(0)

    def _switch_tab(self, idx):
        for t in self._tabs:
            t.pack_forget()
        self._tabs[idx].pack(fill="both", expand=True)

    # ── Reusable sub-widgets ──────────────────────────────────────────────────

    def _tab_header(self, parent, icon, title, subtitle):
        hdr = tk.Frame(parent, bg=BG)
        hdr.pack(fill="x", padx=36, pady=(32, 24))
        tk.Label(hdr, text=icon, bg=BG, fg=ACCENT,
                 font=("Courier", 32, "bold")).pack(side="left", padx=(0, 16))
        tv = tk.Frame(hdr, bg=BG)
        tv.pack(side="left")
        tk.Label(tv, text=title, bg=BG, fg=FG,
                 font=("Courier", 18, "bold")).pack(anchor="w")
        tk.Label(tv, text=subtitle, bg=BG, fg=FG2, font=FONT_SMALL).pack(anchor="w")
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=36, pady=(0, 24))

    def _field_row(self, parent, label_text, widget_factory, pad_y=8):
        row = tk.Frame(parent, bg=parent["bg"])
        row.pack(fill="x", pady=pad_y)
        tk.Label(row, text=label_text, bg=parent["bg"], fg=FG2,
                 font=FONT_SMALL, width=18, anchor="e").pack(side="left", padx=(0, 10))
        w = widget_factory(row)
        w.pack(side="left")
        return w

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB 0  –  HYBRID CRYPTOGRAPHY
    # ═══════════════════════════════════════════════════════════════════════

    def _build_hybrid_tab(self, tab):
        self._tab_header(tab, "☯", "Hybrid Cryptography System",
                         "RSA-2048 (Asymmetric) + AES-256 GCM (Symmetric) for high-security file vaulting")

        self.hybrid_file = None
        self.pub_key_path = None
        self.priv_key_path = None
        
        inner = tk.Frame(tab, bg=BG)
        inner.pack(fill="both", expand=True, padx=36)

        # ── Step 1: RSA Key Management ──
        kc = SectionCard(inner, title="1. RSA Key Management", accent=ACCENT2)
        kc.pack(fill="x", pady=(0, 14))
        kbody = tk.Frame(kc, bg=PANEL)
        kbody.pack(fill="x", padx=16, pady=(8, 16))
        
        tk.Label(kbody, text="To use hybrid encryption, you need an RSA Key Pair.\nThe Public Key encrypts, and the Private Key decrypts.",
                 bg=PANEL, fg=FG2, font=FONT_SMALL, justify="left").pack(side="left")
        
        GlowButton(kbody, " GENERATE RSA PAIR ", self._hybrid_generate_keys,
                   width=180, height=32, bg_col=SUCCESS, text_col=BG).pack(side="right")

        # ── Step 2: Select Keys ──
        skc = SectionCard(inner, title="2. Select Keys", accent=ACCENT)
        skc.pack(fill="x", pady=(0, 14))
        skbody = tk.Frame(skc, bg=PANEL)
        skbody.pack(fill="x", padx=16, pady=(8, 16))

        # Public Key Row
        pub_row = tk.Frame(skbody, bg=PANEL)
        pub_row.pack(fill="x", pady=(0, 8))
        self.lbl_pub_key = tk.Label(pub_row, text="Public Key: No key loaded (Needed for Encryption)", 
                                    bg=PANEL, fg=FG2, font=FONT_SMALL, anchor="w")
        self.lbl_pub_key.pack(side="left", fill="x", expand=True)
        GlowButton(pub_row, " LOAD PUBLIC ", self._hybrid_browse_public,
                   width=120, height=30, bg_col=PANEL2, text_col=ACCENT).pack(side="right")

        # Private Key Row
        priv_row = tk.Frame(skbody, bg=PANEL)
        priv_row.pack(fill="x")
        self.lbl_priv_key = tk.Label(priv_row, text="Private Key: No key loaded (Needed for Decryption)", 
                                     bg=PANEL, fg=FG2, font=FONT_SMALL, anchor="w")
        self.lbl_priv_key.pack(side="left", fill="x", expand=True)
        GlowButton(priv_row, " LOAD PRIVATE ", self._hybrid_browse_private,
                   width=120, height=30, bg_col=PANEL2, text_col=ACCENT2).pack(side="right")

        # ── Step 3: Target File ──
        fc = SectionCard(inner, title="3. Select Target File", accent=CYAN)
        fc.pack(fill="x", pady=(0, 14))
        fbody = tk.Frame(fc, bg=PANEL)
        fbody.pack(fill="x", padx=16, pady=(8, 16))

        self.lbl_hyb_file = tk.Label(fbody, text="No file selected",
                                     bg=PANEL, fg=FG2, font=FONT_SMALL, anchor="w")
        self.lbl_hyb_file.pack(side="left", fill="x", expand=True)
        GlowButton(fbody, "  BROWSE  ", self._hybrid_browse_file,
                   width=110, height=32, bg_col=PANEL2, text_col=CYAN).pack(side="right")

        # ── Actions ──
        ac = SectionCard(inner, title="Actions", accent=ACCENT)
        ac.pack(fill="x", pady=(0, 14))
        abody = tk.Frame(ac, bg=PANEL)
        abody.pack(fill="x", padx=16, pady=(8, 16))

        GlowButton(abody, "  🔒  HYBRID ENCRYPT  ", self._hybrid_action_encrypt,
                   width=190, height=38, bg_col=ACCENT).pack(side="left", padx=(0, 12))
        GlowButton(abody, "  🔓  HYBRID DECRYPT  ", self._hybrid_action_decrypt,
                   width=190, height=38, bg_col="#3a3d6b", text_col=CYAN).pack(side="left")

        # ── Status ──
        self.hyb_status = StatusBar(inner)
        self.hyb_status.pack(fill="x", pady=(4, 0))

    def _hybrid_browse_file(self):
        p = filedialog.askopenfilename()
        if p:
            self.hybrid_file = p
            self.lbl_hyb_file.configure(text=f"{shorten_path(p)}   ({get_file_size_str(p)})", fg=FG)

    def _hybrid_browse_public(self):
        p = filedialog.askopenfilename(filetypes=[("PEM Files", "*.pem"), ("All Files", "*.*")])
        if p:
            self.pub_key_path = p
            self.lbl_pub_key.configure(text=f"Public Key: {shorten_path(p)}", fg=SUCCESS)

    def _hybrid_browse_private(self):
        p = filedialog.askopenfilename(filetypes=[("PEM Files", "*.pem"), ("All Files", "*.*")])
        if p:
            self.priv_key_path = p
            self.lbl_priv_key.configure(text=f"Private Key: {shorten_path(p)}", fg=SUCCESS)

    def _hybrid_generate_keys(self):
        folder = filedialog.askdirectory(title="Select Folder to Save RSA Keys")
        if folder:
            try:
                priv, pub = hybrid_crypto.generate_rsa_keys()
                priv_p, pub_p = hybrid_crypto.save_keys(priv, pub, folder)
                self.pub_key_path = pub_p
                self.priv_key_path = priv_p
                self.lbl_pub_key.configure(text=f"Public Key: {shorten_path(pub_p)}", fg=SUCCESS)
                self.lbl_priv_key.configure(text=f"Private Key: {shorten_path(priv_p)}", fg=SUCCESS)
                messagebox.showinfo("Keys Generated", f"RSA Key Pair successfully generated!\n\nPrivate: {priv_p}\nPublic: {pub_p}\n\nKEEP YOUR PRIVATE KEY SAFE!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate keys: {e}")

    def _hybrid_action_encrypt(self):
        if not self.hybrid_file: return messagebox.showwarning("No File", "Select a file to encrypt.")
        if not self.pub_key_path: return messagebox.showwarning("No Public Key", "Select a Public Key to encrypt the session key.")
        
        self.hyb_status.info("Performing Hybrid Encryption...")
        def task():
            ok, msg = hybrid_crypto.hybrid_encrypt(self.hybrid_file, self.pub_key_path)
            self.root.after(0, self._hybrid_done, ok, msg, "encrypt")
        threading.Thread(target=task, daemon=True).start()

    def _hybrid_action_decrypt(self):
        if not self.hybrid_file: return messagebox.showwarning("No File", "Select a .hyb file to decrypt.")
        if not self.priv_key_path: return messagebox.showwarning("No Private Key", "Select your Private Key to decrypt the session key.")
        
        self.hyb_status.info("Performing Hybrid Decryption...")
        def task():
            ok, msg = hybrid_crypto.hybrid_decrypt(self.hybrid_file, self.priv_key_path)
            self.root.after(0, self._hybrid_done, ok, msg, "decrypt")
        threading.Thread(target=task, daemon=True).start()

    def _hybrid_done(self, ok, msg, op):
        if ok:
            self.hyb_status.ok(f"Hybrid {op} successful: {shorten_path(msg)}")
            messagebox.showinfo("Success", f"Hybrid {op} completed!\n\nResult: {msg}")
        else:
            self.hyb_status.err(msg)
            messagebox.showerror("Error", msg)

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB - DIGITAL SIGNATURES
    # ═══════════════════════════════════════════════════════════════════════

    def _build_signature_tab(self, tab):
        self._tab_header(tab, "✍", "Digital Signatures",
                         "Sign files to prove authenticity (RSA-PSS with SHA-256)")

        self.sig_file = None
        self.sig_key_path = None
        self.sig_cert_path = None
        
        inner = tk.Frame(tab, bg=BG)
        inner.pack(fill="both", expand=True, padx=36)

        # ── Step 1: Target File ──
        fc = SectionCard(inner, title="1. Select Target File", accent=ACCENT)
        fc.pack(fill="x", pady=(0, 14))
        fbody = tk.Frame(fc, bg=PANEL)
        fbody.pack(fill="x", padx=16, pady=(8, 16))

        self.lbl_sig_file = tk.Label(fbody, text="No file selected",
                                     bg=PANEL, fg=FG2, font=FONT_SMALL, anchor="w")
        self.lbl_sig_file.pack(side="left", fill="x", expand=True)
        GlowButton(fbody, "  BROWSE  ", self._sig_browse_file,
                   width=110, height=32, bg_col=PANEL2, text_col=ACCENT).pack(side="right")

        # ── Step 2: Keys ──
        kc = SectionCard(inner, title="2. Select Key", accent=ACCENT2)
        kc.pack(fill="x", pady=(0, 14))
        kbody = tk.Frame(kc, bg=PANEL)
        kbody.pack(fill="x", padx=16, pady=(8, 16))

        tk.Label(kbody, text="Signing requires your PRIVATE key. Verifying requires the signer's PUBLIC key.",
                 bg=PANEL, fg=FG2, font=FONT_SMALL, justify="left").pack(anchor="w", pady=(0,8))
                 
        key_row = tk.Frame(kbody, bg=PANEL)
        key_row.pack(fill="x")
        self.lbl_sig_key = tk.Label(key_row, text="No key loaded", 
                                    bg=PANEL, fg=FG2, font=FONT_SMALL, anchor="w")
        self.lbl_sig_key.pack(side="left", fill="x", expand=True)
        GlowButton(key_row, " LOAD KEY ", self._sig_browse_key,
                   width=120, height=30, bg_col=PANEL2, text_col=ACCENT2).pack(side="right")

        # ── Step 3: Signature File (Verify Only) ──
        vc = SectionCard(inner, title="3. Select Signature File (Verify Only)", accent=CYAN)
        vc.pack(fill="x", pady=(0, 14))
        vbody = tk.Frame(vc, bg=PANEL)
        vbody.pack(fill="x", padx=16, pady=(8, 16))
        
        self.lbl_sig_cert = tk.Label(vbody, text="Select the .sig file generated during signing",
                                     bg=PANEL, fg=FG2, font=FONT_SMALL, anchor="w")
        self.lbl_sig_cert.pack(side="left", fill="x", expand=True)
        GlowButton(vbody, " BROWSE SIG ", self._sig_browse_cert,
                   width=130, height=30, bg_col=PANEL2, text_col=CYAN).pack(side="right")

        # ── Actions ──
        ac = SectionCard(inner, title="Actions", accent=ACCENT)
        ac.pack(fill="x", pady=(0, 14))
        abody = tk.Frame(ac, bg=PANEL)
        abody.pack(fill="x", padx=16, pady=(8, 16))

        GlowButton(abody, "  ✍  SIGN FILE  ", self._sig_action_sign,
                   width=180, height=38, bg_col=ACCENT).pack(side="left", padx=(0, 12))
        GlowButton(abody, "  ✅  VERIFY SIG  ", self._sig_action_verify,
                   width=180, height=38, bg_col="#3a3d6b", text_col=CYAN).pack(side="left")

        # ── Status ──
        self.sig_status = StatusBar(inner)
        self.sig_status.pack(fill="x", pady=(4, 0))

    def _sig_browse_file(self):
        p = filedialog.askopenfilename()
        if p:
            self.sig_file = p
            self.lbl_sig_file.configure(text=f"{shorten_path(p)}   ({get_file_size_str(p)})", fg=FG)

    def _sig_browse_key(self):
        p = filedialog.askopenfilename(filetypes=[("PEM Files", "*.pem"), ("All Files", "*.*")])
        if p:
            self.sig_key_path = p
            self.lbl_sig_key.configure(text=f"Key: {shorten_path(p)}", fg=SUCCESS)

    def _sig_browse_cert(self):
        p = filedialog.askopenfilename(filetypes=[("Signature Files", "*.sig"), ("All Files", "*.*")])
        if p:
            self.sig_cert_path = p
            self.lbl_sig_cert.configure(text=f"Signature: {shorten_path(p)}", fg=SUCCESS)

    def _sig_action_sign(self):
        if not self.sig_file: return messagebox.showwarning("No File", "Select a file to sign.")
        if not self.sig_key_path: return messagebox.showwarning("No Key", "Select a Private Key to sign with.")
        
        self.sig_status.info("Generating RSA-PSS Signature...")
        def task():
            ok, msg = digital_signature.sign_file(self.sig_file, self.sig_key_path)
            self.root.after(0, self._sig_done, ok, msg, "Sign")
        threading.Thread(target=task, daemon=True).start()

    def _sig_action_verify(self):
        if not self.sig_file: return messagebox.showwarning("No File", "Select the original file.")
        if not self.sig_cert_path: return messagebox.showwarning("No Signature", "Select the .sig signature file.")
        if not self.sig_key_path: return messagebox.showwarning("No Key", "Select the signer's Public Key.")
        
        self.sig_status.info("Verifying Signature...")
        def task():
            ok, msg = digital_signature.verify_signature(self.sig_file, self.sig_cert_path, self.sig_key_path)
            self.root.after(0, self._sig_done, ok, msg, "Verify")
        threading.Thread(target=task, daemon=True).start()

    def _sig_done(self, ok, msg, op):
        if ok:
            self.sig_status.ok(f"{op} successful: {shorten_path(msg) if op=='Sign' else msg}")
            messagebox.showinfo("Success", f"{op} completed!\n\nResult: {msg}")
        else:
            self.sig_status.err(msg)
            messagebox.showerror("Error", msg)

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB - KEY MANAGER
    # ═══════════════════════════════════════════════════════════════════════

    def _build_key_manager_tab(self, tab):
        self._tab_header(tab, "🔑", "Key Manager",
                         "Central registry for all RSA cryptographic keys")
                         
        inner = tk.Frame(tab, bg=BG)
        inner.pack(fill="both", expand=True, padx=36)
        
        # ── Key Registry Table ──
        rc = SectionCard(inner, title="Registered Keys", accent=CYAN)
        rc.pack(fill="both", expand=True, pady=(0, 14))
        rbody = tk.Frame(rc, bg=PANEL)
        rbody.pack(fill="both", expand=True, padx=16, pady=(8, 16))
        
        # Treeview for keys
        cols = ("ID", "Label", "Algorithm", "Bits", "Created")
        self.key_tree = ttk.Treeview(rbody, columns=cols, show="headings", height=8)
        
        # Configure style
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=ENTRY_BG, foreground=FG, fieldbackground=ENTRY_BG, borderwidth=0, font=FONT_SMALL)
        style.map("Treeview", background=[("selected", ACCENT)])
        style.configure("Treeview.Heading", background=PANEL2, foreground=FG2, font=FONT_HEAD, borderwidth=1)
        
        self.key_tree.heading("ID", text="ID")
        self.key_tree.heading("Label", text="Label")
        self.key_tree.heading("Algorithm", text="Alg")
        self.key_tree.heading("Bits", text="Bits")
        self.key_tree.heading("Created", text="Created On")
        
        self.key_tree.column("ID", width=40, anchor="center")
        self.key_tree.column("Label", width=200)
        self.key_tree.column("Algorithm", width=80, anchor="center")
        self.key_tree.column("Bits", width=80, anchor="center")
        self.key_tree.column("Created", width=150, anchor="center")
        
        sb = tk.Scrollbar(rbody, orient="vertical", command=self.key_tree.yview, bg=PANEL2, troughcolor=PANEL2, relief="flat")
        self.key_tree.configure(yscrollcommand=sb.set)
        
        sb.pack(side="right", fill="y")
        self.key_tree.pack(side="left", fill="both", expand=True)
        
        # ── Actions ──
        ac = SectionCard(inner, title="Key Actions", accent=ACCENT2)
        ac.pack(fill="x", pady=(0, 14))
        abody = tk.Frame(ac, bg=PANEL)
        abody.pack(fill="x", padx=16, pady=(8, 16))
        
        GlowButton(abody, " ➕ GENERATE NEW KEY ", self._km_generate,
                   width=200, height=35, bg_col=SUCCESS, text_col=BG).pack(side="left", padx=(0,10))
        GlowButton(abody, " 🗑 DELETE SELECTED ", self._km_delete,
                   width=200, height=35, bg_col=ERROR, text_col=BG).pack(side="left")
                   
        self._km_refresh()

    def _km_refresh(self):
        for item in self.key_tree.get_children():
            self.key_tree.delete(item)
        keys = key_manager.list_keys()
        for k in keys:
            self.key_tree.insert("", "end", values=(k["id"], k["label"], k["algorithm"], k["bits"], k["created_at"]))

    def _km_generate(self):
        # Mini dialog to ask for label and folder
        top = tk.Toplevel(self.root)
        top.title("Generate New Key")
        top.geometry("400x250")
        top.configure(bg=BG)
        top.transient(self.root)
        top.grab_set()
        
        tk.Label(top, text="Generate New RSA Key Pair", bg=BG, fg=FG, font=FONT_TITLE).pack(pady=10)
        
        lbl_frame = tk.Frame(top, bg=BG)
        lbl_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(lbl_frame, text="Key Label:", bg=BG, fg=FG2).pack(side="left")
        entry_lbl = CyberEntry(lbl_frame, width=30)
        entry_lbl.pack(side="right")
        
        def do_gen():
            label = entry_lbl.get().strip()
            if not label: return messagebox.showwarning("Empty", "Provide a label for the key.", parent=top)
            folder = filedialog.askdirectory(parent=top, title="Select folder to save PEM files")
            if not folder: return
            
            try:
                priv, pub = hybrid_crypto.generate_rsa_keys()
                priv_path, pub_path = hybrid_crypto.save_keys(priv, pub, folder)
                key_manager.add_key(label, priv_path, pub_path)
                messagebox.showinfo("Success", f"Key '{label}' generated and registered!", parent=top)
                self._km_refresh()
                top.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate key: {e}", parent=top)
                
        GlowButton(top, " GENERATE ", do_gen, width=150, height=35, bg_col=SUCCESS, text_col=BG).pack(pady=15)

    def _km_delete(self):
        selected = self.key_tree.selection()
        if not selected: return messagebox.showwarning("No Selection", "Select a key to delete.")
        
        item = self.key_tree.item(selected[0])
        key_id = item["values"][0]
        label = item["values"][1]
        
        if messagebox.askyesno("Confirm Delete", f"Remove '{label}' from registry?\n\nNote: This does not delete the actual PEM files from your disk."):
            if key_manager.delete_key(key_id):
                self._km_refresh()
                messagebox.showinfo("Deleted", "Key removed from registry.")
            else:
                messagebox.showerror("Error", "Could not delete key.")

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB - FILE ENCRYPTION
    # ═══════════════════════════════════════════════════════════════════════

    def _build_encryption_tab(self, tab):
        self._tab_header(tab, "⬡", "File Encryption",
                         "AES-256 symmetric encryption via Fernet / PBKDF2HMAC key derivation")

        self.enc_file = None
        inner = tk.Frame(tab, bg=BG)
        inner.pack(fill="both", expand=True, padx=36)

        # ── File card ──
        fc = SectionCard(inner, title="Select Target File", accent=ACCENT)
        fc.pack(fill="x", pady=(0, 14))
        body = tk.Frame(fc, bg=PANEL)
        body.pack(fill="x", padx=16, pady=(8, 16))

        self.lbl_enc_file = tk.Label(body, text="No file selected  —  click Browse to choose",
                                     bg=PANEL, fg=FG2, font=FONT_SMALL, anchor="w")
        self.lbl_enc_file.pack(side="left", fill="x", expand=True)
        GlowButton(body, "  BROWSE  ", self._enc_browse,
                   width=110, height=32, bg_col=PANEL2, text_col=ACCENT).pack(side="right")

        # ── Auth card ──
        pc = SectionCard(inner, title="Authentication (Password or Key File)", accent=ACCENT2)
        pc.pack(fill="x", pady=(0, 14))
        pbody = tk.Frame(pc, bg=PANEL)
        pbody.pack(fill="x", padx=16, pady=(8, 6))

        # Mode selector
        self.auth_mode_var = tk.StringVar(value="password")
        mode_frame = tk.Frame(pbody, bg=PANEL)
        mode_frame.pack(fill="x", pady=(0, 10))
        tk.Radiobutton(mode_frame, text="Use Password", variable=self.auth_mode_var, value="password", bg=PANEL, fg=FG, selectcolor=ACCENT, activebackground=PANEL, activeforeground=FG, command=self._toggle_auth, indicatoron=1).pack(side="left", padx=(0, 20))
        tk.Radiobutton(mode_frame, text="Use Key File", variable=self.auth_mode_var, value="key", bg=PANEL, fg=FG, selectcolor=ACCENT, activebackground=PANEL, activeforeground=FG, command=self._toggle_auth, indicatoron=1).pack(side="left", padx=(0, 20))
        tk.Radiobutton(mode_frame, text="Use MFA Vault", variable=self.auth_mode_var, value="mfa", bg=PANEL, fg=FG, selectcolor=ACCENT, activebackground=PANEL, activeforeground=FG, command=self._toggle_auth, indicatoron=1).pack(side="left")

        # --- Password Section ---
        self.pwd_frame = tk.Frame(pbody, bg=PANEL)
        self.pwd_frame.pack(fill="x")
        tk.Label(self.pwd_frame, text="Enter password:", bg=PANEL, fg=FG2, font=FONT_SMALL).pack(anchor="w")
        self.entry_enc_pwd = CyberEntry(self.pwd_frame, show="●", width=50)
        self.entry_enc_pwd.pack(fill="x", pady=(4, 8))
        self.entry_enc_pwd.bind("<KeyRelease>", self._enc_pwd_strength)

        # Strength bar
        sb_frame = tk.Frame(self.pwd_frame, bg=PANEL)
        sb_frame.pack(fill="x", pady=(0, 10))
        tk.Label(sb_frame, text="Strength:", bg=PANEL, fg=FG2, font=FONT_SMALL).pack(side="left")
        self._strength_bars = []
        bar_wrap = tk.Frame(sb_frame, bg=PANEL)
        bar_wrap.pack(side="left", padx=8)
        for _ in range(4):
            b = tk.Frame(bar_wrap, bg=BORDER, width=44, height=6)
            b.pack(side="left", padx=2)
            b.pack_propagate(False)
            self._strength_bars.append(b)
        self.lbl_strength_txt = tk.Label(sb_frame, text="", bg=PANEL, fg=FG2, font=FONT_SMALL)
        self.lbl_strength_txt.pack(side="left", padx=8)

        # --- Key File Section ---
        self.key_frame = tk.Frame(pbody, bg=PANEL)
        self.key_file_path = None
        self.lbl_key_file = tk.Label(self.key_frame, text="No key file selected", bg=PANEL, fg=FG2, font=FONT_SMALL, anchor="w")
        self.lbl_key_file.pack(side="left", fill="x", expand=True)
        GlowButton(self.key_frame, " BROWSE KEY ", self._key_browse, width=120, height=32, bg_col=PANEL2, text_col=ACCENT).pack(side="right", padx=(10, 0))
        GlowButton(self.key_frame, " GENERATE NEW KEY ", self._key_generate, width=170, height=32, bg_col=SUCCESS, text_col=BG).pack(side="right")
        
        # --- MFA Section ---
        self.mfa_frame = tk.Frame(pbody, bg=PANEL)
        self.lbl_mfa_status = tk.Label(self.mfa_frame, text="Vault Configured - Ready" if mfa_vault.is_vault_configured() else "Vault Not Configured - Click Setup", bg=PANEL, fg=SUCCESS if mfa_vault.is_vault_configured() else ERROR, font=FONT_SMALL)
        self.lbl_mfa_status.pack(side="top", anchor="w", pady=(0, 8))
        
        mfa_input_frame = tk.Frame(self.mfa_frame, bg=PANEL)
        mfa_input_frame.pack(fill="x")
        tk.Label(mfa_input_frame, text="6-Digit MFA Code:", bg=PANEL, fg=FG2, font=FONT_SMALL).pack(side="left")
        self.entry_mfa_code = CyberEntry(mfa_input_frame, width=15)
        self.entry_mfa_code.pack(side="left", padx=10)
        GlowButton(mfa_input_frame, " SETUP MFA VAULT ", self._open_mfa_setup, width=160, height=32, bg_col=ACCENT2, text_col=BG).pack(side="right")

        self._toggle_auth()

        # ── Action card ──
        ac = SectionCard(inner, title="Actions", accent=CYAN)
        ac.pack(fill="x", pady=(0, 14))
        abody = tk.Frame(ac, bg=PANEL)
        abody.pack(fill="x", padx=16, pady=(8, 16))

        GlowButton(abody, "  🔒  ENCRYPT  ", self._enc_action_encrypt,
                   width=160, height=38, bg_col=ACCENT).pack(side="left", padx=(0, 12))
        GlowButton(abody, "  🔓  DECRYPT  ", self._enc_action_decrypt,
                   width=160, height=38, bg_col="#3a3d6b", text_col=CYAN).pack(side="left")

        # ── Status ──
        self.enc_status = StatusBar(inner)
        self.enc_status.pack(fill="x", pady=(4, 0))

    def _enc_browse(self):
        p = filedialog.askopenfilename()
        if p:
            self.enc_file = p
            self.lbl_enc_file.configure(
                text=f"{shorten_path(p)}   ({get_file_size_str(p)})", fg=FG)

    def _toggle_auth(self):
        self.pwd_frame.pack_forget()
        self.key_frame.pack_forget()
        self.mfa_frame.pack_forget()
        mode = self.auth_mode_var.get()
        if mode == "password":
            self.pwd_frame.pack(fill="x")
        elif mode == "key":
            self.key_frame.pack(fill="x", pady=(4,8))
        elif mode == "mfa":
            self.mfa_frame.pack(fill="x", pady=(4,8))
            cfg = mfa_vault.is_vault_configured()
            self.lbl_mfa_status.configure(text="Vault Configured - Ready" if cfg else "Vault Not Configured - Click Setup", fg=SUCCESS if cfg else ERROR)

    def _key_browse(self):
        p = filedialog.askopenfilename(filetypes=[("Key Files", "*.key"), ("All Files", "*.*")])
        if p:
            self.key_file_path = p
            self.lbl_key_file.configure(text=shorten_path(p), fg=FG)

    def _key_generate(self):
        p = filedialog.asksaveasfilename(defaultextension=".key", filetypes=[("Key Files", "*.key")], initialfile="my_secret.key")
        if p:
            if generate_key_file(p):
                self.key_file_path = p
                self.lbl_key_file.configure(text=shorten_path(p), fg=FG)
                messagebox.showinfo("Success", "Cryptographic Key successfully generated and saved!\n\nYou can now use this key file instead of a password.")
            else:
                messagebox.showerror("Error", "Failed to generate key file.")

    def _open_mfa_setup(self):
        top = tk.Toplevel(self.root)
        top.title("MFA Vault Setup")
        top.geometry("450x550")
        top.configure(bg=BG)
        top.transient(self.root)
        top.grab_set()
        
        tk.Label(top, text="Google Authenticator Setup", bg=BG, fg=FG, font=FONT_TITLE).pack(pady=10)
        tk.Label(top, text="1. Install Google Authenticator or Authy on your phone\n2. Scan the QR code below", bg=BG, fg=FG2).pack()
        
        seed = mfa_vault.generate_mfa_seed()
        uri = mfa_vault.get_provisioning_uri(seed)
        qr_path = "temp_qr.png"
        mfa_vault.generate_qr_code(uri, qr_path)
        
        try:
            from PIL import Image, ImageTk
            img = Image.open(qr_path)
            img = img.resize((200, 200))
            photo = ImageTk.PhotoImage(img)
            lbl_qr = tk.Label(top, image=photo, bg=BG)
            lbl_qr.image = photo
            lbl_qr.pack(pady=15)
        except Exception:
            tk.Label(top, text="[QR Image Error: run `pip install pillow qrcode`]", fg=ERROR, bg=BG).pack(pady=15)
            
        tk.Label(top, text=f"Or enter code manually: {seed}", bg=BG, fg=FG2, font=("Courier", 10)).pack()
        tk.Label(top, text="3. Enter the 6-digit code to verify:", bg=BG, fg=FG).pack(pady=(15, 5))
        
        verify_entry = CyberEntry(top, width=15)
        verify_entry.pack()
        
        def do_verify():
            code = verify_entry.get().strip()
            ok, msg = mfa_vault.setup_vault(seed, code)
            if ok:
                messagebox.showinfo("Success", "MFA Vault configured successfully!", parent=top)
                if os.path.exists(qr_path): os.remove(qr_path)
                self._toggle_auth()
                top.destroy()
            else:
                messagebox.showerror("Error", msg, parent=top)
                
        GlowButton(top, " VERIFY & SAVE ", do_verify, width=150, height=35, bg_col=SUCCESS, text_col=BG).pack(pady=20)

    def _enc_pwd_strength(self, _=None):
        pwd = self.entry_enc_pwd.get()
        if not pwd:
            for b in self._strength_bars: b.configure(bg=BORDER)
            self.lbl_strength_txt.configure(text="", fg=FG2)
            return
        res = check_password_strength(pwd)
        lvl_map = {"Weak":1, "Fair":2, "Good":3, "Strong":4}
        lvl = lvl_map.get(res["strength"], 1)
        for i, b in enumerate(self._strength_bars):
            b.configure(bg=res["color"] if i < lvl else BORDER)
        self.lbl_strength_txt.configure(text=res["strength"], fg=res["color"])

    def _enc_action_encrypt(self):
        if not self.enc_file:
            return messagebox.showwarning("No file", "Please select a file first.")
        
        mode = self.auth_mode_var.get()
        if mode == "password":
            pwd = self.entry_enc_pwd.get()
            if not pwd:
                return messagebox.showwarning("No password", "Please enter a password.")
            self.enc_status.info("Encrypting with Password… please wait")
            def task():
                ok, msg = encrypt_file(self.enc_file, pwd)
                self.root.after(0, self._enc_done, ok, msg, "encrypt")
            threading.Thread(target=task, daemon=True).start()
        elif mode == "key":
            if not self.key_file_path:
                return messagebox.showwarning("No Key", "Please select or generate a Key File.")
            self.enc_status.info("Encrypting with Key File… please wait")
            def task():
                ok, msg = encrypt_file_with_key(self.enc_file, self.key_file_path)
                self.root.after(0, self._enc_done, ok, msg, "encrypt")
            threading.Thread(target=task, daemon=True).start()
        elif mode == "mfa":
            code = self.entry_mfa_code.get().strip()
            if not code or len(code) != 6:
                return messagebox.showwarning("Invalid Code", "Please enter a 6-digit MFA code.")
            self.enc_status.info("Unlocking Vault & Encrypting… please wait")
            def task():
                ok, msg = mfa_vault.encrypt_with_vault(self.enc_file, code)
                self.root.after(0, self._enc_done, ok, msg, "encrypt")
            threading.Thread(target=task, daemon=True).start()

    def _enc_action_decrypt(self):
        if not self.enc_file:
            return messagebox.showwarning("No file", "Please select a file first.")
            
        mode = self.auth_mode_var.get()
        if mode == "password":
            pwd = self.entry_enc_pwd.get()
            if not pwd:
                return messagebox.showwarning("No password", "Please enter a password.")
            self.enc_status.info("Decrypting with Password… please wait")
            def task():
                ok, msg = decrypt_file(self.enc_file, pwd)
                self.root.after(0, self._enc_done, ok, msg, "decrypt")
            threading.Thread(target=task, daemon=True).start()
        elif mode == "key":
            if not self.key_file_path:
                return messagebox.showwarning("No Key", "Please select a Key File.")
            self.enc_status.info("Decrypting with Key File… please wait")
            def task():
                ok, msg = decrypt_file_with_key(self.enc_file, self.key_file_path)
                self.root.after(0, self._enc_done, ok, msg, "decrypt")
            threading.Thread(target=task, daemon=True).start()
        elif mode == "mfa":
            code = self.entry_mfa_code.get().strip()
            if not code or len(code) != 6:
                return messagebox.showwarning("Invalid Code", "Please enter a 6-digit MFA code.")
            self.enc_status.info("Unlocking Vault & Decrypting… please wait")
            def task():
                ok, msg = mfa_vault.decrypt_with_vault(self.enc_file, code)
                self.root.after(0, self._enc_done, ok, msg, "decrypt")
            threading.Thread(target=task, daemon=True).start()

    def _enc_done(self, ok, msg, op):
        if ok:
            self.enc_status.ok(f"File {op}ed → {shorten_path(msg)}")
            messagebox.showinfo("Success", f"File {op}ed successfully!\n\n{msg}")
        else:
            self.enc_status.err(msg)
            messagebox.showerror("Error", msg)

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB 2  –  DATA INTEGRITY
    # ═══════════════════════════════════════════════════════════════════════

    def _build_dataloss_tab(self, tab):
        self._tab_header(tab, "◈", "Data Integrity Proof",
                         "Encrypt → Decrypt → compare SHA-256 hashes to prove zero data loss")

        self.int_file = None
        inner = tk.Frame(tab, bg=BG)
        inner.pack(fill="both", expand=True, padx=36)

        # File card
        fc = SectionCard(inner, title="Select Dataset / File", accent=ACCENT)
        fc.pack(fill="x", pady=(0, 14))
        fbody = tk.Frame(fc, bg=PANEL)
        fbody.pack(fill="x", padx=16, pady=(8, 16))
        self.lbl_int_file = tk.Label(fbody, text="No file selected",
                                     bg=PANEL, fg=FG2, font=FONT_SMALL, anchor="w")
        self.lbl_int_file.pack(side="left", fill="x", expand=True)
        GlowButton(fbody, "  BROWSE  ", self._int_browse,
                   width=110, height=32, bg_col=PANEL2, text_col=ACCENT).pack(side="right")

        # Run button
        rc = SectionCard(inner, title="Run Test", accent=CYAN)
        rc.pack(fill="x", pady=(0, 14))
        rbody = tk.Frame(rc, bg=PANEL)
        rbody.pack(fill="x", padx=16, pady=(8, 16))
        GlowButton(rbody, "  ▶  RUN INTEGRITY TEST  ", self._int_run,
                   width=240, height=38, bg_col=ACCENT).pack(side="left")

        # Log card
        lc = SectionCard(inner, title="Output Log", accent=ACCENT2)
        lc.pack(fill="both", expand=True, pady=(0, 14))
        lbody = tk.Frame(lc, bg=PANEL)
        lbody.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        self.txt_int = tk.Text(lbody, bg=ENTRY_BG, fg=CYAN, font=FONT_MONO,
                               relief="flat", state="disabled",
                               selectbackground=ACCENT, padx=10, pady=8)
        sb = tk.Scrollbar(lbody, command=self.txt_int.yview,
                          bg=PANEL2, troughcolor=PANEL2, relief="flat")
        self.txt_int.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt_int.pack(fill="both", expand=True)

    def _int_browse(self):
        p = filedialog.askopenfilename()
        if p:
            self.int_file = p
            self.lbl_int_file.configure(
                text=f"{shorten_path(p)}   ({get_file_size_str(p)})", fg=FG)

    def _int_log(self, msg):
        self.txt_int.configure(state="normal")
        self.txt_int.insert("end", msg + "\n")
        self.txt_int.see("end")
        self.txt_int.configure(state="disabled")

    def _int_run(self):
        if not self.int_file:
            return messagebox.showwarning("No file", "Please select a file first.")
        self.txt_int.configure(state="normal"); self.txt_int.delete("1.0","end")
        self.txt_int.configure(state="disabled")
        threading.Thread(target=self._int_task, daemon=True).start()

    def _int_task(self):
        log = lambda m: self.root.after(0, self._int_log, m)
        log("► Step 1/4  —  Computing original SHA-256 hash…")
        orig = hash_file_sha256(self.int_file)
        log(f"  Original : {orig}\n")
        pwd = "integrity_test_pw_777!"
        log("► Step 2/4  —  Encrypting dataset with AES-256…")
        ok, enc = encrypt_file(self.int_file, pwd)
        if not ok: log(f"  ERROR: {enc}"); return
        log(f"  Encrypted: {shorten_path(enc)}\n")
        log("► Step 3/4  —  Decrypting back to original bytes…")
        ok, dec = decrypt_file(enc, pwd)
        if not ok: log(f"  ERROR: {dec}"); return
        log(f"  Decrypted: {shorten_path(dec)}\n")
        log("► Step 4/4  —  Computing decrypted SHA-256 hash…")
        dhash = hash_file_sha256(dec)
        log(f"  Decrypted: {dhash}\n")
        log("─" * 60)
        if orig == dhash:
            log("  ✔  HASHES MATCH  —  ZERO DATA LOSS CONFIRMED")
            log("  Encryption is 100 % lossless (AES is a bijection).")
        else:
            log("  ✖  HASH MISMATCH  —  DATA CORRUPTION DETECTED")
        log("─" * 60)
        try:
            if os.path.exists(enc): os.remove(enc)
            if os.path.exists(dec): os.remove(dec)
        except: pass

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB 3  –  HASHING
    # ═══════════════════════════════════════════════════════════════════════

    def _build_hashing_tab(self, tab):
        self._tab_header(tab, "⬢", "Cryptographic Hashing",
                         "One-way hash functions  —  SHA-256 & MD5")

        inner = tk.Frame(tab, bg=BG)
        inner.pack(fill="both", expand=True, padx=36)

        # Input card
        ic = SectionCard(inner, title="Input Text", accent=ACCENT)
        ic.pack(fill="x", pady=(0, 14))
        ibody = tk.Frame(ic, bg=PANEL)
        ibody.pack(fill="x", padx=16, pady=(8, 16))
        self.txt_hash_in = tk.Text(ibody, bg=ENTRY_BG, fg=FG, font=FONT_ENTRY,
                                   height=5, relief="flat",
                                   insertbackground=CYAN, padx=8, pady=6)
        self.txt_hash_in.pack(fill="x")

        # Buttons
        bc = SectionCard(inner, title="Hash Algorithm", accent=ACCENT2)
        bc.pack(fill="x", pady=(0, 14))
        bbody = tk.Frame(bc, bg=PANEL)
        bbody.pack(fill="x", padx=16, pady=(8, 16))
        GlowButton(bbody, "  SHA-256  ", self._hash_sha256,
                   width=140, height=36, bg_col=ACCENT).pack(side="left", padx=(0,12))
        GlowButton(bbody, "  MD5  ", self._hash_md5,
                   width=140, height=36, bg_col="#5b3e9e", text_col=FG).pack(side="left")

        # Output card
        oc = SectionCard(inner, title="Hash Output", accent=CYAN)
        oc.pack(fill="x", pady=(0, 14))
        obody = tk.Frame(oc, bg=PANEL)
        obody.pack(fill="x", padx=16, pady=(8, 16))
        self.txt_hash_out = tk.Text(obody, bg=ENTRY_BG, fg=CYAN, font=FONT_MONO,
                                    height=3, relief="flat",
                                    insertbackground=CYAN, padx=8, pady=6,
                                    state="disabled")
        self.txt_hash_out.pack(fill="x")
        GlowButton(obody, "  COPY  ", self._hash_copy,
                   width=100, height=30, bg_col=PANEL2, text_col=FG).pack(anchor="e", pady=(8, 0))

        self.hash_status = StatusBar(inner)
        self.hash_status.pack(fill="x")

    def _show_hash(self, h):
        self.txt_hash_out.configure(state="normal")
        self.txt_hash_out.delete("1.0","end")
        self.txt_hash_out.insert("end", h)
        self.txt_hash_out.configure(state="disabled")
        self.hash_status.ok("Hash computed")

    def _hash_sha256(self):
        t = self.txt_hash_in.get("1.0","end").strip()
        if not t: return messagebox.showwarning("Empty","Please enter text.")
        self._show_hash(hash_sha256(t))

    def _hash_md5(self):
        t = self.txt_hash_in.get("1.0","end").strip()
        if not t: return messagebox.showwarning("Empty","Please enter text.")
        self._show_hash(hash_md5(t))

    def _hash_copy(self):
        h = self.txt_hash_out.get("1.0","end").strip()
        if h:
            copy_to_clipboard(self.root, h)
            self.hash_status.ok("Copied to clipboard!")

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB 4  –  CLASSICAL CIPHERS
    # ═══════════════════════════════════════════════════════════════════════

    def _build_ciphers_tab(self, tab):
        self._tab_header(tab, "◇", "Classical Ciphers",
                         "Caesar  &  Vigenère  —  historical substitution ciphers")

        inner = tk.Frame(tab, bg=BG)
        inner.pack(fill="both", expand=True, padx=36)

        # Cipher selector
        sc = SectionCard(inner, title="Cipher Type", accent=ACCENT)
        sc.pack(fill="x", pady=(0, 14))
        sbody = tk.Frame(sc, bg=PANEL)
        sbody.pack(fill="x", padx=16, pady=(8, 16))

        self.cipher_var = tk.StringVar(value="Caesar")
        for val, lbl in (("Caesar","Caesar Cipher  (shift)"),
                         ("Vigenere","Vigenère Cipher  (keyword)")):
            rb = tk.Radiobutton(sbody, text=lbl, variable=self.cipher_var,
                                value=val, bg=PANEL, fg=FG, selectcolor=ACCENT,
                                activebackground=PANEL, activeforeground=FG,
                                font=FONT_LABEL, command=self._cipher_toggle,
                                indicatoron=1)
            rb.pack(side="left", padx=(0,24))

        # Input card
        ic = SectionCard(inner, title="Input Text", accent=ACCENT2)
        ic.pack(fill="x", pady=(0, 14))
        ibody = tk.Frame(ic, bg=PANEL)
        ibody.pack(fill="x", padx=16, pady=(8, 16))
        self.txt_cipher_in = tk.Text(ibody, bg=ENTRY_BG, fg=FG, font=FONT_ENTRY,
                                     height=4, relief="flat",
                                     insertbackground=CYAN, padx=8, pady=6)
        self.txt_cipher_in.pack(fill="x")

        # Key
        kc = SectionCard(inner, title="Key", accent=CYAN)
        kc.pack(fill="x", pady=(0, 14))
        kbody = tk.Frame(kc, bg=PANEL)
        kbody.pack(fill="x", padx=16, pady=(8, 16))
        self.lbl_key = tk.Label(kbody, text="Shift (integer):", bg=PANEL,
                                fg=FG2, font=FONT_SMALL)
        self.lbl_key.pack(side="left", padx=(0, 10))
        self.cipher_key = CyberEntry(kbody, width=22)
        self.cipher_key.pack(side="left")

        # Buttons
        acf = tk.Frame(inner, bg=BG)
        acf.pack(fill="x", pady=(0, 14))
        GlowButton(acf, "  🔒  ENCRYPT  ", self._cipher_encrypt,
                   width=160, height=38, bg_col=ACCENT).pack(side="left", padx=(0,12))
        GlowButton(acf, "  🔓  DECRYPT  ", self._cipher_decrypt,
                   width=160, height=38, bg_col="#3a3d6b", text_col=CYAN).pack(side="left")

        # Output card
        oc = SectionCard(inner, title="Output Text", accent=ACCENT)
        oc.pack(fill="x", pady=(0, 14))
        obody = tk.Frame(oc, bg=PANEL)
        obody.pack(fill="x", padx=16, pady=(8, 16))
        self.txt_cipher_out = tk.Text(obody, bg=ENTRY_BG, fg=CYAN, font=FONT_ENTRY,
                                      height=4, relief="flat",
                                      insertbackground=CYAN, padx=8, pady=6)
        self.txt_cipher_out.pack(fill="x")

        self.cipher_status = StatusBar(inner)
        self.cipher_status.pack(fill="x")

    def _cipher_toggle(self):
        t = "Shift (integer):" if self.cipher_var.get() == "Caesar" else "Keyword (letters):"
        self.lbl_key.configure(text=t)

    def _get_cipher_io(self):
        text = self.txt_cipher_in.get("1.0","end").strip()
        key  = self.cipher_key.get().strip()
        if not text: messagebox.showwarning("Empty","Enter input text."); return None,None
        if not key:  messagebox.showwarning("Empty","Enter a key/shift."); return None,None
        return text, key

    def _log_cipher_history(self, action, cipher_type, key, input_text, output_text):
        """Logs cipher operations to a text file for educational demonstration."""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = (
                f"[{timestamp}] {action} | {cipher_type} Cipher\n"
                f"Key/Shift: {key}\n"
                f"Input:  {input_text}\n"
                f"Output: {output_text}\n"
                f"{'-'*50}\n"
            )
            with open("cipher_history.txt", "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            pass

    def _cipher_encrypt(self):
        text, key = self._get_cipher_io()
        if not text: return
        if self.cipher_var.get() == "Caesar":
            try: r = caesar_encrypt(text, int(key))
            except ValueError: return messagebox.showerror("Error","Shift must be integer.")
        else:
            r = vigenere_encrypt(text, key)
        self.txt_cipher_out.delete("1.0","end")
        self.txt_cipher_out.insert("end", r)
        self.cipher_status.ok("Encryption complete")
        self._log_cipher_history("ENCRYPT", self.cipher_var.get(), key, text, r)

    def _cipher_decrypt(self):
        text, key = self._get_cipher_io()
        if not text: return
        if self.cipher_var.get() == "Caesar":
            try: r = caesar_decrypt(text, int(key))
            except ValueError: return messagebox.showerror("Error","Shift must be integer.")
        else:
            r = vigenere_decrypt(text, key)
        self.txt_cipher_out.delete("1.0","end")
        self.txt_cipher_out.insert("end", r)
        self.cipher_status.ok("Decryption complete")
        self._log_cipher_history("DECRYPT", self.cipher_var.get(), key, text, r)

    # ═══════════════════════════════════════════════════════════════════════
    #  TAB 5  –  ABOUT
    # ═══════════════════════════════════════════════════════════════════════

    def _build_about_tab(self, tab):
        self._tab_header(tab, "◎", "About CipherShield",
                         "An information-security educational toolkit")

        inner = tk.Frame(tab, bg=BG)
        inner.pack(fill="both", expand=True, padx=36)

        cards = [
            (ACCENT,  "⬡", "Symmetric Encryption",
             "AES-256 via Fernet. Keys are derived per-session from your\n"
             "password using PBKDF2HMAC + SHA-256 + 390,000 iterations."),
            (ACCENT2, "◈", "Zero Data Loss Proof",
             "Encrypt a file and immediately decrypt it. Compare SHA-256\n"
             "hashes byte-for-byte to prove AES is 100 % lossless."),
            (CYAN,    "⬢", "Cryptographic Hashing",
             "SHA-256 (256-bit, collision-resistant) and MD5 (128-bit,\n"
             "legacy). Hash any text to verify integrity."),
            (SUCCESS, "◇", "Classical Ciphers",
             "Caesar (monoalphabetic shift) and Vigenère (polyalphabetic\n"
             "keyword) — the historical foundations of modern cryptography."),
        ]

        grid = tk.Frame(inner, bg=BG)
        grid.pack(fill="x", pady=(0, 20))
        for i, (col, icon, title, body) in enumerate(cards):
            card = tk.Frame(grid, bg=PANEL,
                            highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=i//2, column=i%2, padx=8, pady=8, sticky="nsew")
            grid.columnconfigure(i%2, weight=1)
            tk.Label(card, text=icon, bg=PANEL, fg=col,
                     font=("Courier", 22, "bold"), pady=12, padx=16).pack(anchor="w")
            tk.Label(card, text=title, bg=PANEL, fg=FG,
                     font=FONT_HEAD, padx=16).pack(anchor="w")
            tk.Label(card, text=body, bg=PANEL, fg=FG2,
                     font=FONT_SMALL, padx=16, pady=8, justify="left",
                     wraplength=320).pack(anchor="w")

        # Footer
        foot = tk.Frame(inner, bg=PANEL2,
                        highlightbackground=BORDER, highlightthickness=1)
        foot.pack(fill="x", pady=(8, 0))
        tk.Label(foot, text="CipherShield  v2.0  —  Information Security Project  |  "
                            "Built with Python + Tkinter  |  AES-256 · SHA-256 · PBKDF2HMAC",
                 bg=PANEL2, fg=FG2, font=FONT_SMALL, pady=12).pack()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    root = tk.Tk()
    app = CipherShieldApp(root)
    root.mainloop()










    