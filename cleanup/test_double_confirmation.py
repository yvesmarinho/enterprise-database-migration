#!/usr/bin/env python3
"""
Teste de Confirmação Dupla
==========================

Script para testar a lógica de confirmação dupla do servidor de origem.
"""

def test_confirm_action():
    """Simula a função de confirmação para teste."""

    def mock_confirm_action(server_name: str, dry_run: bool = False) -> bool:
        """Versão simulada da função de confirmação."""
        if dry_run:
            return True

        print(f"\n🧪 Testando confirmação para servidor: {server_name}")

        # PRIMEIRA confirmação (obrigatória para todos)
        print("📝 [1/2] Primeira confirmação obrigatória: 'CONFIRMO'")

        # SEGUNDA confirmação (obrigatória para todos)
        print("📝 [2/2] Segunda confirmação obrigatória:")

        if 'origem' in server_name.lower():
            print("🚨 Servidor de ORIGEM - Exige: 'ORIGEM-CONFIRMO'")
        else:
            print("🎯 Servidor de DESTINO/AMBOS - Exige: 'FINAL-CONFIRMO'")

        return True

    # Testar diferentes cenários
    test_cases = [
        ("origem", False),
        ("destino", False),
        ("origem, destino", False),
        ("origem", True),  # dry-run
    ]

    print("🧪 Teste de Confirmação Dupla")
    print("=" * 40)

    for server_name, dry_run in test_cases:
        print(f"\n{'=' * 40}")
        print(f"🎯 Cenário: server='{server_name}', dry_run={dry_run}")

        result = mock_confirm_action(server_name, dry_run)

        if dry_run:
            print("🔍 Modo dry-run: confirmação automática")
        elif result:
            print("✅ Confirmação aprovada")
        else:
            print("❌ Confirmação negada")

    print(f"\n{'=' * 40}")
    print("📋 Resumo das Regras ATUALIZADAS:")
    print("   • TODOS os servidores: Confirmação DUPLA obrigatória")
    print("   • Servidor ORIGEM: [1/2] 'CONFIRMO' + [2/2] 'ORIGEM-CONFIRMO'")
    print("   • Servidor DESTINO/AMBOS: [1/2] 'CONFIRMO' + [2/2] 'FINAL-CONFIRMO'")
    print("   • Modo dry-run: Sem confirmação necessária")
    print("   • --force: Pula todas as confirmações")

if __name__ == "__main__":
    test_confirm_action()
