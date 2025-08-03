#!/usr/bin/env python3
"""
Script para testar a API de processamento de mensagens
"""

import requests
import json
from datetime import datetime

# Configuração
API_BASE_URL = "http://localhost:8000"

def test_health():
    """Testa o health check"""
    print("🏥 Testando health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check OK")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check falhou: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erro no health check: {e}")
        return False

def test_processar_mensagem():
    """Testa o processamento de mensagem"""
    print("\n📝 Testando processamento de mensagem...")
    
    mensagem_teste = """Nome: Eduardo Silva
Email: eduardo.silva@gmail.com
CPF: 123.456.789-00
Endereço: Rua das Flores, 123, Bloco A, Apt 45
CEP: 12345-678
Telefone: (11) 99999-9999
Valor: 1.500,00
Quantidade de Parcelas: 12
Forma de pagamento: Cartão de Crédito"""

    payload = {
        "mensagem": mensagem_teste,
        "webhook_id": "teste_123",
        "origem": "teste_local"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/processar-mensagem",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Processamento de mensagem OK")
            data = response.json()
            print(f"   Sucesso: {data.get('sucesso')}")
            print(f"   Mensagem: {data.get('mensagem')}")
            print("   Dados extraídos:")
            for campo, valor in data.get('dados_extraidos', {}).items():
                if campo not in ['TIMESTAMP']:
                    print(f"     {campo}: {valor}")
        else:
            print(f"❌ Erro no processamento: {response.status_code}")
            print(f"   Response: {response.text}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Erro no teste de mensagem: {e}")
        return False

def test_processar_json():
    """Testa o processamento de JSON"""
    print("\n🔧 Testando processamento JSON...")
    
    dados_teste = {
        "nome": "Maria Santos",
        "email": "maria.santos@email.com",
        "cpf": "987.654.321-00",
        "endereco": "Av. Principal, 456, Casa 2",
        "cep": "87654-321",
        "telefone": "(21) 88888-8888",
        "valor": "2.500,00",
        "parcelas": "6",
        "forma_pagamento": "PIX"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/processar-json",
            json=dados_teste,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Processamento JSON OK")
            data = response.json()
            print(f"   Sucesso: {data.get('sucesso')}")
            print("   Dados processados:")
            for campo, valor in data.get('dados_extraidos', {}).items():
                if campo not in ['TIMESTAMP']:
                    print(f"     {campo}: {valor}")
        else:
            print(f"❌ Erro no processamento JSON: {response.status_code}")
            print(f"   Response: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Erro no teste JSON: {e}")
        return False

def test_webhook():
    """Testa o webhook genérico"""
    print("\n🪝 Testando webhook...")
    
    dados_webhook = {
        "mensagem": "Nome: João Webhook\nEmail: joao@webhook.com\nCPF: 111.222.333-44",
        "origem": "n8n_teste",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/webhook/processar",
            json=dados_webhook,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Webhook OK")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
        else:
            print(f"❌ Erro no webhook: {response.status_code}")
            print(f"   Response: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Erro no teste webhook: {e}")
        return False

def test_gerar_documento():
    """Testa a geração de documento"""
    print("\n📄 Testando geração de documento...")
    
    mensagem_teste = """Nome: Carlos Documento
Email: carlos@documento.com
CPF: 555.666.777-88
Endereço: Rua do Teste, 789
CEP: 01234-567
Telefone: (11) 77777-7777
Valor: 3.000,00
Quantidade de Parcelas: 24
Forma de pagamento: Boleto"""

    payload = {
        "mensagem": mensagem_teste,
        "origem": "teste_documento"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/gerar-documento",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Geração de documento OK")
            
            # Salvar arquivo para verificação
            filename = f"teste_documento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"   Arquivo salvo: {filename}")
            print(f"   Tamanho: {len(response.content)} bytes")
        else:
            print(f"❌ Erro na geração: {response.status_code}")
            print(f"   Response: {response.text}")
            
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Erro no teste de documento: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 INICIANDO TESTES DA API")
    print("=" * 50)
    
    resultados = []
    
    # Executar testes
    resultados.append(("Health Check", test_health()))
    resultados.append(("Processar Mensagem", test_processar_mensagem()))
    resultados.append(("Processar JSON", test_processar_json()))
    resultados.append(("Webhook", test_webhook()))
    resultados.append(("Gerar Documento", test_gerar_documento()))
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES")
    print("=" * 50)
    
    sucessos = 0
    for nome, sucesso in resultados:
        status = "✅ PASSOU" if sucesso else "❌ FALHOU"
        print(f"{nome:<20} {status}")
        if sucesso:
            sucessos += 1
    
    print(f"\n🎯 Resultado: {sucessos}/{len(resultados)} testes passaram")
    
    if sucessos == len(resultados):
        print("🎉 Todos os testes passaram! API está funcionando corretamente.")
    else:
        print("⚠️  Alguns testes falharam. Verifique os logs acima.")
        print("💡 Dicas:")
        print("   - Certifique-se que a API está rodando (python main.py)")
        print("   - Verifique se o template.docx existe")
        print("   - Confirme se todas as dependências estão instaladas")

if __name__ == "__main__":
    main()