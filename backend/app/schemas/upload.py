from datetime import datetime
from pydantic import BaseModel


class UploadRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    original_filename: str
    file_type: str
    size_bytes: int
    checksum_md5: str
    created_at: datetime
