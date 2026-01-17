#!/usr/bin/env python3
"""
Quick launcher for PerfexCRM MySQL Migration
===========================================

Wrapper simples para executar a migração do PerfexCRM.

Uso:
    python3 cli/migrate_perfexcrm.py
    ou
    ./cli/migrate_perfexcrm.py
"""

import sys
from pathlib import Path

# Adicionar projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Launcher principal."""
    try:
        from app.orchestrators.migrate_perfexcrm_mysql import main as migrate_main
        return migrate_main()
    except ImportError as e:
        print(f"❌ Erro ao importar migrador: {e}")
        print("💡 Verifique se as dependências estão instaladas:")
        print("   uv sync")
        return 1
    except Exception as e:
        print(f"💥 Erro inesperado: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
