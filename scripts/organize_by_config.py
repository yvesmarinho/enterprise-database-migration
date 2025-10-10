#!/usr/bin/env python3
"""
Script inteligente de organização de arquivos usando config.ini
Organiza todos os arquivos da raiz baseado na estrutura definida em config.ini
"""

import configparser
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


class ConfigBasedOrganizer:
    """Organizador baseado em configuração"""

    def __init__(self, config_file="config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.moved_files = {}
        self.skipped_files = []
        self.errors = []

        # Arquivos que NUNCA devem ser movidos da raiz
        self.protected_files = {
            'main.py',            # Controlador principal
            'config.ini',         # Configuração central
            'Makefile',           # Build system
            'README.md',          # Documentação principal
            'requirements.txt',   # Dependências Python
            'pyproject.toml',     # Configuração Python moderna
            'docker-compose.yml',  # Docker
            'Dockerfile',         # Docker
            '.env.example',       # Template de ambiente
            'activate-mcp.sh',    # Script de ativação MCP
            'setup.sh',           # Setup inicial
            'uv.lock',            # Lock file do uv
            'objetivo.yaml',      # Objetivo do projeto
            'mcp-questions.yaml'  # Configuração MCP
        }

        # Diretórios que nunca devem ser movidos
        self.protected_dirs = {
            '.git', '.vscode', '__pycache__', '.venv',
            'config', 'secrets', 'core', 'docs', 'scripts',
            'test', 'utils', 'validation', 'cleanup', 'cli',
            'components', 'orchestrators', 'logs', 'reports'
        }

    def load_config(self):
        """Carrega configuração do arquivo INI"""
        try:
            if not Path(self.config_file).exists():
                raise FileNotFoundError(
                    f"Arquivo de configuração {self.config_file} não encontrado"
                )

            self.config.read(self.config_file)
            print(f"✅ Configuração carregada de {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar configuração: {e}")
            return False

    def get_target_dir_for_file(self, file_path):
        """Determina o diretório de destino para um arquivo
        baseado nas regras
        """
        filename = file_path.name.lower()

        # Regras específicas baseadas no nome do arquivo
        categorization_rules = {
            # Scripts de migração
            r'.*migration.*\.py$': self.config.get('PATHS', 'core_dir'),
            r'.*orchestrator.*\.py$': self.config.get(
                'PATHS', 'orchestrators_dir'
            ),
            r'phase\d+.*\.py$': self.config.get('PATHS', 'core_dir'),
            r'execute.*migration.*\.py$': self.config.get('PATHS', 'core_dir'),

            # Scripts de debug e teste
            r'debug.*\.py$': self.config.get('PATHS', 'test_dir'),
            r'test.*\.py$': self.config.get('PATHS', 'test_dir'),
            r'validate.*\.py$': self.config.get('PATHS', 'validation_dir'),
            r'verify.*\.py$': self.config.get('PATHS', 'validation_dir'),
            r'investigate.*\.py$': self.config.get('PATHS', 'test_dir'),
            r'analise.*\.py$': self.config.get('PATHS', 'test_dir'),

            # Scripts de exemplo e uso
            r'exemplo.*\.py$': (
                self.config.get('PATHS', 'docs_dir') + '/examples'
            ),
            r'example.*\.py$': (
                self.config.get('PATHS', 'docs_dir') + '/examples'
            ),

            # Arquivos de documentação
            r'.*\.md$': self.config.get('PATHS', 'docs_dir'),

            # Templates de configuração
            r'.*template.*\.json$': (
                self.config.get('PATHS', 'config_dir') + '/templates'
            ),
            r'.*_template\..*$': (
                self.config.get('PATHS', 'config_dir') + '/templates'
            ),

            # Dados extraídos
            r'extracted_data.*\.json$': 'extracted_data',

            # Scripts gerados
            r'generated.*': 'generated_scripts'
        }

        # Aplicar regras de categorização
        for pattern, target_dir in categorization_rules.items():
            if re.match(pattern, filename):
                return target_dir

        # Se não encontrou regra específica, tentar por extensão
        suffix = file_path.suffix.lower()
        extension_rules = {
            '.py': self.config.get('PATHS', 'utils_dir'),    # Python
            '.sh': self.config.get('PATHS', 'scripts_dir'),  # Scripts shell
            '.json': self.config.get('PATHS', 'config_dir'),  # JSON
            '.yaml': self.config.get('PATHS', 'config_dir'),  # YAML
            '.yml': self.config.get('PATHS', 'config_dir'),   # YAML
            '.md': self.config.get('PATHS', 'docs_dir'),      # Docs
            '.txt': self.config.get('PATHS', 'docs_dir'),     # Texto
        }

        if suffix in extension_rules:
            return extension_rules[suffix]

        return None  # Não mover se não souber onde colocar

    def should_move_file(self, file_path):
        """Verifica se um arquivo deve ser movido"""
        # Verificar se está na lista de arquivos protegidos
        if file_path.name in self.protected_files:
            return False, f"Arquivo protegido: {file_path.name}"

        # Verificar se é um diretório protegido
        if file_path.is_dir() and file_path.name in self.protected_dirs:
            return False, f"Diretório protegido: {file_path.name}"

        # Verificar se já está na estrutura organizacional correta
        current_parent = file_path.parent.name
        if current_parent in self.protected_dirs:
            return False, f"Já está organizado em: {current_parent}"

        return True, "OK para mover"

    def create_directory_structure(self):
        """Cria a estrutura de diretórios baseada no config.ini"""
        dirs_to_create = []

        # Diretórios principais do config
        for key, value in self.config['PATHS'].items():
            if key.endswith('_dir'):
                dirs_to_create.append(value)

        # Diretórios adicionais específicos
        additional_dirs = [
            'extracted_data',
            'generated_scripts',
            'backup',
            self.config.get('PATHS', 'config_dir') + '/templates',
            self.config.get('PATHS', 'docs_dir') + '/examples'
        ]

        dirs_to_create.extend(additional_dirs)

        created_count = 0
        for dir_path in dirs_to_create:
            path = Path(dir_path)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    created_count += 1
                    print(f"📁 Criado: {dir_path}")
                except Exception as e:
                    self.errors.append(f"Erro ao criar {dir_path}: {e}")

        if created_count > 0:
            print(f"✅ {created_count} diretórios criados")
        else:
            print("📁 Estrutura de diretórios já existe")

    def move_file_safely(self, source, target_dir):
        """Move arquivo com verificações de segurança"""
        try:
            target_dir_path = Path(target_dir)
            target_dir_path.mkdir(parents=True, exist_ok=True)

            target_file = target_dir_path / source.name

            # Se o arquivo já existe no destino, criar nome único
            counter = 1
            original_target = target_file
            while target_file.exists():
                stem = original_target.stem
                suffix = original_target.suffix
                target_file = target_dir_path / f"{stem}_{counter:03d}{suffix}"
                counter += 1

            # Mover arquivo
            shutil.move(str(source), str(target_file))

            return target_file, None

        except Exception as e:
            return None, str(e)

    def organize_root_files(self, dry_run=False):
        """Organiza arquivos da raiz baseado na configuração"""

        if not self.load_config():
            return False

        print(f"🔍 Analisando arquivos na raiz do projeto...")

        if not dry_run:
            self.create_directory_structure()

        root_path = Path(".")
        files_to_process = []

        # Listar todos os arquivos na raiz (exceto diretórios protegidos)
        for item in root_path.iterdir():
            if item.is_file():
                files_to_process.append(item)

        print(f"📋 Encontrados {len(files_to_process)} arquivos para análise")

        # Processar cada arquivo
        for file_path in files_to_process:
            should_move, reason = self.should_move_file(file_path)

            if not should_move:
                self.skipped_files.append({
                    'file': str(file_path),
                    'reason': reason
                })
                continue

            # Determinar destino
            target_dir = self.get_target_dir_for_file(file_path)

            if not target_dir:
                self.skipped_files.append({
                    'file': str(file_path),
                    'reason': 'Sem regra de categorização'
                })
                continue

            # Registrar para relatório
            if target_dir not in self.moved_files:
                self.moved_files[target_dir] = []

            if dry_run:
                self.moved_files[target_dir].append({
                    'source': str(file_path),
                    'target': f"{target_dir}/{file_path.name}",
                    'size': file_path.stat().st_size,
                    'action': 'WOULD_MOVE'
                })
            else:
                # Mover arquivo
                target_file, error = self.move_file_safely(file_path, target_dir)

                if error:
                    self.errors.append(f"Erro ao mover {file_path}: {error}")
                else:
                    self.moved_files[target_dir].append({
                        'source': str(file_path),
                        'target': str(target_file),
                        'size': target_file.stat().st_size,
                        'action': 'MOVED'
                    })

    def generate_report(self, dry_run=False):
        """Gera relatório da organização"""
        action_verb = "SERIAM MOVIDOS" if dry_run else "MOVIDOS"
        mode_text = "SIMULAÇÃO" if dry_run else "EXECUÇÃO"

        print(f"\n{'='*60}")
        print(f"📊 RELATÓRIO DE ORGANIZAÇÃO - {mode_text}")
        print(f"{'='*60}")

        total_files = 0
        total_size = 0

        # Arquivos movidos por categoria
        if self.moved_files:
            print(f"\n✅ ARQUIVOS {action_verb}:")

            for target_dir, files in self.moved_files.items():
                if files:
                    dir_size = sum(f['size'] for f in files)
                    total_size += dir_size
                    total_files += len(files)

                    print(f"\n📁 {target_dir} ({len(files)} arquivos - {dir_size/1024:.1f} KB)")

                    for file_info in files:
                        source = Path(file_info['source']).name
                        size_kb = file_info['size'] / 1024
                        action_icon = "➡️" if not dry_run else "🔄"
                        print(f"   {action_icon} {source:<40} ({size_kb:.1f} KB)")

        # Arquivos ignorados
        if self.skipped_files:
            print(f"\n⏭️ ARQUIVOS MANTIDOS NA RAIZ ({len(self.skipped_files)}):")

            for skip_info in self.skipped_files:
                filename = Path(skip_info['file']).name
                reason = skip_info['reason']
                print(f"   🏠 {filename:<40} - {reason}")

        # Erros
        if self.errors:
            print(f"\n❌ ERROS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   🚫 {error}")

        # Resumo
        print(f"\n{'='*60}")
        print(f"📈 RESUMO:")
        print(f"   {action_verb}: {total_files} arquivos ({total_size/1024:.1f} KB)")
        print(f"   MANTIDOS: {len(self.skipped_files)} arquivos")
        print(f"   ERROS: {len(self.errors)} erros")
        print(f"{'='*60}")

        return {
            'moved_files': total_files,
            'skipped_files': len(self.skipped_files),
            'errors': len(self.errors),
            'total_size': total_size
        }

    def save_organization_log(self):
        """Salva log detalhado da organização"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"organization_log_{timestamp}.json"

        log_data = {
            'timestamp': datetime.now().isoformat(),
            'config_file': self.config_file,
            'moved_files': self.moved_files,
            'skipped_files': self.skipped_files,
            'errors': self.errors,
            'summary': {
                'total_moved': sum(len(files) for files in self.moved_files.values()),
                'total_skipped': len(self.skipped_files),
                'total_errors': len(self.errors)
            }
        }

        try:
            logs_dir = Path(self.config.get('PATHS', 'logs_dir'))
            logs_dir.mkdir(parents=True, exist_ok=True)

            log_path = logs_dir / log_file
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

            print(f"📄 Log salvo em: {log_path}")

        except Exception as e:
            print(f"⚠️ Erro ao salvar log: {e}")


def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Organização inteligente de arquivos baseada em config.ini"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Modo simulação (não move arquivos)"
    )
    parser.add_argument(
        '--config',
        default='config.ini',
        help="Arquivo de configuração (padrão: config.ini)"
    )

    args = parser.parse_args()

    print("🚀 Organizador Inteligente de Arquivos")
    print("=" * 50)

    organizer = ConfigBasedOrganizer(config_file=args.config)

    # Executar organização
    organizer.organize_root_files(dry_run=args.dry_run)

    # Gerar relatório
    summary = organizer.generate_report(dry_run=args.dry_run)

    # Salvar log (apenas se não for dry-run)
    if not args.dry_run and summary['moved_files'] > 0:
        organizer.save_organization_log()

    # Status final
    if args.dry_run:
        print("\n🔄 Simulação concluída. Use sem --dry-run para executar.")
    else:
        if summary['errors'] == 0:
            print("\n✅ Organização concluída com sucesso!")
        else:
            print(f"\n⚠️ Organização concluída com {summary['errors']} erros.")

    return 0 if summary['errors'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
