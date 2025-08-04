from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
import os
import tempfile
import shutil
import re
from docx import Document
from datetime import datetime
from typing import Optional
import logging
import base64
import mimetypes

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Processamento de Mensagens N8N + WhatsApp",
    description="API para processar mensagens do N8N e gerar documentos DOCX para WhatsApp",
    version="2.0.0",
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

# Modelos Pydantic
class MensagemRequest(BaseModel):
    mensagem: str
    webhook_id: Optional[str] = None
    origem: Optional[str] = "n8n"
    formato_resposta: Optional[str] = "binary"  # binary, base64, json

class MensagemResponse(BaseModel):
    sucesso: bool
    mensagem: str
    dados_extraidos: dict
    arquivo_gerado: Optional[str] = None

class DocumentoResponse(BaseModel):
    success: bool
    message: str
    filename: str
    file_size: int
    mime_type: str
    base64_content: Optional[str] = None
    download_url: Optional[str] = None
    dados_extraidos: dict
    timestamp: str

def substituir_em_runs_preservando_tudo(paragrafos, dados):
    """Substitui placeholders nos runs preservando formatação"""
    for paragrafo in paragrafos:
        texto_completo = ""
        for run in paragrafo.runs:
            texto_completo += run.text
        
        texto_modificado = texto_completo
        substituicoes_feitas = False
        
        for chave, valor in dados.items():
            placeholder = f'{{{{{chave}}}}}'
            if placeholder in texto_modificado:
                valor_str = str(valor) if valor is not None else ""
                texto_modificado = texto_modificado.replace(placeholder, valor_str)
                substituicoes_feitas = True
                logger.info(f"Substituído: {placeholder} -> {valor_str}")
        
        if substituicoes_feitas:
            for run in paragrafo.runs:
                run.text = ""
            
            if not paragrafo.runs:
                paragrafo.add_run()
            
            paragrafo.runs[0].text = texto_modificado

def preencher_modelo(caminho_modelo, caminho_saida, dados):
    """Preenche um modelo DOCX com os dados fornecidos"""
    try:
        logger.info(f"Abrindo modelo: {caminho_modelo}")
        doc = Document(caminho_modelo)
        
        dados_limpos = {}
        for chave, valor in dados.items():
            if valor is None or valor == "":
                dados_limpos[chave] = "Não informado"
            else:
                dados_limpos[chave] = str(valor)
        
        logger.info("Processando parágrafos principais...")
        substituir_em_runs_preservando_tudo(doc.paragraphs, dados_limpos)
        
        logger.info("Processando tabelas...")
        for tabela in doc.tables:
            for linha in tabela.rows:
                for celula in linha.cells:
                    substituir_em_runs_preservando_tudo(celula.paragraphs, dados_limpos)
        
        logger.info("Processando cabeçalhos e rodapés...")
        for section in doc.sections:
            if section.header:
                substituir_em_runs_preservando_tudo(section.header.paragraphs, dados_limpos)
            if section.footer:
                substituir_em_runs_preservando_tudo(section.footer.paragraphs, dados_limpos)
        
        logger.info(f"Salvando documento em: {caminho_saida}")
        doc.save(caminho_saida)
        logger.info("Arquivo gerado com sucesso!")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao preencher modelo: {str(e)}")
        raise Exception(f"Erro ao preencher modelo: {str(e)}")

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
        "PARCELAS": [
            r"Quantidade de Parcelas:\s*(.+?)(?=\n|$)", 
            r"quantidade de parcelas:\s*(.+?)(?=\n|$)",
            r"Parcelas:\s*(.+?)(?=\n|$)",
            r"parcelas:\s*(.+?)(?=\n|$)"
        ],
        "FORMA_PAGAMENTO": [
            r"Forma de pagamento:\s*(.+?)(?=\n|$)", 
            r"forma de pagamento:\s*(.+?)(?=\n|$)",
            r"Pagamento:\s*(.+?)(?=\n|$)",
            r"pagamento:\s*(.+?)(?=\n|$)"
        ]
    }
    
    for campo, padroes_campo in padroes.items():
        valor_encontrado = None
        for padrao in padroes_campo:
            match = re.search(padrao, mensagem, re.IGNORECASE | re.MULTILINE)
            if match:
                valor_encontrado = match.group(1).strip()
                break
        
        dados[campo] = valor_encontrado if valor_encontrado else "Não informado"
    
    # Adicionar campos de data/hora automaticamente
    agora = datetime.now()
    dados["DATA"] = agora.strftime("%d/%m/%Y")
    dados["HORA"] = agora.strftime("%H:%M:%S")
    dados["DATA_HORA"] = agora.strftime("%d/%m/%Y %H:%M:%S")
    dados["DATA_PROCESSAMENTO"] = agora.strftime("%d/%m/%Y %H:%M:%S")
    dados["TIMESTAMP"] = agora.isoformat()
    
    dados["PACIENTE"] = dados["NOME"]
    dados["ARQUIVO_FONTE"] = "API N8N Cloud"
    
    return dados

