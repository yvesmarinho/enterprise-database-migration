#!/usr/bin/env python3
"""
Launcher para PostgreSQL Migration Orchestrator
===============================================

Script principal para executar migrações PostgreSQL de forma segura.
Substitui completamente o script bash anterior.

Versão: 1.0.0
Data: 03/10/2025
"""

import sys
import os
from pathlib import Path

# Adicionar diretório do projeto ao Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Launcher principal."""
    try:
        # Importar e executar o orquestrador
        from src.migration.orchestrator_pure_python import main as orchestrator_main
        return orchestrator_main()
    except ImportError as e:
        print(f"❌ Erro ao importar orquestrador: {e}")
        print("💡 Verifique se está executando a partir do diretório raiz do projeto")
        return 1
    except Exception as e:
        print(f"💥 Erro inesperado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
