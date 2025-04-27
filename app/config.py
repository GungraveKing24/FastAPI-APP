import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

#Base de datos
DATABASE_URL = os.getenv("database_url")

#Google
CLIENT_ID = os.environ.get("CLIENT_ID", None)
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", None)
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", None)
CYPHER_SECURE_KEY = os.environ.get("CYPHER_SECURE_KEY", None)

#URL
F_URL = os.environ.get("FRONTEND_URL", None)

#Session general
secret_key = os.environ.get("secret_key", None)

# Cloudinary config
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", None)
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", None)
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", None)

# Wompi config
WOMPI_PUBLIC_KEY = os.environ.get("WOMPI_PUBLIC_KEY", None)
WOMPI_PRIVATE_KEY = os.environ.get("WOMPI_PRIVATE_KEY", None)
WOMPI_URL = os.environ.get("WOMPI_URL", None)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
