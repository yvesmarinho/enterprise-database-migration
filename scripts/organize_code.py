#!/usr/bin/env python3
"""
Script para organizar e gerenciar arquivos de código
Usado pelo Makefile target: organize-code
"""

import shutil
from pathlib import Path
from datetime import datetime


def organize_code():
    """Organiza arquivos de código do projeto"""

    print("💻 Analisando arquivos de código...")

    # Diretório de destino
    scripts_base = Path("scripts")

    # Criar estrutura de código
    code_dirs = {
        "dashboard": scripts_base / "dashboards",
        "backup": scripts_base / "backup",
        "config": scripts_base / "config",
        "general": scripts_base / "general",
    }

    for dir_path in code_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    # Padrões de busca para diferentes tipos de código
    search_patterns = {"general": ["./*.py", "./*.sh"]}

    # Arquivos que devem permanecer na raiz ou em locais específicos
    keep_in_place = {
        "activate-mcp.sh",  # Script de ativação MCP - deve ficar na raiz
        "setup.py",
        "requirements.txt",
    }

    moved_files = {key: [] for key in code_dirs.keys()}

    # Processar arquivos de código
    for code_type, patterns in search_patterns.items():
        for pattern in patterns:
            # Buscar arquivos com o padrão
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    # Pular arquivos que devem ficar no local atual
                    if file_path.name in keep_in_place:
                        print(f"⏭️ Mantendo {file_path.name} na localização atual")
                        continue

                    # Pular se já está em scripts/
                    if "scripts" in str(file_path):
                        continue

                    try:
                        # Determinar subdiretório baseado no nome do arquivo
                        final_dest_dir = categorize_code(file_path, code_dirs)
                        dest_file = final_dest_dir / file_path.name

                        # Se o arquivo já existe no destino, criar nome único
                        counter = 1
                        original_dest = dest_file
                        while dest_file.exists():
                            stem = original_dest.stem
                            suffix = original_dest.suffix
                            dest_file = final_dest_dir / f"{stem}_{counter:03d}{suffix}"
                            counter += 1

                        shutil.move(str(file_path), str(dest_file))

                        # Tornar executável se for .sh
                        if dest_file.suffix == ".sh":
                            dest_file.chmod(0o755)

                        # Categorizar para relatório
                        category = get_category_name(final_dest_dir, code_dirs)
                        moved_files[category].append(
                            {
                                "original": str(file_path),
                                "destination": str(dest_file),
                                "size": dest_file.stat().st_size,
                                "mtime": datetime.fromtimestamp(
                                    dest_file.stat().st_mtime
                                ),
                            }
                        )

                    except Exception as e:
                        print(f"⚠️ Erro ao mover {file_path}: {e}")

    # Relatório final
    print("📊 Resumo da organização:")
    total_files = 0
    total_size = 0

    for code_type, files in moved_files.items():
        if files:
            type_size = sum(f["size"] for f in files)
            total_size += type_size
            total_files += len(files)

            print(f"  📁 {code_type.capitalize()}:")
            print(f"     - {len(files)} arquivos movidos")
            print(f"     - {type_size / 1024:.1f} KB total")

            # Mostrar alguns exemplos
            for file_info in files[:3]:  # Primeiros 3
                name = Path(file_info["destination"]).name
                date = file_info["mtime"].strftime("%Y-%m-%d")
                ext = (
                    "🐍"
                    if name.endswith(".py")
                    else "📜"
                    if name.endswith(".sh")
                    else "📄"
                )
                print(f"     - {ext} {name} ({date})")

            if len(files) > 3:
                print(f"     - ... e mais {len(files) - 3} arquivos")

    if total_files > 0:
        print(
            f"\\n✅ Total: {total_files} arquivos organizados ({total_size / 1024:.1f} KB)"
        )
        print(f"📁 Localização: {scripts_base}")
    else:
        print("\\n📋 Nenhum arquivo de código encontrado para organizar")

    return total_files


def categorize_code(file_path, code_dirs):
    """Categoriza código baseado no nome do arquivo"""

    file_name = file_path.name.lower()

    # Regras de categorização baseadas no nome
    if any(
        keyword in file_name
        for keyword in ["dashboard", "grafana", "mysql", "postgres", "wfdb"]
    ):
        return code_dirs["dashboard"]
    elif any(keyword in file_name for keyword in ["backup", "organize"]):
        return code_dirs["backup"]
    elif any(keyword in file_name for keyword in ["config", "setup", "install"]):
        return code_dirs["config"]
    else:
        return code_dirs["general"]


def get_category_name(dest_dir, code_dirs):
    """Retorna o nome da categoria baseado no diretório"""
    for category, path in code_dirs.items():
        if dest_dir == path:
            return category
    return "general"


def list_code():
    """Lista todos os arquivos de código organizados"""

    scripts_base = Path("scripts")

    if not scripts_base.exists():
        print("❌ Diretório de scripts não existe")
        return

    print("💻 Código organizado:")

    for code_type in ["dashboards", "backup", "config", "general"]:
        code_dir = scripts_base / code_type

        if code_dir.exists():
            code_files = list(code_dir.glob("*.py")) + list(code_dir.glob("*.sh"))

            if code_files:
                print(f"\\n📁 {code_type.capitalize()} ({len(code_files)} arquivos):")

                # Ordenar por data de modificação
                code_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

                for file_path in code_files:
                    stat = file_path.stat()
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime)

                    # Ícone baseado na extensão
                    icon = (
                        "🐍"
                        if file_path.suffix == ".py"
                        else "📜"
                        if file_path.suffix == ".sh"
                        else "📄"
                    )

                    # Verificar se é executável
                    executable = "⚡" if (stat.st_mode & 0o111) else "📄"

                    size_str = (
                        f"{size:,} bytes" if size < 1024 else f"{size / 1024:.1f} KB"
                    )
                    date_str = mtime.strftime("%Y-%m-%d %H:%M")

                    print(
                        f"   - {icon}{executable} {file_path.name:<40} {size_str:>10} {date_str}"
                    )


def show_root_scripts():
    """Mostra scripts que ficaram na raiz"""

    print("\\n🏠 Scripts mantidos na raiz:")

    root_scripts = list(Path(".").glob("*.py")) + list(Path(".").glob("*.sh"))

    if root_scripts:
        for script in root_scripts:
            stat = script.stat()
            size_str = (
                f"{stat.st_size / 1024:.1f} KB"
                if stat.st_size >= 1024
                else f"{stat.st_size} bytes"
            )
            icon = (
                "🐍"
                if script.suffix == ".py"
                else "📜"
                if script.suffix == ".sh"
                else "📄"
            )
            executable = "⚡" if (stat.st_mode & 0o111) else ""

            print(f"   - {icon}{executable} {script.name} ({size_str})")
    else:
        print("   - Nenhum script na raiz")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_code()
        show_root_scripts()
    else:
        organize_code()
