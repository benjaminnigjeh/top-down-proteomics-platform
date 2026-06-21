from fastapi import APIRouter, Depends, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.upload import Upload
from app.schemas.upload import UploadRead
from app.utils.file_utils import validate_extension, determine_file_type, save_upload
from app.config import settings

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", response_model=UploadRead, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile, db: Session = Depends(get_db)):
    try:
        ext = validate_extension(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    content = await file.read()
    size = len(content)
    if size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit")
    if size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    stored, md5 = save_upload(content, file.filename, settings.UPLOAD_DIR)

    upload = Upload(
        original_filename=file.filename,
        stored_filename=stored,
        file_type=determine_file_type(file.filename),
        size_bytes=size,
        checksum_md5=md5,
    )
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


@router.get("/{upload_id}", response_model=UploadRead)
def get_upload(upload_id: str, db: Session = Depends(get_db)):
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    return upload


@router.delete("/{upload_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_upload(upload_id: str, db: Session = Depends(get_db)):
    upload = db.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")
    path = settings.UPLOAD_DIR / upload.stored_filename
    if path.exists():
        path.unlink()
    db.delete(upload)
    db.commit()
