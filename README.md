# Guia rápido

## 1) Criar e ativar a virtualenv

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate
```

## 2) Instalar dependências

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Executar o servidor

- Opção A — usando o script (Windows)
  - Basta rodar o arquivo run-server.bat.

Exemplo de conteúdo do run-server.bat:

- Opção B — via Python
  - Já com o venv ativado, digite:
  ```powershell
  python -m app.main
  ```
