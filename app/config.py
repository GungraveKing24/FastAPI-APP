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

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
