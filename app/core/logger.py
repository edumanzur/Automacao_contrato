# Local packages
import os
import logging
from datetime import datetime
from ..settings import Settings

#TODO: full debug logger for view in terminal
# TODO: create logger.py in core/
# add all enums for process status ("processing", "on-going", "awaiting for user"...)

def logger_init():
    port = Settings.PORT
    logger.info("🚀 Iniciando servidor FastAPI para N8N + WhatsApp (Cloud Version)...")
    logger.info(f"🌐 Porta: {port}")
    logger.info(f"📅 Data atual: {datetime.now().strftime('%d/%m/%Y')}")
    logger.info(f"🕐 Hora atual: {datetime.now().strftime('%H:%M:%S')}")
    
    return port


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)