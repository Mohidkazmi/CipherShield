"""
utils.py - Utility Functions Module
=====================================
CipherShield | Information Security Project

This module contains helper functions used across the project:
- Password strength checker
- Clipboard operations
- File path formatting helpers
"""

import re
import tkinter as tk


# ─── Password Strength Checker ────────────────────────────────────────────────

def check_password_strength(password: str) -> dict:
    """
    Analyzes password strength and returns a detailed report.

    A strong password should have:
    - At least 12 characters (length matters most)
    - Uppercase letters (A-Z)
    - Lowercase letters (a-z)
    - Digits (0-9)
    - Special symbols (!@#$%^&*)

    Args:
        password: The password string to analyze.

    Returns:
        A dictionary with:
        - 'score': 0-5 (number of criteria met)
        - 'strength': "Very Weak" / "Weak" / "Medium" / "Strong" / "Very Strong"
        - 'color': Color for the strength label (for the GUI)
        - 'checks': Dict of individual criteria results (True/False)
        - 'tips': List of improvement suggestions
    """
    if not password:
        return {
            'score': 0,
            'strength': 'No Password',
            'color': '#888888',
            'checks': {},
            'tips': ['Enter a password to check its strength.']
        }

    # Individual check results
    checks = {
        'length_8':     len(password) >= 8,
        'length_12':    len(password) >= 12,
        'uppercase':    bool(re.search(r'[A-Z]', password)),
        'lowercase':    bool(re.search(r'[a-z]', password)),
        'digits':       bool(re.search(r'\d', password)),
        'symbols':      bool(re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password)),
    }

    # Calculate score (0-5)
    score = sum([
        checks['length_8'],
        checks['length_12'],
        checks['uppercase'] and checks['lowercase'],
        checks['digits'],
        checks['symbols'],
    ])

    # Map score to strength label
    strength_map = {
        0: ('Very Weak',   '#FF3B3B'),
        1: ('Weak',        '#FF6B35'),
        2: ('Fair',        '#FFB300'),
        3: ('Medium',      '#7BC67E'),
        4: ('Strong',      '#4CAF50'),
        5: ('Very Strong', '#00C853'),
    }
    strength, color = strength_map.get(score, ('Very Weak', '#FF3B3B'))

    # Build improvement tips
    tips = []
    if not checks['length_8']:
        tips.append('• Use at least 8 characters.')
    if not checks['length_12']:
        tips.append('• Use 12+ characters for a stronger password.')
    if not checks['uppercase']:
        tips.append('• Add uppercase letters (A-Z).')
    if not checks['lowercase']:
        tips.append('• Add lowercase letters (a-z).')
    if not checks['digits']:
        tips.append('• Include numbers (0-9).')
    if not checks['symbols']:
        tips.append('• Add symbols like !@#$%^&*.')
    if not tips:
        tips.append('✓ Excellent password! All criteria met.')

    return {
        'score': score,
        'strength': strength,
        'color': color,
        'checks': checks,
        'tips': tips,
    }


# ─── Clipboard Utility ────────────────────────────────────────────────────────

def copy_to_clipboard(root: tk.Tk, text: str) -> bool:
    """
    Copies text to the system clipboard using Tkinter.

    Args:
        root: The Tkinter root window (needed to access clipboard).
        text: The text to copy.

    Returns:
        True if successful, False otherwise.
    """
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()  # Flush clipboard operation
        return True
    except Exception:
        return False


# ─── File Path Helpers ────────────────────────────────────────────────────────

def shorten_path(path: str, max_length: int = 55) -> str:
    """
    Shortens a long file path for display in the GUI.

    Example: /Users/mohid/.../very_long_folder/file.txt → ...very_long_folder/file.txt

    Args:
        path: The full file path string.
        max_length: Maximum characters to display.

    Returns:
        A shortened path string suitable for GUI labels.
    """
    if not path:
        return "No file selected"
    if len(path) <= max_length:
        return path
    return "..." + path[-(max_length - 3):]


def get_file_size_str(file_path: str) -> str:
    """
    Returns human-readable file size (e.g., "2.5 KB", "1.2 MB").

    Args:
        file_path: Path to the file.

    Returns:
        Human-readable file size string.
    """
    import os
    try:
        size = os.path.getsize(file_path)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 ** 2:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 ** 3:
            return f"{size / (1024 ** 2):.1f} MB"
        else:
            return f"{size / (1024 ** 3):.1f} GB"
    except Exception:
        return "Unknown size"
