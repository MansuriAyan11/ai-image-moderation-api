from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import shutil
import uuid
import os

from detector import detect_image


app = FastAPI(
    title="AI Image Moderation API",
    description="API for detecting nudity/inappropriate content in uploaded images",
    version="1.0.0"
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}


@app.get("/")
def home():
    return {
        "success": True,
        "message": "Nudity Detection API is running",
        "docs": "/docs"
    }


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    file_path = None

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file uploaded"
        )

    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Invalid file extension. Only jpg, jpeg, png, and webp are allowed."
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a valid image file."
        )

    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if os.path.getsize(file_path) == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )

        result = detect_image(str(file_path))

        if result["status"] == "safe":
            return {
                "success": True,
                "message": "Image is safe",
                "data": result
            }

        if result["status"] == "unsafe":
            return {
                "success": True,
                "message": "Inappropriate content detected",
                "data": result
            }

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Image detection failed",
                "data": result
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

    finally:
        await file.close()

        if file_path is not None and file_path.exists():
            try:
                file_path.unlink()
                print(f"Deleted temporary file: {file_path}")
            except Exception as cleanup_error:
                print(f"Failed to delete temporary file: {cleanup_error}")