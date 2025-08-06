# Imported packages
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Native packages
from datetime import datetime

# Local packages
from app.settings import Settings
from app.routers.documents import router


app = FastAPI(
    title="Auto-bot's FastAPIs",
    version=Settings.APP_VERSION,
    docs_url="/docs"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # TODO: Create a list with all allowed origins for better security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)


@app.get("/")
def root():
    return {
        "api_name": "Auto-bots API server",
        "contributors": "Edu viadinho, Becker, Gui da Gaita",
        "license_copyrights": "all rights reserved, 06/2025",
        "version": Settings.APP_VERSION,
        "status": "online",
        "environment": "production",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "GET /": "Core program info (this endpoint)",
            "GET /documents": "Core documents functionalities and endpoints",
        }
    }