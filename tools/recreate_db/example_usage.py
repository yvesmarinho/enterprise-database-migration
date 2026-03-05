#!/usr/bin/env python3
"""
Exemplos de uso do DatabaseRecreator

Demonstra diferentes formas de usar o módulo recreate_database.py
"""

from recreate_database import DatabaseRecreator
import logging

# Configura logging para ver detalhes
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_mysql_simple():
    """Exemplo 1: Uso simples com MySQL"""
    print("\n" + "="*60)
    print("EXEMPLO 1: Recriação simples MySQL")
    print("="*60 + "\n")

    recreator = DatabaseRecreator(
        config_path='../../secrets/mysql_config.json',
        database_name='perfexcrm_db'
    )

    try:
        result = recreator.execute_full_recreation(
            force=False,
            save_report=True
        )

        print(f"\nResultado: {result['success']}")
        print(f"Etapas: {result['steps_completed']}")

    except Exception as e:
        print(f"Erro: {e}")


def example_2_postgresql_forced():
    """Exemplo 2: PostgreSQL com force (termina conexões)"""
    print("\n" + "="*60)
    print("EXEMPLO 2: Recriação PostgreSQL com force")
    print("="*60 + "\n")

    recreator = DatabaseRecreator(
        config_path='../../secrets/postgresql_source_config.json',
        database_name='app_workforce'
    )

    try:
        result = recreator.execute_full_recreation(
            force=True,  # Termina conexões ativas
            save_report=True
        )

        print(f"\nSucesso: {result['success']}")
        if result.get('report_file'):
            print(f"Relatório salvo em: {result['report_file']}")

    except Exception as e:
        print(f"Erro: {e}")


def example_3_step_by_step():
    """Exemplo 3: Controle passo a passo"""
    print("\n" + "="*60)
    print("EXEMPLO 3: Execução passo a passo")
    print("="*60 + "\n")

    recreator = DatabaseRecreator(
        config_path='../../secrets/mysql_config.json',
        database_name='test_db'
    )

    try:
        # Passo 1: Conecta
        print("Passo 1: Conectando...")
        recreator.connect()

        # Passo 2: Coleta metadados
        print("Passo 2: Coletando metadados...")
        metadata = recreator.collect_metadata()

        print(f"\nMetadados coletados:")
        print(f"  - Banco existe: {metadata.get('exists')}")
        print(f"  - Tipo: {metadata.get('type')}")
        print(f"  - Charset: {metadata.get('charset')}")
        print(f"  - Tabelas: {metadata.get('table_count')}")

        # Passo 3: Salva relatório
        print("\nPasso 3: Salvando relatório...")
        report_file = recreator.save_metadata_report()
        print(f"Relatório: {report_file}")

        # Passo 4: Apaga banco (se existir)
        if metadata.get('exists'):
            print("\nPasso 4: Apagando banco...")
            recreator.drop_database()
        else:
            print("\nPasso 4: Banco não existe, pulando...")

        # Passo 5: Recria banco
        print("\nPasso 5: Recriando banco vazio...")
        recreator.create_database()

        print("\n✓ Processo concluído com sucesso!")

    except Exception as e:
        print(f"Erro: {e}")

    finally:
        recreator.close()


def example_4_metadata_only():
    """Exemplo 4: Apenas coletar metadados (sem apagar)"""
    print("\n" + "="*60)
    print("EXEMPLO 4: Apenas coletar metadados")
    print("="*60 + "\n")

    recreator = DatabaseRecreator(
        config_path='../../secrets/mysql_config.json',
        database_name='perfexcrm_db'
    )

    try:
        recreator.connect()
        metadata = recreator.collect_metadata()

        print("\nInformações do banco:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")

        # Salva relatório mas NÃO apaga o banco
        report_file = recreator.save_metadata_report()
        print(f"\nRelatório salvo: {report_file}")
        print("Banco NÃO foi modificado.")

    except Exception as e:
        print(f"Erro: {e}")

    finally:
        recreator.close()


def example_5_multiple_databases():
    """Exemplo 5: Recriar múltiplos bancos"""
    print("\n" + "="*60)
    print("EXEMPLO 5: Recriar múltiplos bancos")
    print("="*60 + "\n")

    databases = ['test_db1', 'test_db2', 'test_db3']
    config = '../../secrets/mysql_config.json'

    results = {}

    for db_name in databases:
        print(f"\n--- Processando: {db_name} ---")

        try:
            recreator = DatabaseRecreator(config, db_name)
            result = recreator.execute_full_recreation(
                force=False,
                save_report=True
            )
            results[db_name] = 'SUCCESS' if result['success'] else 'FAILED'

        except Exception as e:
            print(f"Erro em {db_name}: {e}")
            results[db_name] = 'ERROR'

    print("\n" + "="*60)
    print("RESUMO")
    print("="*60)
    for db, status in results.items():
        print(f"  {db}: {status}")


def example_6_with_validation():
    """Exemplo 6: Recriação com validação"""
    print("\n" + "="*60)
    print("EXEMPLO 6: Recriação com validação")
    print("="*60 + "\n")

    database_name = 'test_db'
    config_path = '../../secrets/postgresql_source_config.json'

    # Fase 1: Backup de metadados
    print("FASE 1: Backup de metadados...")
    recreator = DatabaseRecreator(config_path, database_name)

    try:
        recreator.connect()
        metadata_before = recreator.collect_metadata()
        recreator.save_metadata_report()
        print(f"✓ Metadados salvos: {metadata_before}")
        recreator.close()

        # Fase 2: Recriação
        print("\nFASE 2: Recriação do banco...")
        recreator = DatabaseRecreator(config_path, database_name)
        result = recreator.execute_full_recreation(force=True)

        if not result['success']:
            raise Exception("Falha na recriação")

        # Fase 3: Validação
        print("\nFASE 3: Validação...")
        recreator = DatabaseRecreator(config_path, database_name)
        recreator.connect()
        metadata_after = recreator.collect_metadata()

        # Verifica se o banco foi recriado
        if metadata_after['exists']:
            print("✓ Banco existe após recriação")
        else:
            raise Exception("Banco não foi criado!")

        # Verifica se está vazio
        if metadata_after['table_count'] == 0:
            print("✓ Banco está vazio (conforme esperado)")
        else:
            print(f"⚠ Atenção: Banco tem {metadata_after['table_count']} tabelas!")

        print("\n✓ Validação concluída com sucesso!")

    except Exception as e:
        print(f"✗ Erro: {e}")

    finally:
        recreator.close()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("DATABASE RECREATOR - EXEMPLOS DE USO")
    print("="*60)

    print("\nEscolha um exemplo para executar:")
    print("1. Recriação simples MySQL")
    print("2. PostgreSQL com force")
    print("3. Execução passo a passo")
    print("4. Apenas coletar metadados")
    print("5. Recriar múltiplos bancos")
    print("6. Recriação com validação")
    print("0. Sair")

    choice = input("\nOpção: ").strip()

    examples = {
        '1': example_1_mysql_simple,
        '2': example_2_postgresql_forced,
        '3': example_3_step_by_step,
        '4': example_4_metadata_only,
        '5': example_5_multiple_databases,
        '6': example_6_with_validation
    }

    if choice in examples:
        examples[choice]()
    elif choice == '0':
        print("Saindo...")
    else:
        print("Opção inválida!")
