#!/usr/bin/env python3
"""
Script para executar testes do Worker com verificações de ambiente.

Este script verifica se o ambiente está configurado corretamente
antes de executar os testes.
"""

import os
import subprocess
import sys
from pathlib import Path

import requests


def check_supabase_local():
    """Verifica se o Supabase local está rodando."""
    try:
        response = requests.get("http://127.0.0.1:54321/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def check_test_images():
    """Verifica se as imagens de teste existem."""
    test_data_path = Path("../corrector_backend_v2/tests/test_data/10_4_filled1")
    if not test_data_path.exists():
        return False
    
    images = list(test_data_path.glob("*.jpeg"))
    return len(images) > 0


def check_dependencies():
    """Verifica se as dependências estão instaladas."""
    required_packages = [
        "pytest",
        "hypothesis",
        "opencv-python",
        "numpy",
        "openpyxl",
        "requests",
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing.append(package)
    
    return missing


def main():
    """Função principal."""
    print("🧪 Verificando ambiente para testes do Worker...")
    
    # Verifica dependências
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"❌ Dependências faltando: {', '.join(missing_deps)}")
        print("   Execute: pip install -r requirements.txt")
        return 1
    
    print("✅ Dependências OK")
    
    # Verifica imagens de teste
    if not check_test_images():
        print("⚠️  Imagens de teste não encontradas")
        print("   Alguns testes de integração serão pulados")
    else:
        print("✅ Imagens de teste encontradas")
    
    # Verifica Supabase local
    supabase_running = check_supabase_local()
    if not supabase_running:
        print("⚠️  Supabase local não está rodando")
        print("   Testes de integração serão pulados")
        print("   Para executar todos os testes, execute: supabase start")
    else:
        print("✅ Supabase local rodando")
    
    # Determina quais testes executar
    test_args = ["pytest"]
    
    if len(sys.argv) > 1:
        # Usa argumentos passados
        test_args.extend(sys.argv[1:])
    else:
        # Configuração padrão baseada no ambiente
        if supabase_running:
            print("\n🚀 Executando todos os testes (incluindo integração)...")
            test_args.extend([
                "-m", "not slow",  # Pula testes lentos por padrão
                "--tb=short",
                "-v"
            ])
        else:
            print("\n🚀 Executando apenas testes unitários...")
            test_args.extend([
                "-m", "not integration and not slow",
                "--tb=short",
                "-v"
            ])
    
    # Executa os testes
    try:
        result = subprocess.run(test_args, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Testes interrompidos pelo usuário")
        return 1
    except Exception as e:
        print(f"❌ Erro ao executar testes: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())