from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from urllib.parse import urlencode
from config import secret_key

from routes import auth, categories, arrangements, orders

#Prod mode
#app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

#dev mode
app = FastAPI()

origins = ["http://localhost:5173, https://reactpage-production.up.railway.app"]

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # puedes usar ["*"] temporalmente para pruebas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=secret_key)

app.include_router(auth.router, tags=["Authentication"])
app.include_router(categories.router, tags=["Categorias"])
app.include_router(arrangements.router, tags=["Arreglos"])
app.include_router(orders.router)