import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import math

from encrypt import encrypt_file, decrypt_file
from hashing import hash_sha256, hash_md5, hash_file_sha256
from ciphers import caesar_encrypt, caesar_decrypt, vigenere_encrypt, vigenere_decrypt
from utils import check_password_strength, copy_to_clipboard, shorten_path, get_file_size_str

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
    #  TAB 1  –  FILE ENCRYPTION
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

        # ── Password card ──
        pc = SectionCard(inner, title="Password", accent=ACCENT2)
        pc.pack(fill="x", pady=(0, 14))
        pbody = tk.Frame(pc, bg=PANEL)
        pbody.pack(fill="x", padx=16, pady=(8, 6))

        tk.Label(pbody, text="Enter password:", bg=PANEL, fg=FG2, font=FONT_SMALL).pack(anchor="w")
        self.entry_enc_pwd = CyberEntry(pbody, show="●", width=50)
        self.entry_enc_pwd.pack(fill="x", pady=(4, 8))
        self.entry_enc_pwd.bind("<KeyRelease>", self._enc_pwd_strength)

        # Strength bar
        sb_frame = tk.Frame(pbody, bg=PANEL)
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
        pwd = self.entry_enc_pwd.get()
        if not pwd:
            return messagebox.showwarning("No password", "Please enter a password.")
        self.enc_status.info("Encrypting… please wait")
        def task():
            ok, msg = encrypt_file(self.enc_file, pwd)
            self.root.after(0, self._enc_done, ok, msg, "encrypt")
        threading.Thread(target=task, daemon=True).start()

    def _enc_action_decrypt(self):
        if not self.enc_file:
            return messagebox.showwarning("No file", "Please select a file first.")
        pwd = self.entry_enc_pwd.get()
        if not pwd:
            return messagebox.showwarning("No password", "Please enter a password.")
        self.enc_status.info("Decrypting… please wait")
        def task():
            ok, msg = decrypt_file(self.enc_file, pwd)
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