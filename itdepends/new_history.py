import logging
import os
import sys
import csv
from datetime import datetime, timezone
from typing import Iterator, Dict, Any
import pandas as pd
from pydriller import Repository

from .parsers import parse_dependency_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

CSV_HEADERS = [
    # Metadados do Commit
    "repository", "commit_hash", "author_name", "author_email", "date_utc", 
    "file_name", "change_type", 
    
    # Dados da Dependência 
    "dep_name", "dep_version_pinned", "dep_raw_specifier", "dep_type", "dep_category",
    "dep_source_url",   
    "dep_source_path",  
    "dep_git_ref",      
    "dep_marker",       
    "dep_extras"        
]

def _sanitize_str(val: Any) -> str:
    """Limpa strings para evitar quebra de CSV (remove newlines/tabs)"""
    if val is None:
        return ""
    return str(val).replace('\n', ' ').replace('\r', '').replace('\t', ' ').strip()

def is_dependency_file(filename: str) -> bool:
    """
    Verifica se o arquivo é um manifesto de dependência suportado.
    """
    if filename in {"pyproject.toml", "poetry.lock"}:
        return True
    
    # Variações de requirements
    if "requirements" in filename and (filename.endswith(".txt") or filename.endswith(".pip")):
        return True
        
    return False

def extract_dependencies_from_commit(repo_path: str) -> Iterator[Dict[str, Any]]:
    """
    Generator otimizado e normalizado.
    """
    # - only_no_merge=True: Ignora commits de merge 
    # - order='reverse': Começa do MAIS RECENTE para o mais antigo
    repo_mining = Repository(
        path_to_repo=repo_path,
        only_no_merge=True,
        order='reverse'
    )

    logger.info(f"Iniciando varredura (REVERSA) em: {repo_path}")
    
    for commit in repo_mining.traverse_commits():
        
        commit_date_utc = commit.author_date.astimezone(timezone.utc).isoformat()

        for mod in commit.modified_files:
            filename = os.path.basename(mod.new_path or "")
            
            if not is_dependency_file(filename):
                continue
            
            if mod.change_type.name == 'DELETE':
                continue

            try:
                content = mod.source_code
                
                if not content:
                    continue

                if len(content) > MAX_FILE_SIZE_BYTES:
                     logger.warning(f"Arquivo {filename} excede limite seguro ({len(content)/1024/1024:.2f} MB). Pulando.")
                     continue
                
                dependencies_objects = parse_dependency_file(filename, content)

                for dep in dependencies_objects:
                    dep_dict = dep.to_dict()
                    
                    raw_extras = dep_dict.get("extras_requested")
                    if raw_extras is None:
                        raw_extras = []
                    extras_str = ",".join(raw_extras)

                    yield {
                        "repository": repo_path,
                        "commit_hash": commit.hash,
                        "author_name": _sanitize_str(commit.author.name),
                        "author_email": _sanitize_str(commit.author.email),
                        "date_utc": commit_date_utc,
                        "file_name": filename,
                        "change_type": mod.change_type.name,
                        "dep_name": _sanitize_str(dep_dict.get("name")),
                        "dep_version_pinned": _sanitize_str(dep_dict.get("pinned_version")),
                        "dep_raw_specifier": _sanitize_str(dep_dict.get("raw_specifier")),
                        "dep_type": _sanitize_str(dep_dict.get("dependency_type")),
                        "dep_category": _sanitize_str(dep_dict.get("category")),
                        "dep_source_url": _sanitize_str(dep_dict.get("source_url")),
                        "dep_source_path": _sanitize_str(dep_dict.get("source_path")),
                        "dep_git_ref": _sanitize_str(dep_dict.get("git_ref")),
                        "dep_marker": _sanitize_str(dep_dict.get("marker")),
                        "dep_extras": _sanitize_str(extras_str)
                    }

            except UnicodeDecodeError:
                logger.warning(f"Erro de encoding: {filename} @ {commit.hash[:7]}")
            except Exception as e:
                logger.error(f"Erro de parser: {filename} @ {commit.hash[:7]} -> {e}")

def analyze_repository_stream(repo_path: str, output_csv_path: str) -> pd.DataFrame:
    """
    Processa e salva ao mesmo tempo.
    """
    output_dir = os.path.dirname(output_csv_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_csv_path, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()

        count = 0
        logger.info("Extraindo dependências...")
        
        for record in extract_dependencies_from_commit(repo_path):
            writer.writerow(record)
            count += 1
            
            if count % 100 == 0:
                print(f"\rRegistros processados: {count}", end="", flush=True)

    print("")

    if count == 0:
        logger.warning("Nenhuma dependência encontrada (verifique se o repo possui arquivos pyproject.toml ou requirements.txt modificados no histórico analisado).")
        return pd.DataFrame()

    logger.info(f"Extração concluída. {count} registros salvos em disco.")
    
    try:
        df = pd.read_csv(output_csv_path, parse_dates=['date_utc'])
        return df
    except Exception:
        return pd.DataFrame()

def main():
    if len(sys.argv) < 2:
        print("Uso: python history.py <caminho_do_repo>")
        sys.exit(1)

    repo_path = sys.argv[1]
    repo_name = os.path.basename(os.path.normpath(repo_path))
    output_filename = f"{repo_name}_history.csv"

    try:
        df = analyze_repository_stream(repo_path, output_filename)
        
        if not df.empty:
            print("\n--- Resumo da Análise ---")
            print(f"Total de Registros: {len(df)}")
            print(f"Arquivo salvo em: {os.path.abspath(output_filename)}")
            print(df.head())
        
    except KeyboardInterrupt:
        logger.info("\nOperação interrompida pelo usuário.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()