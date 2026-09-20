class S3Storage:
    def __init__(self, bucket: str):
        self.bucket = bucket

    def save(self, filename: str, data: bytes) -> str:
        raise NotImplementedError('S3 adapter not implemented in this MVP')

    def get_signed_url(self, path: str, expires: int = 3600) -> str:
        raise NotImplementedError('S3 adapter not implemented in this MVP')
