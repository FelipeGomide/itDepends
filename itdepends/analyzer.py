import os
import logging
from pydriller import Repository
import pandas as pd
from itdepends.parsers import parse_dependency_file

# Configuração de log removida (correto)
logger = logging.getLogger(__name__)

TARGET_EXTENSIONS = [".toml", ".txt", ".lock", ".pip"]
TARGET_FILES_PATTERNS = ("requirements.txt", "pyproject.toml", "poetry.lock")

def analyze_repository(repo_path_or_name: str) -> pd.DataFrame:
    if os.path.exists(repo_path_or_name):
        repo_url = repo_path_or_name
        logger.info(f"Analisando local: {repo_url}")
    else:
        repo_url = f"https://github.com/{repo_path_or_name}.git"
        logger.info(f"Analisando remoto: {repo_url}")

    records = []

    repo_miner = Repository(
        repo_url,
        only_modifications_with_file_types=TARGET_EXTENSIONS
    )

    try:
        for commit in repo_miner.traverse_commits():
            
            # Compatibilidade PyDriller
            modifications = getattr(commit, "modified_files", None) or getattr(commit, "modifications", [])

            for mod in modifications:
                full_path = mod.new_path if mod.new_path else mod.old_path
                
                if not full_path:
                    continue

                filename = os.path.basename(full_path)

                if filename.endswith(TARGET_FILES_PATTERNS):
                    content_after = mod.source_code 
                    content_before = mod.source_code_before
                    
                    try:
                        deps_before = parse_dependency_file(full_path, content_before)
                        deps_after = parse_dependency_file(full_path, content_after)
                        
                        # 'deps' é uma lista de objetos complexos, método .to_dict() cuida de converter Enums para strings
                        # Pandas vai criar uma coluna do tipo "object" contendo a lista de dicts
                        parsed_before = [d.to_dict() for d in deps_before]
                        parsed_after = [d.to_dict() for d in deps_after]
                        
                    except Exception as e:
                        logger.error(f"Erro processando {full_path} no commit {commit.hash}: {e}")
                        parsed_before = []
                        parsed_after = []

                    records.append({
                        "repository": repo_path_or_name,
                        "commit_hash": commit.hash,
                        "author": commit.author.name,
                        "date": commit.author_date,
                        "file": full_path,
                        "old_content": content_before,
                        "new_content": content_after,
                        "parsed_before": parsed_before,
                        "parsed_after": parsed_after
                    })

    except Exception as e:
        logger.critical(f"Falha fatal na análise do repositório: {e}")

    expected_columns = [
        "repository", "commit_hash", "author", "date",
        "file", "old_content", "new_content",
        "parsed_before", "parsed_after"
    ]

    if not records:
        return pd.DataFrame(columns=expected_columns)

    return pd.DataFrame(records, columns=expected_columns)