def criar_documento_fallback(dados: dict, output_path: str) -> None:
    """Cria um documento DOCX simples com os dados extraídos"""
    doc = Document()
    
    # Cabeçalho
    doc.add_heading('Dados do Cliente', 0)
    doc.add_paragraph(f'Processado em: {dados.get("DATA_HORA", "N/A")}')
    doc.add_paragraph('---')
    
    # Seção de informações pessoais
    doc.add_heading('Informações Pessoais', level=1)
    doc.add_paragraph(f'Nome: {dados.get("NOME", "Não informado")}')
    doc.add_paragraph(f'Email: {dados.get("EMAIL", "Não informado")}')
    doc.add_paragraph(f'CPF: {dados.get("CPF", "Não informado")}')
    doc.add_paragraph(f'Telefone: {dados.get("TELEFONE", "Não informado")}')
    
    # Seção de endereço
    doc.add_heading('Endereço', level=1)
    doc.add_paragraph(f'Endereço: {dados.get("ENDERECO", "Não informado")}')
    doc.add_paragraph(f'CEP: {dados.get("CEP", "Não informado")}')
    
    # Seção financeira
    doc.add_heading('Informações Financeiras', level=1)
    doc.add_paragraph(f'Valor: {dados.get("VALOR", "Não informado")}')
    doc.add_paragraph(f'Quantidade de Parcelas: {dados.get("PARCELAS", "Não informado")}')
    doc.add_paragraph(f'Forma de Pagamento: {dados.get("FORMA_PAGAMENTO", "Não informado")}')
    
    # Adicionar data/hora
    doc.add_heading('Informações do Processamento', level=1)
    doc.add_paragraph(f'Data: {dados.get("DATA", "N/A")}')
    doc.add_paragraph(f'Hora: {dados.get("HORA", "N/A")}')
    
    doc.save(output_path)

@app.get("/")
async def root():
    return {
        "message": "API Processamento de Mensagens N8N + WhatsApp - Cloud Version",
        "version": "2.0.0",
        "status": "online",
        "environment": "production",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "gerar_documento": "POST /gerar-documento (retorna binário)",
            "gerar_documento_base64": "POST /gerar-documento-base64 (retorna JSON com base64)",
            "gerar_documento_whatsapp": "POST /gerar-documento-whatsapp (otimizado para Z-API)",
            "webhook": "POST /webhook/processar",
            "health": "GET /health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check para o N8N verificar se a API está funcionando"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "processamento-mensagens-whatsapp-cloud",
        "environment": "production",
        "data_atual": datetime.now().strftime("%d/%m/%Y"),
        "hora_atual": datetime.now().strftime("%H:%M:%S")
    }

