from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

class EncryptionManager:
    def __init__(self, is_server=False, private_key=None, public_key=None):
        if is_server:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
        else:
            self.private_key = None
            self.public_key = public_key

    def get_serialized_public_key(self) -> bytes:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def load_public_key(self, public_key_bytes: bytes):
        self.public_key = serialization.load_pem_public_key(
            public_key_bytes, backend=default_backend()
        )

    def encrypt(self, message: str) -> bytes:
        return self.public_key.encrypt(
            message.encode('utf-8'),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def decrypt(self, ciphertext: bytes) -> str:
        if self.private_key is None:
            raise ValueError("Private key not loaded (only server has private key)")
        plaintext = self.private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext.decode('utf-8')