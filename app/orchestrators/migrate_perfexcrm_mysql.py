#!/usr/bin/env python3
"""
MySQL Migration Script - PerfexCRM
===================================

Script simples para migrar banco MySQL do PerfexCRM.
Usa migration_user para todas as operações.

Origem: wf004.vya.digital
Destino: wfdb02.vya.digital
Database: perfexcrm_db

Versão: 2.0.0
Data: 14/01/2026
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from colorama import Fore, Style, init

# Adicionar projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

init(autoreset=True)


def log(message: str, level: str = "INFO"):
    """Log simples."""
    icons = {
        "INFO": f"{Fore.BLUE}ℹ️",
        "SUCCESS": f"{Fore.GREEN}✓",
        "ERROR": f"{Fore.RED}✗",
    }
    icon = icons.get(level, "ℹ️")
    print(f"{icon} {message}{Style.RESET_ALL}")


def run_mysql_command(host: str, user: str, password: str, database: str, sql: str) -> bool:
    """Executa comando MySQL."""
    cmd = [
        "mysql",
        f"-h{host}",
        f"-u{user}",
        f"-p{password}",
        database,
        "-e",
        sql
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def main():
    """Migração principal."""
    # Banner
    print(f"\n{Fore.BLUE}{'=' * 70}")
    print(f"{Fore.CYAN}     Migração MySQL - PerfexCRM")
    print(f"{Fore.CYAN}     wf004.vya.digital → wfdb02.vya.digital")
    print(f"{Fore.BLUE}{'=' * 70}{Style.RESET_ALL}\n")

    # Carregar configurações
    config_file = project_root / "secrets" / "mysql_config.json"
    if not config_file.exists():
        log(f"Arquivo de configuração não encontrado: {config_file}", "ERROR")
        return 1

    with open(config_file) as f:
        config = json.load(f)

    src = config['source']
    dst = config['destination']
    db = config['perfexcrm']['database']

    log(f"Origem: {src['user']}@{src['host']}")
    log(f"Destino: {dst['user']}@{dst['host']}")
    log(f"Database: {db}")
    print()

    # Criar diretório de backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_root / "backup" / f"perfexcrm_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    dump_file = backup_dir / f"{db}_dump.sql"

    log(f"Backup em: {backup_dir}")
    print()

    # ETAPA 1: Dump do banco origem
    log("ETAPA 1: Criando dump do banco de origem...")

    dump_cmd = [
        "mysqldump",
        f"-h{src['host']}",
        f"-u{src['user']}",
        f"-p{src['password']}",
        "--single-transaction",
        "--routines",
        "--triggers",
        "--set-gtid-purged=OFF",
        db
    ]

    try:
        with open(dump_file, 'w') as f:
            result = subprocess.run(
                dump_cmd, stdout=f, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            log(f"Erro no dump: {result.stderr}", "ERROR")
            return 1

        size_mb = dump_file.stat().st_size / (1024 * 1024)
        log(f"Dump criado: {size_mb:.2f} MB", "SUCCESS")
    except Exception as e:
        log(f"Erro ao criar dump: {e}", "ERROR")
        return 1

    print()

    # ETAPA 2: Criar banco no destino
    log("ETAPA 2: Criando banco no destino...")

    create_db_cmd = f"DROP DATABASE IF EXISTS `{db}`; CREATE DATABASE `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

    result = subprocess.run([
        "mysql",
        f"-h{dst['host']}",
        f"-u{dst['user']}",
        f"-p{dst['password']}",
        "-e",
        create_db_cmd
    ], capture_output=True, text=True)

    if result.returncode != 0:
        log(f"Erro ao criar banco: {result.stderr}", "ERROR")
        return 1

    log(f"Banco {db} criado", "SUCCESS")
    print()

    # ETAPA 3: Restaurar dump
    log("ETAPA 3: Restaurando dados...")

    try:
        with open(dump_file, 'r') as f:
            result = subprocess.run([
                "mysql",
                f"-h{dst['host']}",
                f"-u{dst['user']}",
                f"-p{dst['password']}",
                db
            ], stdin=f, capture_output=True, text=True)

        if result.returncode != 0:
            log(f"Erro na restauração: {result.stderr}", "ERROR")
            return 1

        log("Dados restaurados", "SUCCESS")
    except Exception as e:
        log(f"Erro ao restaurar: {e}", "ERROR")
        return 1

    print()

    # ETAPA 4: Validação
    log("ETAPA 4: Validando migração...")

    # Contar tabelas
    count_cmd = f"SELECT COUNT(*) AS count FROM information_schema.tables WHERE table_schema = '{db}'"

    result = subprocess.run([
        "mysql",
        f"-h{dst['host']}",
        f"-u{dst['user']}",
        f"-p{dst['password']}",
        "-N",
        "-e",
        count_cmd
    ], capture_output=True, text=True)

    if result.returncode == 0:
        table_count = result.stdout.strip()
        log(f"Tabelas no destino: {table_count}", "SUCCESS")

    print()

    # Resumo final
    print(f"{Fore.GREEN}{'=' * 70}")
    print(f"{Fore.GREEN}✓ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print(f"{Fore.GREEN}{'=' * 70}{Style.RESET_ALL}")
    print()
    print(f"📁 Backup: {dump_file}")
    print(f"🗄️  Banco: {db}")
    print(f"🎯 Destino: {dst['host']}")
    print()
    print(f"{Fore.YELLOW}⚠️  Próximos passos:{Style.RESET_ALL}")
    print(f"   1. Teste a aplicação PerfexCRM")
    print(f"   2. Atualize a configuração para apontar para {dst['host']}")
    print(f"   3. Verifique os dados migrados")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())

# Adicionar projeto ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


init(autoreset=True)


class PerfexCRMMigrator:
    """Migrador MySQL para PerfexCRM."""

    def __init__(self, config_path: Optional[Path] = None):
        """Inicializa o migrador."""
        # Carregar configurações
        if config_path is None:
            config_path = project_root / "secrets" / "mysql_config.json"

        self.config = self._load_config(config_path)

        self.source_host = self.config['source']['host']
        self.dest_host = self.config['destination']['host']
        self.database = self.config['perfexcrm']['database']

        # Diretórios
        self.backup_dir = None
        self.dump_file = None
        self.log_file = None

        # Credenciais (carregadas do config)
        self.source_user = self.config['source']['user']
        self.source_pass = self.config['source']['password']
        self.dest_user = self.config['destination']['user']
        self.dest_pass = self.config['destination']['password']

        # Usar migration_user para tudo
        self.use_migration_user_only = True

        # Conexões
        self.source_conn = None
        self.dest_conn = None

        # Estatísticas
        self.stats = {
            'start_time': None,
            'end_time': None,
            'source_tables': 0,
            'source_size_mb': 0,
            'dest_tables': 0,
            'dest_size_mb': 0,
            'dump_size': 0,
            'errors': []
        }

    def print_header(self):
        """Imprime cabeçalho do script."""
        print(f"{Fore.BLUE}{'=' * 70}")
        print(f"{Fore.CYAN}     Migração MySQL - PerfexCRM")
        print(f"{Fore.CYAN}     Origem: {self.source_host}")
        print(f"{Fore.CYAN}     Destino: {self.dest_host}")
        print(f"{Fore.BLUE}{'=' * 70}{Style.RESET_ALL}\n")

    def _load_config(self, config_path: Path) -> Dict:
        """Carrega configurações do arquivo JSON."""
        if not config_path.exists():
            raise FileNotFoundError(
                f"Arquivo de configuração não encontrado: {config_path}\n"
                f"Crie o arquivo secrets/mysql_config.json com as credenciais."
            )

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def log(self, message: str, level: str = "INFO"):
        """Registra mensagem no log."""
        icons = {
            "INFO": f"{Fore.BLUE}ℹ️",
            "SUCCESS": f"{Fore.GREEN}✓",
            "WARNING": f"{Fore.YELLOW}⚠",
            "ERROR": f"{Fore.RED}✗",
        }

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        icon = icons.get(level, "•")

        log_msg = f"[{timestamp}] {level}: {message}"
        print(f"{icon} {message}{Style.RESET_ALL}")

        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{log_msg}\n")

    def setup_backup_directory(self):
        """Cria diretório de backup."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = project_root / "backup" / f"perfexcrm_{timestamp}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.dump_file = self.backup_dir / f"{self.database}_dump.sql"
        self.log_file = self.backup_dir / "migration.log"

        self.log(f"Diretório de backup: {self.backup_dir}", "INFO")

    def collect_credentials(self):
        """Confirma uso das credenciais do arquivo config."""
        self.log("Usando credenciais do migration_user...", "INFO")
        print()

        print(f"{Fore.CYAN}ℹ️  Credenciais carregadas do arquivo de configuração:")
        print(f"   Origem: {self.source_user}@{self.source_host}")
        print(f"   Destino: {self.dest_user}@{self.dest_host}")
        print(
            f"   ✓ Usuário migration_user será usado para todas as operações{Style.RESET_ALL}")
        print()

    def test_mysql_connection(self, host: str, user: str, password: str, db: Optional[str] = None) -> Tuple[bool, Optional[mysql.connector.connection.MySQLConnection]]:
        """Testa conexão MySQL."""
        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=db,
                charset='utf8mb4'
            )
            return True, conn
        except MySQLError as e:
            self.log(f"Erro ao conectar em {host}: {e}", "ERROR")
            return False, None

    def get_database_info(self, conn: mysql.connector.connection.MySQLConnection, database: str) -> Dict:
        """Obtém informações do banco de dados."""
        cursor = conn.cursor(dictionary=True)
        try:
            # Tamanho do banco
            cursor.execute(f"""
                SELECT ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS size_mb
                FROM information_schema.tables
                WHERE table_schema = '{database}'
            """)
            size_result = cursor.fetchone()
            size_mb = size_result['size_mb'] if size_result else 0

            # Número de tabelas
            cursor.execute(f"""
                SELECT COUNT(*) AS table_count
                FROM information_schema.tables
                WHERE table_schema = '{database}'
            """)
            count_result = cursor.fetchone()
            table_count = count_result['table_count'] if count_result else 0

            return {
                'size_mb': float(size_mb or 0),
                'table_count': int(table_count or 0)
            }
        finally:
            cursor.close()

    def verify_source_environment(self) -> bool:
        """Verifica ambiente de origem."""
        self.log("=" * 60, "INFO")
        self.log("ETAPA 1: Verificando ambiente de origem", "INFO")
        self.log("=" * 60, "INFO")

        success, conn = self.test_mysql_connection(
            self.source_host,
            self.source_user,
            self.source_pass,
            self.database
        )

        if not success:
            self.log(f"Falha ao conectar no banco {self.database}", "ERROR")
            return False

        self.source_conn = conn
        self.log(f"Conexão com {self.source_host} estabelecida", "SUCCESS")

        # Obter informações do banco
        info = self.get_database_info(conn, self.database)
        self.stats['source_tables'] = info['table_count']
        self.stats['source_size_mb'] = info['size_mb']

        self.log(f"Tamanho do banco: {info['size_mb']} MB", "INFO")
        self.log(f"Número de tabelas: {info['table_count']}", "INFO")

        return True

    def backup_database(self) -> bool:
        """Cria backup do banco de dados."""
        self.log("", "INFO")
        self.log("=" * 60, "INFO")
        self.log("ETAPA 2: Criando backup do banco", "INFO")
        self.log("=" * 60, "INFO")

        self.log(f"Iniciando dump de {self.database}...", "INFO")

        # Comando mysqldump
        cmd = [
            "mysqldump",
            f"-h{self.source_host}",
            f"-u{self.source_user}",
            f"-p{self.source_pass}",
            "--single-transaction",
            "--routines",
            "--triggers",
            "--events",
            "--quick",
            "--set-gtid-purged=OFF",
            self.database
        ]

        try:
            with open(self.dump_file, 'w', encoding='utf8') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True
                )

            if result.returncode != 0:
                self.log(f"Erro no mysqldump: {result.stderr}", "ERROR")
                return False

            # Verificar arquivo criado
            if not self.dump_file.exists():
                self.log("Arquivo de dump não foi criado", "ERROR")
                return False

            dump_size_mb = self.dump_file.stat().st_size / (1024 * 1024)
            self.stats['dump_size'] = dump_size_mb

            self.log(f"Dump criado: {self.dump_file}", "SUCCESS")
            self.log(f"Tamanho do dump: {dump_size_mb:.2f} MB", "INFO")

            # Criar backup compactado
            self.log("Compactando backup...", "INFO")
            subprocess.run(['gzip', '-c', str(self.dump_file)],
                           stdout=open(f"{self.dump_file}.gz", 'wb'),
                           check=True)

            compressed_size_mb = Path(
                f"{self.dump_file}.gz").stat().st_size / (1024 * 1024)
            self.log(
                f"Backup compactado: {compressed_size_mb:.2f} MB", "SUCCESS")

            return True

        except Exception as e:
            self.log(f"Erro ao criar backup: {e}", "ERROR")
            self.stats['errors'].append(str(e))
            return False

    def verify_destination_environment(self) -> bool:
        """Verifica ambiente de destino."""
        self.log("", "INFO")
        self.log("=" * 60, "INFO")
        self.log("ETAPA 3: Verificando ambiente de destino", "INFO")
        self.log("=" * 60, "INFO")

        success, conn = self.test_mysql_connection(
            self.dest_host,
            self.dest_user,
            self.dest_pass
        )

        if not success:
            self.log(
                f"Falha ao conectar no servidor {self.dest_host}", "ERROR")
            return False

        self.dest_conn = conn
        self.log(f"Conexão com {self.dest_host} estabelecida", "SUCCESS")

        # Verificar se banco já existe
        with conn.cursor() as cursor:
            cursor.execute(f"SHOW DATABASES LIKE '{self.database}'")
            exists = cursor.fetchone()

            if exists:
                self.log(
                    f"AVISO: Banco {self.database} já existe no destino!", "WARNING")
                confirm = input(
                    f"\n{Fore.YELLOW}Deseja SOBRESCREVER o banco existente? (digite 'SIM' para confirmar): {Style.RESET_ALL}")

                if confirm.strip() != "SIM":
                    self.log("Operação cancelada pelo usuário", "WARNING")
                    return False

                self.log("Banco existente será sobrescrito", "WARNING")

        return True

    def create_destination_database(self) -> bool:
        """Cria banco de dados no destino."""
        self.log("", "INFO")
        self.log("=" * 60, "INFO")
        self.log("ETAPA 4: Criando banco de dados no destino", "INFO")
        self.log("=" * 60, "INFO")

        try:
            with self.dest_conn.cursor() as cursor:
                # Dropar banco se existir
                cursor.execute(f"DROP DATABASE IF EXISTS `{self.database}`")
                self.dest_conn.commit()

                # Criar banco novo
                cursor.execute(f"""
                    CREATE DATABASE `{self.database}`
                    CHARACTER SET utf8mb4
                    COLLATE utf8mb4_unicode_ci
                """)
                self.dest_conn.commit()

                self.log(
                    f"Banco {self.database} criado com sucesso", "SUCCESS")
                return True

        except Exception as e:
            self.log(f"Erro ao criar banco: {e}", "ERROR")
            self.stats['errors'].append(str(e))
            return False

    def restore_database(self) -> bool:
        """Restaura banco de dados no destino."""
        self.log("", "INFO")
        self.log("=" * 60, "INFO")
        self.log("ETAPA 5: Restaurando dados no destino", "INFO")
        self.log("=" * 60, "INFO")

        self.log("Iniciando importação dos dados...", "INFO")

        cmd = [
            "mysql",
            f"-h{self.dest_host}",
            f"-u{self.dest_user}",
            f"-p{self.dest_pass}",
            self.database
        ]

        try:
            with open(self.dump_file, 'r', encoding='utf8') as f:
                result = subprocess.run(
                    cmd,
                    stdin=f,
                    stderr=subprocess.PIPE,
                    text=True
                )

            if result.returncode != 0:
                self.log(f"Erro na importação: {result.stderr}", "ERROR")
                return False

            self.log("Dados importados com sucesso", "SUCCESS")
            return True

        except Exception as e:
            self.log(f"Erro ao restaurar banco: {e}", "ERROR")
            self.stats['errors'].append(str(e))
            return False

    def configure_users(self) -> bool:
        """Configura usuários e permissões."""
        self.log("", "INFO")
        self.log("=" * 60, "INFO")
        self.log("ETAPA 6: Configurando usuários e permissões", "INFO")
        self.log("=" * 60, "INFO")

        try:
            with self.dest_conn.cursor() as cursor:
                # Dropar usuários se existirem
                self.log("Removendo usuários antigos se existirem...", "INFO")
                cursor.execute("DROP USER IF EXISTS 'perfexcrm_user'@'%'")
                cursor.execute("DROP USER IF EXISTS 'perfexcrm_view'@'%'")
                self.dest_conn.commit()

                # Criar perfexcrm_user (Read/Write)
                self.log("Criando usuário perfexcrm_user (Read/Write)...", "INFO")
                cursor.execute(f"""
                    CREATE USER 'perfexcrm_user'@'%'
                    IDENTIFIED BY '{self.perfex_user_pass}'
                """)
                cursor.execute(f"""
                    GRANT ALL PRIVILEGES ON `{self.database}`.*
                    TO 'perfexcrm_user'@'%'
                """)

                # Criar perfexcrm_view (Read Only)
                self.log("Criando usuário perfexcrm_view (Read Only)...", "INFO")
                cursor.execute(f"""
                    CREATE USER 'perfexcrm_view'@'%'
                    IDENTIFIED BY '{self.perfex_view_pass}'
                """)
                cursor.execute(f"""
                    GRANT SELECT ON `{self.database}`.*
                    TO 'perfexcrm_view'@'%'
                """)

                # Aplicar privilégios
                cursor.execute("FLUSH PRIVILEGES")
                self.dest_conn.commit()

                self.log("Usuários criados e configurados com sucesso", "SUCCESS")
                return True

        except Exception as e:
            self.log(f"Erro ao configurar usuários: {e}", "ERROR")
            self.stats['errors'].append(str(e))
            return False

    def validate_migration(self) -> bool:
        """Valida migração."""
        self.log("", "INFO")
        self.log("=" * 60, "INFO")
        self.log("ETAPA 7: Validando migração", "INFO")
        self.log("=" * 60, "INFO")

        try:
            # Reconectar ao banco de destino
            self.dest_conn.close()
            success, conn = self.test_mysql_connection(
                self.dest_host,
                self.dest_user,
                self.dest_pass,
                self.database
            )

            if not success:
                return False

            self.dest_conn = conn

            # Obter informações do destino
            info = self.get_database_info(conn, self.database)
            self.stats['dest_tables'] = info['table_count']
            self.stats['dest_size_mb'] = info['size_mb']

            self.log(
                f"Tabelas na origem: {self.stats['source_tables']}", "INFO")
            self.log(
                f"Tabelas no destino: {self.stats['dest_tables']}", "INFO")

            if self.stats['source_tables'] == self.stats['dest_tables']:
                self.log("Número de tabelas confere", "SUCCESS")
            else:
                self.log("AVISO: Número de tabelas diferente!", "WARNING")

            self.log(
                f"Tamanho na origem: {self.stats['source_size_mb']} MB", "INFO")
            self.log(
                f"Tamanho no destino: {self.stats['dest_size_mb']} MB", "INFO")

            # Testar conexão com perfexcrm_user
            self.log("", "INFO")
            self.log("Testando conexão com perfexcrm_user...", "INFO")
            success, test_conn = self.test_mysql_connection(
                self.dest_host,
                'perfexcrm_user',
                self.perfex_user_pass,
                self.database
            )

            if success:
                self.log("perfexcrm_user pode acessar o banco", "SUCCESS")
                test_conn.close()
            else:
                self.log("perfexcrm_user NÃO consegue acessar o banco", "ERROR")
                return False

            # Testar conexão com perfexcrm_view
            self.log("Testando conexão com perfexcrm_view...", "INFO")
            success, test_conn = self.test_mysql_connection(
                self.dest_host,
                'perfexcrm_view',
                self.perfex_view_pass,
                self.database
            )

            if success:
                self.log("perfexcrm_view pode acessar o banco", "SUCCESS")
                test_conn.close()
            else:
                self.log("perfexcrm_view NÃO consegue acessar o banco", "ERROR")
                return False

            return True

        except Exception as e:
            self.log(f"Erro na validação: {e}", "ERROR")
            self.stats['errors'].append(str(e))
            return False

    def print_final_report(self):
        """Imprime relatório final."""
        self.log("", "INFO")
        self.log("=" * 60, "INFO")
        self.log("MIGRAÇÃO CONCLUÍDA COM SUCESSO!", "SUCCESS")
        self.log("=" * 60, "INFO")

        print(f"\n{Fore.GREEN}✓ Resumo da Migração:{Style.RESET_ALL}")
        print(f"  Banco de dados: {Fore.CYAN}{self.database}{Style.RESET_ALL}")
        print(f"  Origem: {Fore.CYAN}{self.source_host}{Style.RESET_ALL}")
        print(f"  Destino: {Fore.CYAN}{self.dest_host}{Style.RESET_ALL}")
        print(
            f"  Tabelas migradas: {Fore.CYAN}{self.stats['dest_tables']}{Style.RESET_ALL}")
        print(
            f"  Tamanho: {Fore.CYAN}{self.stats['dest_size_mb']} MB{Style.RESET_ALL}")

        print(f"\n{Fore.GREEN}✓ Usuários configurados:{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}perfexcrm_user{Style.RESET_ALL} - Leitura e Escrita")
        print(f"  {Fore.CYAN}perfexcrm_view{Style.RESET_ALL} - Somente Leitura")

        print(f"\n{Fore.YELLOW}⚠ Arquivos salvos em:{Style.RESET_ALL}")
        print(f"  Dump SQL: {Fore.CYAN}{self.dump_file}{Style.RESET_ALL}")
        print(
            f"  Dump compactado: {Fore.CYAN}{self.dump_file}.gz{Style.RESET_ALL}")
        print(f"  Log: {Fore.CYAN}{self.log_file}{Style.RESET_ALL}")

        print(f"\n{Fore.YELLOW}⚠ PRÓXIMOS PASSOS:{Style.RESET_ALL}")
        print(f"  1. Atualize a configuração do PerfexCRM para:")
        print(f"     Host: {Fore.CYAN}{self.dest_host}{Style.RESET_ALL}")
        print(f"     Database: {Fore.CYAN}{self.database}{Style.RESET_ALL}")
        print(f"     User: {Fore.CYAN}perfexcrm_user{Style.RESET_ALL}")
        print(
            f"     Password: {Fore.CYAN}[senha configurada]{Style.RESET_ALL}")
        print(f"  2. Teste a aplicação PerfexCRM")
        print(f"  3. Verifique os logs da aplicação")
        print(f"  4. Guarde o backup em local seguro")
        print()

    def cleanup(self):
        """Fecha conexões."""
        if self.source_conn:
            self.source_conn.close()
        if self.dest_conn:
            self.dest_conn.close()

    def run(self) -> bool:
        """Executa migração completa."""
        try:
            self.stats['start_time'] = datetime.now()

            self.print_header()
            self.setup_backup_directory()
            self.collect_credentials()

            # Executar etapas
            if not self.verify_source_environment():
                return False

            if not self.backup_database():
                return False

            if not self.verify_destination_environment():
                return False

            if not self.create_destination_database():
                return False

            if not self.restore_database():
                return False

            if not self.configure_users():
                return False

            if not self.validate_migration():
                return False

            self.stats['end_time'] = datetime.now()
            duration = (self.stats['end_time'] -
                        self.stats['start_time']).total_seconds()
            self.log(f"Duração total: {duration:.2f} segundos", "INFO")

            self.print_final_report()
            return True

        except KeyboardInterrupt:
            self.log("\nMigração cancelada pelo usuário", "WARNING")
            return False
        except Exception as e:
            self.log(f"Erro inesperado: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.cleanup()


def main():
    """Função principal."""
    migrator = PerfexCRMMigrator()
    success = migrator.run()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
