from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Configuración de la aplicación
app = FastAPI()

# Configuración de CORS
origins = [
    "https://reactpage-production.up.railway.app",
    "http://localhost:0000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Configuración de la base de datos PostgreSQL en Railway
DATABASE_URL = "postgresql://postgres:bJcwTJJSsDMPXdkZhmyRFrdUqrjobynA@junction.proxy.rlwy.net:51337/railway"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de la base de datos
class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    juego = Column(String(255), nullable=False)
    estado = Column(String(255), nullable=False)
    runN = Column(Integer, nullable=False)
    rejugando = Column(String(255), nullable=False)
    DatosAdicionales = Column(String(255), nullable=False)
    Calificacion = Column(Float, nullable=False)
    img = Column(String(255), nullable=True)
    fecha_finalizado = Column(Date, nullable=True)

# Crear las tablas en la base de datos (solo para desarrollo, en producción usa migraciones)
Base.metadata.create_all(bind=engine)

# Dependencia para la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint para obtener los juegos
@app.get("/games")
def get_games(db: Session = Depends(get_db)):
    games = db.query(Game).all()
    return games
