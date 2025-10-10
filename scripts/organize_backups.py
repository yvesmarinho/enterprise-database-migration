#!/usr/bin/env python3
"""
Script para organizar e gerenciar arquivos de backup
Usado pelo Makefile target: organize-backups
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


def organize_backups():
    """Organiza arquivos de backup do projeto"""

    print("🔍 Analisando arquivos de backup...")

    # Diretórios base
    backup_base = Path("src/backup")

    # Criar estrutura de backup
    backup_dirs = {
        "dashboards": backup_base / "dashboards",
        "configs": backup_base / "configs",
        "scripts": backup_base / "scripts",
    }

    for dir_path in backup_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    # Padrões de busca para diferentes tipos de backup
    search_patterns = {
        "dashboards": ["src/dashboards/**/*.backup*"],
        "configs": ["src/config/**/*.backup*"],
        "scripts": ["scripts/**/*.backup*"],
    }

    moved_files = {key: [] for key in backup_dirs.keys()}

    # Processar cada tipo de backup
    for backup_type, patterns in search_patterns.items():
        dest_dir = backup_dirs[backup_type]

        for pattern in patterns:
            # Buscar arquivos com o padrão
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    try:
                        dest_file = dest_dir / file_path.name

                        # Se o arquivo já existe no destino, criar nome único
                        counter = 1
                        original_dest = dest_file
                        while dest_file.exists():
                            stem = original_dest.stem
                            suffix = original_dest.suffix
                            dest_file = dest_dir / f"{stem}_{counter:03d}{suffix}"
                            counter += 1

                        shutil.move(str(file_path), str(dest_file))
                        moved_files[backup_type].append(
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

    for backup_type, files in moved_files.items():
        if files:
            type_size = sum(f["size"] for f in files)
            total_size += type_size
            total_files += len(files)

            print(f"  📁 {backup_type.capitalize()}:")
            print(f"     - {len(files)} arquivos movidos")
            print(f"     - {type_size / 1024:.1f} KB total")

            # Mostrar alguns exemplos
            for file_info in files[:3]:  # Primeiros 3
                name = Path(file_info["destination"]).name
                date = file_info["mtime"].strftime("%Y-%m-%d")
                print(f"     - {name} ({date})")

            if len(files) > 3:
                print(f"     - ... e mais {len(files) - 3} arquivos")

    if total_files > 0:
        print(
            f"\\n✅ Total: {total_files} arquivos organizados ({total_size / 1024:.1f} KB)"
        )
        print(f"📁 Localização: {backup_base}")
    else:
        print("\\n📋 Nenhum arquivo de backup encontrado para organizar")

    return total_files


def list_backups():
    """Lista todos os backups organizados"""

    backup_base = Path("src/backup")

    if not backup_base.exists():
        print("❌ Diretório de backup não existe")
        return

    print("📋 Backups organizados:")

    for backup_type in ["dashboards", "configs", "scripts"]:
        backup_dir = backup_base / backup_type

        if backup_dir.exists():
            backup_files = list(backup_dir.glob("*.backup*"))

            if backup_files:
                print(
                    f"\\n📁 {backup_type.capitalize()} ({len(backup_files)} arquivos):"
                )

                # Ordenar por data de modificação
                backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

                for file_path in backup_files:
                    stat = file_path.stat()
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime)

                    size_str = (
                        f"{size:,} bytes" if size < 1024 else f"{size / 1024:.1f} KB"
                    )
                    date_str = mtime.strftime("%Y-%m-%d %H:%M")

                    print(f"   - {file_path.name:<50} {size_str:>10} {date_str}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_backups()
    else:
        organize_backups()
