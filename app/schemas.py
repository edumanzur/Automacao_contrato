from pydantic import BaseModel
from enum import Enum

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


class TestPlaceHolder(BaseModel):
    name: str
    price: str
    email: str
    cpf: str
    cellphone: str


# TODO: create enum of possible .docx name ("templates(testing)", "contract", "finance"...)
class DocxNames(Enum):
    TEMPLATE = "template.docx"
    MODELO = "modelo.docx"