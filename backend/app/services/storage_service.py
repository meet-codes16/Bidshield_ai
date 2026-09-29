from pathlib import Path
from app.core.config import settings

class StorageProvider:
    def put(self, key: str, content: bytes) -> str: raise NotImplementedError
    def get(self, key: str) -> bytes: raise NotImplementedError

class LocalStorageProvider(StorageProvider):
    def __init__(self):
        self.root=Path("data/object_store"); self.root.mkdir(parents=True, exist_ok=True)
    def put(self,key,content):
        p=self.root/key; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(content); return str(p)
    def get(self,key): return (self.root/key).read_bytes()

storage_provider=LocalStorageProvider()
