from config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
from cloudinary.utils import cloudinary_url
import cloudinary.uploader, cloudinary

# Configuration       
cloudinary.config( 
    cloud_name = CLOUDINARY_CLOUD_NAME, 
    api_key = CLOUDINARY_API_KEY, 
    api_secret = CLOUDINARY_API_SECRET, # Click 'View API Keys' above to copy your API secret
    secure=True
)

async def upload_file(file):
    try:
        file.seek(0)  # Asegura que estás leyendo desde el inicio
        file_contents = await file.read()
        upload_result = cloudinary.uploader.upload(
            file_contents,
            resource_type="auto"
        )
        if upload_result:
            return upload_result.get("secure_url")  # Usa HTTPS mejor
        else:
            return None
    except Exception as e:
        print(f"Cloudinary upload error: {str(e)}")
        return None
    finally:
        await file.seek(0)  # Asegura que estás leyendo desde el inicio