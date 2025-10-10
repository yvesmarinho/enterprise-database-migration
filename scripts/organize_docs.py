#!/usr/bin/env python3
"""
Script para organizar e gerenciar arquivos de documentação
Usado pelo Makefile target: organize-docs
"""

import shutil
from pathlib import Path
from datetime import datetime


def organize_docs():
    """Organiza arquivos de documentação do projeto"""

    print("📚 Analisando arquivos de documentação...")

    # Diretório de destino
    docs_base = Path("src/docs")

    # Criar estrutura de documentação
    doc_dirs = {
        "dashboards": docs_base / "dashboards",
        "guides": docs_base / "guides",
        "reports": docs_base / "reports",
        "general": docs_base / "general",
    }

    for dir_path in doc_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)

    # Padrões de busca para diferentes tipos de documentação
    search_patterns = {
        "dashboards": ["src/dashboards/**/*.md", "src/dashboards/**/*.txt"],
        "general": ["./*.md", "./*.txt"],
    }

    # Arquivos que devem permanecer na raiz
    keep_in_root = {"README.md", "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md"}

    moved_files = {key: [] for key in doc_dirs.keys()}

    # Processar cada tipo de documento
    for doc_type, patterns in search_patterns.items():
        dest_dir = doc_dirs[doc_type]

        for pattern in patterns:
            # Buscar arquivos com o padrão
            for file_path in Path(".").glob(pattern):
                if file_path.is_file():
                    # Pular arquivos que devem ficar na raiz
                    if file_path.name in keep_in_root:
                        continue

                    # Pular se já está em src/docs
                    if "src/docs" in str(file_path):
                        continue

                    try:
                        # Determinar subdiretório baseado no conteúdo/nome
                        final_dest_dir = categorize_document(file_path, doc_dirs)
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

                        # Categorizar para relatório
                        category = get_category_name(final_dest_dir, doc_dirs)
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

    for doc_type, files in moved_files.items():
        if files:
            type_size = sum(f["size"] for f in files)
            total_size += type_size
            total_files += len(files)

            print(f"  📁 {doc_type.capitalize()}:")
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
        print(f"📁 Localização: {docs_base}")
    else:
        print("\\n📋 Nenhum arquivo de documentação encontrado para organizar")

    return total_files


def categorize_document(file_path, doc_dirs):
    """Categoriza documento baseado no nome e localização"""

    file_name = file_path.name.lower()
    file_content_preview = ""

    try:
        # Ler primeiras linhas para categorização
        with open(file_path, "r", encoding="utf-8") as f:
            file_content_preview = f.read(500).lower()
    except:
        pass

    # Regras de categorização
    if any(keyword in file_name for keyword in ["dashboard", "grafana", "prometheus"]):
        return doc_dirs["dashboards"]
    elif any(
        keyword in file_name for keyword in ["guide", "template", "how-to", "tutorial"]
    ):
        return doc_dirs["guides"]
    elif any(
        keyword in file_name for keyword in ["report", "analysis", "metric", "error"]
    ):
        return doc_dirs["reports"]
    elif any(
        keyword in file_content_preview for keyword in ["dashboard", "grafana", "query"]
    ):
        return doc_dirs["dashboards"]
    elif any(
        keyword in file_content_preview for keyword in ["guide", "tutorial", "how to"]
    ):
        return doc_dirs["guides"]
    else:
        return doc_dirs["general"]


def get_category_name(dest_dir, doc_dirs):
    """Retorna o nome da categoria baseado no diretório"""
    for category, path in doc_dirs.items():
        if dest_dir == path:
            return category
    return "general"


def list_docs():
    """Lista todos os documentos organizados"""

    docs_base = Path("src/docs")

    if not docs_base.exists():
        print("❌ Diretório de documentos não existe")
        return

    print("📚 Documentação organizada:")

    for doc_type in ["dashboards", "guides", "reports", "general"]:
        doc_dir = docs_base / doc_type

        if doc_dir.exists():
            doc_files = list(doc_dir.glob("*.md")) + list(doc_dir.glob("*.txt"))

            if doc_files:
                print(f"\\n📁 {doc_type.capitalize()} ({len(doc_files)} arquivos):")

                # Ordenar por data de modificação
                doc_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

                for file_path in doc_files:
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
        list_docs()
    else:
        organize_docs()
