"""
BOLT ⚡ — Key Generator
Run: python gen_key.py
"""
from cryptography.fernet import Fernet
key = Fernet.generate_key().decode()
print("=" * 50)
print("⚡ BOLT — Encryption Key Generator")
print("=" * 50)
print(f"\n🔑 Your Key:\n{key}\n")
print("📋 Paste this in Railway as ENCRYPTION_KEY")
print("⚠️  SAVE THIS KEY! If lost, all tokens are lost forever!")
print("=" * 50)
