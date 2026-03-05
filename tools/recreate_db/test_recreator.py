#!/usr/bin/env python3
"""
Testes simples para validar o módulo DatabaseRecreator

Não requer pytest, apenas execução direta.
"""

import sys
import json
from pathlib import Path
from recreate_database import DatabaseRecreator


def test_load_mysql_config():
    """Testa carregamento de config MySQL"""
    print("\n📋 Teste 1: Carregamento de config MySQL")

    config_path = "../../secrets/mysql_config.json"

    if not Path(config_path).exists():
        print("⚠️  Config não encontrado, pulando teste")
        return True

    try:
        recreator = DatabaseRecreator(config_path, "test_db")
        assert recreator.db_type == 'mysql', "Tipo deveria ser MySQL"
        assert recreator.config is not None, "Config não foi carregado"
        print("✅ Config MySQL carregado corretamente")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def test_load_postgresql_config():
    """Testa carregamento de config PostgreSQL"""
    print("\n📋 Teste 2: Carregamento de config PostgreSQL")

    config_path = "../../secrets/postgresql_source_config.json"

    if not Path(config_path).exists():
        print("⚠️  Config não encontrado, pulando teste")
        return True

    try:
        recreator = DatabaseRecreator(config_path, "test_db")
        assert recreator.db_type == 'postgresql', "Tipo deveria ser PostgreSQL"
        assert recreator.config is not None, "Config não foi carregado"
        print("✅ Config PostgreSQL carregado corretamente")
        return True
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def test_detect_db_type():
    """Testa detecção automática do tipo de banco"""
    print("\n📋 Teste 3: Detecção automática do tipo")

    # Cria configs temporários
    mysql_config = {
        "source": {"host": "localhost", "port": 3306, "user": "test", "password": "test"}
    }

    pg_config = {
        "server": {"host": "localhost", "port": 5432},
        "authentication": {"user": "test", "password": "test"}
    }

    # Testa MySQL
    with open("/tmp/test_mysql.json", "w") as f:
        json.dump(mysql_config, f)

    try:
        recreator = DatabaseRecreator("/tmp/test_mysql.json", "test")
        assert recreator.db_type == 'mysql'
        print("✅ MySQL detectado corretamente")
    except Exception as e:
        print(f"❌ Erro MySQL: {e}")
        return False

    # Testa PostgreSQL
    with open("/tmp/test_pg.json", "w") as f:
        json.dump(pg_config, f)

    try:
        recreator = DatabaseRecreator("/tmp/test_pg.json", "test")
        assert recreator.db_type == 'postgresql'
        print("✅ PostgreSQL detectado corretamente")
    except Exception as e:
        print(f"❌ Erro PostgreSQL: {e}")
        return False

    return True


def test_connection_params_extraction():
    """Testa extração de parâmetros de conexão"""
    print("\n📋 Teste 4: Extração de parâmetros de conexão")

    # Testa diferentes estruturas
    configs = [
        {
            "source": {
                "host": "host1", "port": 3306,
                "user": "user1", "password": "pass1"
            }
        },
        {
            "server": {"host": "host2", "port": 5432},
            "authentication": {"user": "user2", "password": "pass2"}
        },
        {
            "destination": {
                "host": "host3", "port": 3306,
                "user": "user3", "password": "pass3"
            }
        }
    ]

    for i, config in enumerate(configs, 1):
        with open(f"/tmp/test_config_{i}.json", "w") as f:
            json.dump(config, f)

        try:
            recreator = DatabaseRecreator(f"/tmp/test_config_{i}.json", "test")
            params = recreator._get_connection_params()

            assert params['host'] is not None, f"Host não extraído de config {i}"
            assert params['port'] is not None, f"Port não extraído de config {i}"
            assert params['user'] is not None, f"User não extraído de config {i}"
            print(f"✅ Estrutura {i} OK: {params['host']}:{params['port']}")

        except Exception as e:
            print(f"❌ Erro na config {i}: {e}")
            return False

    return True


def test_metadata_structure():
    """Testa estrutura dos metadados (sem conexão real)"""
    print("\n📋 Teste 5: Estrutura de metadados")

    # Testa se os métodos existem
    config = {"source": {"host": "x", "port": 3306, "user": "x", "password": "x"}}
    with open("/tmp/test_meta.json", "w") as f:
        json.dump(config, f)

    try:
        recreator = DatabaseRecreator("/tmp/test_meta.json", "test_db")

        # Verifica atributos
        assert hasattr(recreator, 'collect_metadata'), "Método collect_metadata não existe"
        assert hasattr(recreator, 'drop_database'), "Método drop_database não existe"
        assert hasattr(recreator, 'create_database'), "Método create_database não existe"
        assert hasattr(recreator, 'save_metadata_report'), "Método save_metadata_report não existe"
        assert hasattr(recreator, 'execute_full_recreation'), "Método execute_full_recreation não existe"

        print("✅ Todos os métodos necessários estão presentes")
        return True

    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


def run_all_tests():
    """Executa todos os testes"""
    print("="*60)
    print("EXECUTANDO TESTES DO DATABASE RECREATOR")
    print("="*60)

    tests = [
        ("Carregamento MySQL", test_load_mysql_config),
        ("Carregamento PostgreSQL", test_load_postgresql_config),
        ("Detecção de tipo", test_detect_db_type),
        ("Extração de parâmetros", test_connection_params_extraction),
        ("Estrutura de metadados", test_metadata_structure),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Exceção em {name}: {e}")
            results.append((name, False))

    # Resumo
    print("\n" + "="*60)
    print("RESUMO DOS TESTES")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} testes passaram")

    if passed == total:
        print("\n🎉 Todos os testes passaram!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} teste(s) falharam")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