@app.post("/gerar-documento")
async def gerar_documento(request: MensagemRequest):
    """Endpoint para processar mensagem E gerar documento DOCX (retorna binário)"""
    logger.info("=== GERAÇÃO DE DOCUMENTO N8N CLOUD (BINÁRIO) ===")
    logger.info(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    temp_dir = tempfile.mkdtemp()
    output_path = None
    
    try:
        # Extrair dados
        dados_extraidos = extrair_dados_da_mensagem(request.mensagem)
        logger.info("Dados extraídos para documento")
        
        # Definir nome do arquivo
        nome_cliente = dados_extraidos.get("NOME", "cliente").replace(" ", "_")
        nome_cliente = re.sub(r'[^\w\-_.]', '', nome_cliente)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"documento_{nome_cliente}_{timestamp}.docx"
        output_path = os.path.join(temp_dir, output_filename)
        
        logger.info(f"Gerando documento: {output_filename}")
        
        try:
            # Procurar template
            possible_templates = [
                "template.docx",
                "modelo.docx",
                "templates/template.docx",
                "templates/modelo.docx"
            ]
            
            template_encontrado = None
            for template_path in possible_templates:
                if os.path.exists(template_path):
                    template_encontrado = template_path
                    break
            
            if template_encontrado:
                logger.info(f"Template encontrado: {template_encontrado}")
                preencher_modelo(template_encontrado, output_path, dados_extraidos)
                logger.info("Template preenchido com sucesso")
            else:
                logger.info("Template não encontrado, criando documento padrão")
                criar_documento_fallback(dados_extraidos, output_path)
                
        except Exception as e:
            logger.error(f"Erro no preenchimento: {e}")
            logger.info("Criando documento fallback...")
            criar_documento_fallback(dados_extraidos, output_path)
        
        # Verificar se arquivo foi criado
        if not os.path.exists(output_path):
            raise Exception("Documento não foi gerado")
        
        file_size = os.path.getsize(output_path)
        logger.info(f"Documento criado: {file_size} bytes")
        
        # Ler arquivo
        with open(output_path, "rb") as f:
            docx_content = f.read()
        
        return Response(
            content=docx_content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}",
                "Content-Length": str(len(docx_content)),
                "Cache-Control": "no-cache",
                "X-Filename": output_filename,
                "X-File-Size": str(file_size)
            }
        )
        
    except Exception as e:
        logger.error(f"ERRO CRÍTICO: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na geração do documento: {str(e)}")
    
    finally:
        # Limpar arquivos temporários
        try:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info("Arquivos temporários removidos")
        except Exception as e:
            logger.warning(f"Erro na limpeza: {e}")

