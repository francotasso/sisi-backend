from io import BytesIO
from uuid import uuid4

import cloudinary
import cloudinary.uploader
from fastapi import UploadFile

from app.core.config import get_settings

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}

settings = get_settings()

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


class CloudinaryService:
    async def upload(self, file: UploadFile, folder: str = "products") -> str:
        content_type = file.content_type or "application/octet-stream"
        if content_type not in ALLOWED_CONTENT_TYPES:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Invalid image type: {content_type}. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
            )

        contents = await file.read()
        if len(contents) > settings.MAX_IMAGE_SIZE:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Image too large. Max size: {settings.MAX_IMAGE_SIZE // (1024 * 1024)}MB",
            )

        public_id = f"{folder}/{uuid4().hex}"

        result = cloudinary.uploader.upload(
            BytesIO(contents),
            public_id=public_id,
            overwrite=False,
            resource_type="image",
            quality="auto",
            fetch_format="auto",
        )

        return str(result["secure_url"])

    def extract_public_id(self, url: str) -> str | None:
        if "cloudinary" not in url:
            return None
        try:
            parts = url.split("/")
            idx = parts.index("upload")
            return "/".join(parts[idx + 2:]).rsplit(".", 1)[0]
        except (ValueError, IndexError):
            return None

    def delete(self, url: str) -> None:
        public_id = self.extract_public_id(url)
        if public_id:
            cloudinary.uploader.destroy(public_id)


cloudinary_service = CloudinaryService()
