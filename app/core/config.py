import os
import logging

from fastapi import FastAPI
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Processamento de Mensagens N8N + WhatsApp",
    description="API para processar mensagens do N8N e gerar documentos DOCX para WhatsApp",
    version="2.0.1",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS para permitir acesso do N8N
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique as origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def logger_init():
    port = int(os.environ.get("PORT", 8000))
    logger.info("🚀 Iniciando servidor FastAPI para N8N + WhatsApp (Cloud Version)...")
    logger.info(f"🌐 Porta: {port}")
    logger.info(f"📅 Data atual: {datetime.now().strftime('%d/%m/%Y')}")
    logger.info(f"🕐 Hora atual: {datetime.now().strftime('%H:%M:%S')}")
    
    return port