@app.post("/gerar-documento-base64", response_model=DocumentoResponse)
async def gerar_documento_base64(request: MensagemRequest):
    """Endpoint que retorna o documento em base64 (ideal para integração com APIs)"""
    logger.info("=== GERAÇÃO DE DOCUMENTO N8N CLOUD (BASE64) ===")
    logger.info(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    temp_dir = tempfile.mkdtemp()
    output_path = None
    
    try:
        # Extrair dados
        dados_extraidos = extrair_dados_da_mensagem(request.mensagem)
        logger.info("Dados extraídos para documento")
        
        # Definir nome do arquivo
        nome_cliente = dados_extraidos.get("NOME", "cliente").replace(" ", "_")
        nome_cliente = re.sub(r'[^\w\-_.]', '', nome_cliente)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"documento_{nome_cliente}_{timestamp}.docx"
        output_path = os.path.join(temp_dir, output_filename)
        
        logger.info(f"Gerando documento: {output_filename}")
        
        try:
            # Procurar template
            possible_templates = [
                "template.docx",
                "modelo.docx",
                "templates/template.docx",
                "templates/modelo.docx"
            ]
            
            template_encontrado = None
            for template_path in possible_templates:
                if os.path.exists(template_path):
                    template_encontrado = template_path
                    break
            
            if template_encontrado:
                logger.info(f"Template encontrado: {template_encontrado}")
                preencher_modelo(template_encontrado, output_path, dados_extraidos)
                logger.info("Template preenchido com sucesso")
            else:
                logger.info("Template não encontrado, criando documento padrão")
                criar_documento_fallback(dados_extraidos, output_path)
                
        except Exception as e:
            logger.error(f"Erro no preenchimento: {e}")
            logger.info("Criando documento fallback...")
            criar_documento_fallback(dados_extraidos, output_path)
        
        # Verificar se arquivo foi criado
        if not os.path.exists(output_path):
            raise Exception("Documento não foi gerado")
        
        file_size = os.path.getsize(output_path)
        logger.info(f"Documento criado: {file_size} bytes")
        
        # Converter para base64
        with open(output_path, "rb") as f:
            docx_content = f.read()
            base64_content = base64.b64encode(docx_content).decode('utf-8')
        
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        return DocumentoResponse(
            success=True,
            message="Documento gerado com sucesso",
            filename=output_filename,
            file_size=file_size,
            mime_type=mime_type,
            base64_content=base64_content,
            dados_extraidos=dados_extraidos,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"ERRO CRÍTICO: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na geração do documento: {str(e)}")
    
    finally:
        # Limpar arquivos temporários
        try:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info("Arquivos temporários removidos")
        except Exception as e:
            logger.warning(f"Erro na limpeza: {e}")

@app.post("/gerar-documento-whatsapp")
async def gerar_documento_whatsapp(request: MensagemRequest):
    """Endpoint otimizado para envio via WhatsApp usando Z-API"""
    logger.info("=== GERAÇÃO DE DOCUMENTO PARA WHATSAPP ===")
    logger.info(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    temp_dir = tempfile.mkdtemp()
    output_path = None
    
    try:
        # Extrair dados
        dados_extraidos = extrair_dados_da_mensagem(request.mensagem)
        logger.info("Dados extraídos para documento WhatsApp")
        
        # Definir nome do arquivo (mais curto para WhatsApp)
        nome_cliente = dados_extraidos.get("NOME", "cliente").replace(" ", "_")
        nome_cliente = re.sub(r'[^\w\-_.]', '', nome_cliente)[:15]  # Limitar tamanho
        timestamp = datetime.now().strftime('%d%m%Y_%H%M')
        output_filename = f"doc_{nome_cliente}_{timestamp}.docx"
        output_path = os.path.join(temp_dir, output_filename)
        
        logger.info(f"Gerando documento para WhatsApp: {output_filename}")
        
        try:
            # Procurar template
            possible_templates = [
                "template.docx",
                "modelo.docx",
                "templates/template.docx",
                "templates/modelo.docx"
            ]
            
            template_encontrado = None
            for template_path in possible_templates:
                if os.path.exists(template_path):
                    template_encontrado = template_path
                    break
            
            if template_encontrado:
                logger.info(f"Template encontrado: {template_encontrado}")
                preencher_modelo(template_encontrado, output_path, dados_extraidos)
                logger.info("Template preenchido com sucesso")
            else:
                logger.info("Template não encontrado, criando documento padrão")
                criar_documento_fallback(dados_extraidos, output_path)
                
        except Exception as e:
            logger.error(f"Erro no preenchimento: {e}")
            logger.info("Criando documento fallback...")
            criar_documento_fallback(dados_extraidos, output_path)
        
        # Verificar se arquivo foi criado
        if not os.path.exists(output_path):
            raise Exception("Documento não foi gerado")
        
        file_size = os.path.getsize(output_path)
        logger.info(f"Documento criado: {file_size} bytes")
        
        # Converter para base64 para WhatsApp
        with open(output_path, "rb") as f:
            docx_content = f.read()
            base64_content = base64.b64encode(docx_content).decode('utf-8')
        
        # Resposta otimizada para integração com Z-API
        return {
            "success": True,
            "status": "document_ready",
            "message": "Documento gerado com sucesso para WhatsApp",
            "whatsapp_data": {
                "filename": output_filename,
                "base64": base64_content,
                "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "caption": f"📄 Documento gerado: {dados_extraidos.get('NOME', 'Cliente')}\n📅 Data: {dados_extraidos.get('DATA_HORA', 'N/A')}"
            },
            "document_info": {
                "filename": output_filename,
                "file_size": file_size,
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            },
            "dados_extraidos": dados_extraidos,
            "timestamp": datetime.now().isoformat(),
            "environment": "production"
        }
        
    except Exception as e:
        logger.error(f"ERRO CRÍTICO: {e}")
        return {
            "success": False,
            "status": "error",
            "message": f"Erro na geração do documento: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
    
    finally:
        # Limpar arquivos temporários
        try:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logger.info("Arquivos temporários removidos")
        except Exception as e:
            logger.warning(f"Erro na limpeza: {e}")

@app.post("/webhook/processar")
async def webhook_processar(dados: dict):
    """Endpoint específico para webhooks do N8N"""
    logger.info("=== WEBHOOK N8N CLOUD ===")
    logger.info(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logger.info(f"Dados recebidos: {dados}")
    
    try:
        agora = datetime.now()
        
        # Verificar se tem mensagem em texto
        mensagem_texto = None
        if "mensagem" in dados:
            mensagem_texto = dados["mensagem"]
        elif "message" in dados:
            mensagem_texto = dados["message"]
        elif "texto" in dados:
            mensagem_texto = dados["texto"]
        
        if mensagem_texto:
            dados_extraidos = extrair_dados_da_mensagem(mensagem_texto)
        else:
            dados_extraidos = {
                "NOME": dados.get("nome") or dados.get("NOME") or "Não informado",
                "EMAIL": dados.get("email") or dados.get("EMAIL") or "Não informado",
                "CPF": dados.get("cpf") or dados.get("CPF") or "Não informado",
                "ENDERECO": dados.get("endereco") or dados.get("ENDERECO") or "Não informado",
                "CEP": dados.get("cep") or dados.get("CEP") or "Não informado",
                "TELEFONE": dados.get("telefone") or dados.get("TELEFONE") or "Não informado",
                "VALOR": dados.get("valor") or dados.get("VALOR") or "Não informado",
                "PARCELAS": dados.get("parcelas") or dados.get("PARCELAS") or "Não informado",
                "FORMA_PAGAMENTO": dados.get("forma_pagamento") or dados.get("FORMA_PAGAMENTO") or "Não informado",
                "PACIENTE": dados.get("nome") or dados.get("NOME") or "Não informado",
                
                "DATA": agora.strftime("%d/%m/%Y"),
                "HORA": agora.strftime("%H:%M:%S"),
                "DATA_HORA": agora.strftime("%d/%m/%Y %H:%M:%S"),
                "DATA_PROCESSAMENTO": agora.strftime("%d/%m/%Y %H:%M:%S"),
                "TIMESTAMP": agora.isoformat(),
                "ARQUIVO_FONTE": "Webhook N8N Cloud"
            }
        
        return {
            "status": "success",
            "message": "Dados processados com sucesso",
            "dados": dados_extraidos,
            "timestamp": agora.isoformat(),
            "data_processamento": agora.strftime("%d/%m/%Y %H:%M:%S"),
            "environment": "production"
        }
        
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info("🚀 Iniciando servidor FastAPI para N8N + WhatsApp (Cloud Version)...")
    logger.info(f"🌐 Porta: {port}")
    logger.info(f"📅 Data atual: {datetime.now().strftime('%d/%m/%Y')}")
    logger.info(f"🕐 Hora atual: {datetime.now().strftime('%H:%M:%S')}")
    
    uvicorn.run(app, host="0.0.0.0", port=port)