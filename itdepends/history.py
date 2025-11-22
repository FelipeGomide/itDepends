import os
import sys

import pandas as pd

from .utils import save_to_csv, create_results_directories
# from .parser import parse_dependency_file # importa a função de parser que o Lucca fizer

TARGET_FILES = {"pyproject.toml", "requirements.txt"}

def analyze_repository_commit_history(cloned_repo, repo_full_name):
    records = []

    for commit in cloned_repo.traverse_commits():

        for mod in commit.modified_files:
            filename = os.path.basename(mod.new_path or "")
            print(filename)

            if filename in TARGET_FILES:
                try:
                    # Chama a função que o Lucca implementou
                    # parsed = parse_dependency_file(filename, before)
                    parsed = None # Temporário
                    
                except Exception as e:
                    # Captura erros no parsing e registra
                    print(f"Erro ao analisar o arquivo {filename} no commit {commit.hash}: {e}")
                    parsed_before = None

                records.append({
                    "repository": repo_full_name,
                    "commit_hash": commit.hash,
                    "author": commit.author.name,
                    "date": commit.author_date,
                    "file": filename,
                    # "old_content": before,
                    # "new_content": after,
                    "dependencies": parsed,
                    #"parsed_after": parsed_after
                })

    df = pd.DataFrame(records)
    return df

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    repo_name = sys.argv[1]

    df = analyze_repository_commit_history(repo_name)

    print(f"\nTotal de commits relevantes: {len(df)}")
    print(df.head())
    
    output_file = save_to_csv(df, repo_name)

    print(f"\nArquivo salvo: {output_file}")

if __name__ == "__main__":
    main()