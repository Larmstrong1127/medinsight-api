import pytest
from cryptography.fernet import Fernet

from app.core.security import decrypt_content, encrypt_content


@pytest.fixture(autouse=True)
def set_encryption_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", key)
    # Clear lru_cache so settings picks up the new env var
    from app import config
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def test_encrypt_decrypt_roundtrip():
    plaintext = "This is a sensitive clinical note."
    ciphertext = encrypt_content(plaintext)
    assert ciphertext != plaintext
    assert decrypt_content(ciphertext) == plaintext


def test_encrypted_content_differs_each_call():
    plaintext = "Same content"
    # Fernet uses a random IV — same plaintext should produce different ciphertext
    assert encrypt_content(plaintext) != encrypt_content(plaintext)


def test_decrypt_wrong_key_raises(monkeypatch):
    plaintext = "secret"
    ciphertext = encrypt_content(plaintext)

    # Switch to a different key
    new_key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", new_key)
    from app import config
    config.get_settings.cache_clear()

    with pytest.raises(ValueError, match="decryption failed"):
        decrypt_content(ciphertext)
