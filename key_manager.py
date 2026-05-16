"""
key_manager.py - RSA Key Registry
====================================
Secure File Encryption System | Information Security Project

CONCEPT: Key Management Systems (KMS)
- In production, keys are stored in Hardware Security Modules (HSMs) or cloud KMS.
- For this project, we track key metadata in a local JSON registry file.
- The registry stores file paths and metadata, NOT the raw key material itself.
- This lets users manage multiple key pairs and select them by label.
"""

import os
import json
import datetime

REGISTRY_FILE = "keys_registry.json"


def _load_registry() -> list:
    """Loads and returns the key registry list from disk."""
    if not os.path.exists(REGISTRY_FILE):
        return []
    try:
        with open(REGISTRY_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_registry(registry: list) -> None:
    """Saves the key registry list to disk."""
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)


def list_keys() -> list:
    """Returns all registered key entries."""
    return _load_registry()


def add_key(label: str, priv_path: str, pub_path: str,
            algorithm: str = "RSA", bits: int = 2048) -> dict:
    """
    Registers a new key pair in the local registry.

    Args:
        label:     A human-readable name (e.g., "Project Key", "Alice's Key").
        priv_path: Absolute path to the private key PEM file.
        pub_path:  Absolute path to the public key PEM file.
        algorithm: Algorithm name, default "RSA".
        bits:      Key size in bits, default 2048.

    Returns:
        The new registry entry as a dict.
    """
    registry = _load_registry()

    # Generate a unique ID (max existing ID + 1)
    existing_ids = {k.get("id", 0) for k in registry}
    new_id = max(existing_ids, default=0) + 1

    entry = {
        "id":         new_id,
        "label":      label,
        "priv_path":  os.path.abspath(priv_path),
        "pub_path":   os.path.abspath(pub_path),
        "algorithm":  algorithm,
        "bits":       bits,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    registry.append(entry)
    _save_registry(registry)
    return entry


def delete_key(key_id: int) -> bool:
    """
    Removes a key entry from the registry by ID.
    Does NOT delete the actual PEM files from disk.

    Returns True if removed, False if ID not found.
    """
    registry = _load_registry()
    new_registry = [k for k in registry if k.get("id") != key_id]
    if len(new_registry) == len(registry):
        return False
    _save_registry(new_registry)
    return True


def get_key(key_id: int) -> dict | None:
    """Returns a specific key entry by ID, or None if not found."""
    for k in _load_registry():
        if k.get("id") == key_id:
            return k
    return None
