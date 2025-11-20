import os
from pydriller import Repository
import pandas as pd
# from .parser import parse_dependency_file # importa a função de parser que o Lucca fizer


TARGET_FILES = {"pyproject.toml", "requirements.txt"}


def analyze_repository(repo_full_name: str):
    repo_url = f"https://github.com/{repo_full_name}.git"

    print(f"Clonando e analisando repositório: {repo_url}")

    records = []

    # PyDriller cuida do clone temporário automaticamente
    for commit in Repository(repo_url).traverse_commits():

        for mod in commit.modifications:
            filename = os.path.basename(mod.new_path or "")

            if filename in TARGET_FILES:
                # Dentro do loop de modificações
                try:
                    # Chama a função que o Lucca implementou
                    #parsed_before = parse_dependency_file(filename, before)
                    #parsed_after = parse_dependency_file(filename, after)
                except Exception as e:
                    # Captura erros no parsing e registra
                    print(f"Erro ao analisar o arquivo {filename} no commit {commit.hash}: {e}")
                    parsed_before = None
                    parsed_after = None

                records.append({
                    "repository": repo_full_name,
                    "commit_hash": commit.hash,
                    "author": commit.author.name,
                    "date": commit.author_date,
                    "file": filename,
                    "old_content": before,
                    "new_content": after,
                    "parsed_before": parsed_before,
                    "parsed_after": parsed_after
                })

    df = pd.DataFrame(records)
    return df
