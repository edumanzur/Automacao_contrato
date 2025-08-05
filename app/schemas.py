from pydantic import BaseModel

class MensagemRequest(BaseModel):
    mensagem: str
    webhook_id: str | None = None
    origem: str | None = "n8n"
    formato_resposta: str | None = "binary"  # binary, base64, json

class MensagemResponse(BaseModel):
    sucesso: bool
    mensagem: str
    dados_extraidos: dict
    arquivo_gerado: str | None = None

class DocumentoResponse(BaseModel):
    success: bool
    message: str
    filename: str
    file_size: int
    mime_type: str
    base64_content: str | None = None
    download_url: str | None = None
    dados_extraidos: dict
    timestamp: str