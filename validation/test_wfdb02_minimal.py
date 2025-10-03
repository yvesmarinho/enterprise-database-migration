#!/usr/bin/env python3
"""
Teste Mínimo de Conexão com WFDB02
"""

import socket
import sys
import time


def test_tcp_connection(host, port, timeout=5):
    """Testa conexão TCP básica"""
    print(f"Testando conexão TCP para {host}:{port}...")
    start_time = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        if result == 0:
            print(
                f"✅ Conexão estabelecida com {host}:{port} em {time.time() - start_time:.2f} segundos"
            )
            sock.close()
            return True
        else:
            print(f"❌ Falha ao conectar com {host}:{port} (código {result})")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar com {host}:{port}: {e}")
        print(f"Tempo até falha: {time.time() - start_time:.2f} segundos")
        return False
    finally:
        try:
            sock.close()
        except:
            pass


if __name__ == "__main__":
    host = "82.197.64.145"

    print("=== Teste Mínimo de Conexão com WFDB02 ===")
    print(f"Host: {host}")
    print(f"Timestamp: {time.time()}")

    # Portas a testar
    ports = {
        3306: "MySQL",
        5432: "PostgreSQL (PgBouncer)",
        6432: "PostgreSQL (Direto)",
        5010: "SSH",
        9100: "Node Exporter",
        9104: "MySQL Exporter",
        9187: "PostgreSQL Exporter",
    }

    results = {}

    for port, desc in ports.items():
        print(f"\nTestando {desc} na porta {port}...")
        result = test_tcp_connection(host, port)
        results[f"{desc} ({port})"] = result

    print("\n=== Resumo dos Testes ===")
    success_count = 0
    for service, success in results.items():
        status = "✅ Sucesso" if success else "❌ Falha"
        print(f"{service}: {status}")
        if success:
            success_count += 1

    print(f"\nResultado final: {success_count}/{len(ports)} conexões bem-sucedidas")
