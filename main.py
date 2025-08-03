from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import os
import io # Usado para criar o arquivo em memória
import re
from datetime import datetime
from typing import Optional
import logging

# Importações para gerar PDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Processamento de Mensagens N8N",
    description="API para processar mensagens do N8N e gerar documentos PDF",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS para permitir acesso do N8N
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class MensagemRequest(BaseModel):
    mensagem: str
    webhook_id: Optional[str] = None
    origem: Optional[str] = "n8n"

# --- Funções de Extração de Dados (sem alteração) ---
def extrair_dados_da_mensagem(mensagem: str) -> dict:
    """Extrai os dados da mensagem com a estrutura especificada"""
    dados = {}
    padroes = {
        "NOME": [r"Nome:\s*(.+?)(?=\n|$)", r"nome:\s*(.+?)(?=\n|$)"],
        "EMAIL": [r"Email:\s*(.+?)(?=\n|$)", r"email:\s*(.+?)(?=\n|$)", r"E-mail:\s*(.+?)(?=\n|$)"],
        "CPF": [r"CPF:\s*(.+?)(?=\n|$)", r"cpf:\s*(.+?)(?=\n|$)"],
        "ENDERECO": [r"Endereço:\s*(.+?)(?=\n|$)", r"endereco:\s*(.+?)(?=\n|$)", r"Endereco:\s*(.+?)(?=\n|$)"],
        "CEP": [r"CEP:\s*(.+?)(?=\n|$)", r"cep:\s*(.+?)(?=\n|$)"],
        "TELEFONE": [r"Telefone:\s*(.+?)(?=\n|$)", r"telefone:\s*(.+?)(?=\n|$)", r"Fone:\s*(.+?)(?=\n|$)"],
        "VALOR": [r"Valor:\s*(.+?)(?=\n|$)", r"valor:\s*(.+?)(?=\n|$)"],
        "PARCELAS": [r"Quantidade de Parcelas:\s*(.+?)(?=\n|$)", r"quantidade de parcelas:\s*(.+?)(?=\n|$)"],
        "FORMA_PAGAMENTO": [r"Forma de pagamento:\s*(.+?)(?=\n|$)", r"forma de pagamento:\s*(.+?)(?=\n|$)"]
    }
    for campo, padroes_campo in padroes.items():
        valor_encontrado = None
        for padrao in padroes_campo:
            match = re.search(padrao, mensagem, re.IGNORECASE | re.MULTILINE)
            if match:
                valor_encontrado = match.group(1).strip()
                break
        dados[campo] = valor_encontrado if valor_encontrado else "Não informado"
    
    agora = datetime.now()
    dados["DATA"] = agora.strftime("%d/%m/%Y")
    dados["HORA"] = agora.strftime("%H:%M:%S")
    dados["DATA_HORA"] = agora.strftime("%d/%m/%Y %H:%M:%S")
    return dados

# --- NOVA FUNÇÃO PARA GERAR PDF ---
def criar_documento_pdf(dados: dict, buffer: io.BytesIO):
    """Cria um documento PDF simples com os dados extraídos e o salva no buffer."""
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter  # Tamanho da página

    # Posição inicial
    x = 1 * inch
    y = height - 1 * inch
    line_height = 20  # Espaçamento entre linhas

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "Relatório de Dados do Cliente")
    y -= line_height * 2

    # Função auxiliar para desenhar uma linha de texto
    def draw_line(label, value):
        nonlocal y
        if y < 1 * inch: # Se chegar ao final da página, cria uma nova
            c.showPage()
            c.setFont("Helvetica-Bold", 12)
            y = height - 1 * inch
        c.setFont("Helvetica-Bold", 12)
        c.drawString(x, y, f"{label}:")
        c.setFont("Helvetica", 12)
        c.drawString(x + 1.5 * inch, y, str(dados.get(value, "Não informado")))
        y -= line_height

    # Escrevendo os dados no PDF
    draw_line("Processado em", "DATA_HORA")
    y -= line_height # Espaço extra

    draw_line("Nome", "NOME")
    draw_line("Email", "EMAIL")
    draw_line("CPF", "CPF")
    draw_line("Telefone", "TELEFONE")
    y -= line_height

    draw_line("Endereço", "ENDERECO")
    draw_line("CEP", "CEP")
    y -= line_height

    draw_line("Valor", "VALOR")
    draw_line("Parcelas", "PARCELAS")
    draw_line("Forma de Pagamento", "FORMA_PAGAMENTO")

    # Finaliza e salva o PDF
    c.save()
    logger.info("PDF gerado em memória com sucesso.")


@app.get("/")
async def root():
    return {"message": "API de Geração de Documentos - Agora gera PDF!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# --- ENDPOINT MODIFICADO PARA GERAR PDF ---
@app.post("/gerar-documento")
async def gerar_documento(request: MensagemRequest):
    """Endpoint para processar mensagem E gerar documento PDF"""
    logger.info("=== INICIANDO GERAÇÃO DE DOCUMENTO PDF ===")
    
    try:
        # 1. Extrair dados da mensagem
        dados_extraidos = extrair_dados_da_mensagem(request.mensagem)
        logger.info("Dados extraídos para o documento.")
        
        # 2. Definir nome do arquivo de saída
        nome_cliente = re.sub(r'[^\w\-_.]', '', dados_extraidos.get("NOME", "cliente").replace(" ", "_"))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"documento_{nome_cliente}_{timestamp}.pdf" # <-- Alterado para .pdf
        
        logger.info(f"Gerando documento: {output_filename}")

        # 3. Criar o PDF em um buffer de memória
        pdf_buffer = io.BytesIO()
        criar_documento_pdf(dados_extraidos, pdf_buffer)
        
        # Reposicionar o cursor do buffer para o início
        pdf_buffer.seek(0)
        pdf_content = pdf_buffer.read()
        pdf_buffer.close()

        # 4. Retornar a resposta com o conteúdo do PDF
        return Response(
            content=pdf_content,
            media_type="application/pdf", # <-- Alterado para PDF
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}",
                "Content-Length": str(len(pdf_content))
            }
        )
        
    except Exception as e:
        logger.error(f"ERRO CRÍTICO NA GERAÇÃO DO PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na geração do documento: {str(e)}")

# --- Outros endpoints (sem alteração) ---
@app.post("/webhook/processar")
async def webhook_processar(dados: dict):
    logger.info("Webhook recebido, processando dados...")
    # Esta é uma lógica de exemplo, adapte conforme necessário
    try:
        mensagem_texto = dados.get("mensagem") or dados.get("message") or dados.get("texto")
        if mensagem_texto:
            dados_extraidos = extrair_dados_da_mensagem(mensagem_texto)
            return {"status": "success", "dados_extraidos": dados_extraidos}
        return {"status": "error", "message": "Nenhum texto encontrado para processar"}
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
