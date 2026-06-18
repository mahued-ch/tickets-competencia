from pathlib import Path
import hashlib
from app.core.config import get_settings

settings = get_settings()


class LocalStorageService:
    def __init__(self):
        self.root = Path(settings.storage_root)
        self.root.mkdir(parents=True, exist_ok=True)

    def save_ticket_file(self, ticket_id: int, original_name: str, content: bytes) -> dict:
        suffix = Path(original_name).suffix.lower()
        folder = self.root / str(ticket_id)
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / original_name
        # avoid collision in starter
        counter = 1
        while target.exists():
            target = folder / f"{Path(original_name).stem}_{counter}{suffix}"
            counter += 1
        target.write_bytes(content)
        file_hash = hashlib.sha256(content).hexdigest()
        return {
            "file_name": target.name,
            "extension": suffix.replace('.', ''),
            "mime_type": _mime_from_ext(suffix),
            "size": len(content),
            "path": str(target.resolve()),
            "provider": "LOCAL",
            "hash": file_hash,
        }

    def open_read(self, path: str) -> bytes:
        return Path(path).read_bytes()


def _mime_from_ext(suffix: str) -> str:
    suffix = suffix.lower()
    if suffix == '.pdf':
        return 'application/pdf'
    if suffix in {'.jpg', '.jpeg'}:
        return 'image/jpeg'
    if suffix == '.png':
        return 'image/png'
    return 'application/octet-stream'
