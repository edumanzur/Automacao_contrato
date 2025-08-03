#!/bin/bash

# Script para iniciar o projeto
echo "🚀 Iniciando API Processamento de Mensagens N8N"

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Instale Python 3.8+ primeiro."
    exit 1
fi

# Verificar se pip está instalado
if ! command -v pip &> /dev/null; then
    echo "❌ pip não encontrado. Instale pip primeiro."
    exit 1
fi

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "📥 Instalando dependências..."
pip install -r requirements.txt

# Verificar se template existe
if [ ! -f "template.docx" ] && [ ! -f "modelo.docx" ]; then
    echo "⚠️  AVISO: Template não encontrado!"
    echo "   Crie um arquivo 'template.docx' com os placeholders:"
    echo "   {{NOME}}, {{EMAIL}}, {{CPF}}, etc."
    echo ""
fi

# Verificar arquivos necessários
echo "🔍 Verificando arquivos..."
if [ ! -f "main.py" ]; then
    echo "❌ main.py não encontrado!"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt não encontrado!"
    exit 1
fi

echo "✅ Todos os arquivos encontrados!"

# Iniciar servidor
echo "🌐 Iniciando servidor em http://localhost:8000"
echo "📋 Endpoints disponíveis:"
echo "   GET  /                    - Informações da API"
echo "   GET  /health              - Health check"
echo "   POST /processar-mensagem  - Processar mensagem"
echo "   POST /gerar-documento     - Gerar documento DOCX"
echo "   POST /webhook/processar   - Webhook N8N"
echo ""
echo "🛑 Para parar: Ctrl+C"
echo ""

python main.py