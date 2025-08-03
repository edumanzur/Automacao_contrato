@echo off
echo 🚀 Iniciando API Processamento de Mensagens N8N

:: Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado. Instale Python 3.8+ primeiro.
    pause
    exit /b 1
)

:: Verificar se pip está instalado
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip não encontrado. Instale pip primeiro.
    pause
    exit /b 1
)

:: Criar ambiente virtual se não existir
if not exist "venv" (
    echo 📦 Criando ambiente virtual...
    python -m venv venv
)

:: Ativar ambiente virtual
echo 🔧 Ativando ambiente virtual...
call venv\Scripts\activate.bat

:: Instalar dependências
echo 📥 Instalando dependências...
pip install -r requirements.txt

:: Verificar se template existe
if not exist "template.docx" (
    if not exist "modelo.docx" (
        echo ⚠️  AVISO: Template não encontrado!
        echo    Crie um arquivo 'template.docx' com os placeholders:
        echo    {{NOME}}, {{EMAIL}}, {{CPF}}, etc.
        echo.
    )
)

:: Verificar arquivos necessários
echo 🔍 Verificando arquivos...
if not exist "main.py" (
    echo ❌ main.py não encontrado!
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo ❌ requirements.txt não encontrado!
    pause
    exit /b 1
)

echo ✅ Todos os arquivos encontrados!

:: Iniciar servidor
echo 🌐 Iniciando servidor em http://localhost:8000
echo 📋 Endpoints disponíveis:
echo    GET  /                    - Informações da API
echo    GET  /health              - Health check
echo    POST /processar-mensagem  - Processar mensagem
echo    POST /gerar-documento     - Gerar documento DOCX
echo    POST /webhook/processar   - Webhook N8N
echo.
echo 🛑 Para parar: Ctrl+C
echo.

python main.py

pause