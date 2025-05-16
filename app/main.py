from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from urllib.parse import urlencode
from config import secret_key, Base, engine

from routes import auth, categories, arrangements, orders, users, stats, coments, webhooks, orders_details

#Prod mode
#app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

#dev mode
app = FastAPI()

Base.metadata.create_all(bind=engine)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://reactpage-production.up.railway.app",
        "https://arreglitosv.up.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=secret_key)

app.include_router(auth.router, tags=["Authentication"])
app.include_router(categories.router, tags=["Categorias"])
app.include_router(arrangements.router, tags=["Arreglos"])
app.include_router(stats.router, tags=["Estadísticas"])
app.include_router(users.router, tags=["Usuarios"])
app.include_router(coments.router, tags=["Comentarios"])
app.include_router(webhooks.router, tags=["Webhooks"])
app.include_router(orders.router, tags=["Pedidos"])
app.include_router(orders_details.router, tags=["Detalles de Pedidos"])