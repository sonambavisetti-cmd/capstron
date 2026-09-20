import os
from typing import Optional

class LocalStorage:
    def __init__(self, base_path: Optional[str]=None):
        self.base_path = base_path or os.path.join(os.getcwd(), 'storage')
        os.makedirs(self.base_path, exist_ok=True)

    def save(self, filename: str, data: bytes) -> str:
        path = os.path.join(self.base_path, filename)
        with open(path, 'wb') as f:
            f.write(data)
        return path

    def get_signed_url(self, path: str, expires: int = 3600) -> str:
        # Return a file:// style path for local dev
        return f'file://{path}'
