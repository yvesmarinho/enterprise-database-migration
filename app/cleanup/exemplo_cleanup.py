#!/usr/bin/env python3
"""
Exemplo Rápido de L    print("💡 Para executar REALMENTE (sem --dry-run):")
    print("   Remova --dry-run e adicione --force para pular confirmação")
    print()
    print("🚨 ATENÇÃO - CONFIRMAÇÃO DUPLA OBRIGATÓRIA (COM HOSTS):")
    print("   Servidor ORIGEM apenas:")
    print("     1ª confirmação: Digite 'CONFIRMO'")
    print("     2ª confirmação: Digite 'ORIGEM-CONFIRMO'")
    print("   Servidor DESTINO apenas:")
    print("     1ª confirmação: Digite 'CONFIRMO'")
    print("     2ª confirmação: Digite 'FINAL-CONFIRMO'")
    print("   AMBOS servidores:")
    print("     1ª confirmação: Digite 'CONFIRMO'")
    print("     2ª confirmação: Digite 'AMBOS-CONFIRMO'")
    print()
    print("🖥️ NOVIDADE: Confirmações mostram HOST e PORTA dos servidores!")
    print()
    print("🛡️ Bancos/usuários protegidos não são apagados:")
    print("   - postgres, template0, template1")
    print("   - postgres, *superuser*")Banco
==================================

Script simplificado para demonstrar uso do cleanup_database.py

Exemplos seguros para testar.
"""

import subprocess
import sys

def run_cleanup_example():
    """Executa exemplos de limpeza."""

    print("🧹 Exemplos de Limpeza de Banco PostgreSQL")
    print("="*50)
    print()
    print("⚠️  ATENÇÃO: Scripts de exemplo para desenvolvimento")
    print("   Use apenas em servidores de teste!")
    print()

    examples = [
        ("🔍 Ver o que seria apagado (simulação segura)",
         "python3 cleanup_database.py --server origem --dry-run"),

        ("🗑️ Apagar apenas bancos de dados",
         "python3 cleanup_database.py --server origem --databases-only --dry-run"),

        ("👥 Apagar apenas usuários",
         "python3 cleanup_database.py --server origem --users-only --dry-run"),

        ("🧹 Limpeza completa (bancos + usuários)",
         "python3 cleanup_database.py --server origem --dry-run"),

        ("🎯 Limpar ambos servidores",
         "python3 cleanup_database.py --server ambos --dry-run"),
    ]

    print("📋 Exemplos disponíveis:")
    for i, (desc, cmd) in enumerate(examples, 1):
        print(f"  {i}. {desc}")
        print(f"     {cmd}")
        print()

    print("💡 Para executar REALMENTE (sem --dry-run):")
    print("   Remova --dry-run e adicione --force para pular confirmação")
    print()
    print("� ATENÇÃO - Servidor ORIGEM requer confirmação DUPLA:")
    print("   1ª confirmação: Digite 'CONFIRMO'")
    print("   2ª confirmação: Digite 'ORIGEM-CONFIRMO'")
    print()
    print("�🛡️ Bancos/usuários protegidos não são apagados:")
    print("   - postgres, template0, template1")
    print("   - postgres, *superuser*")

    # Opção interativa
    choice = input("\n❓ Executar exemplo? (1-5, Enter para sair): ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(examples):
        idx = int(choice) - 1
        desc, cmd = examples[idx]

        print(f"\n🚀 Executando: {desc}")
        print(f"📝 Comando: {cmd}")
        print("-" * 50)

        try:
            result = subprocess.run(cmd.split(), cwd=".")
            return result.returncode
        except Exception as e:
            print(f"❌ Erro: {e}")
            return 1
    else:
        print("👋 Saindo...")
        return 0

if __name__ == "__main__":
    sys.exit(run_cleanup_example())
