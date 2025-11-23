import os
import sys

import pandas as pd
from datetime import datetime
from tqdm import tqdm

from .utils import save_to_csv, create_results_directories
from .parsers import parse_dependency_file # importa a função de parser que o Lucca fizer

TARGET_FILES = {"pyproject.toml", "requirements.txt"}

def analyze_repository_commit_history(cloned_repo, repo_full_name):
    records = []
    
    for commit in tqdm(cloned_repo.traverse_commits(), desc="Traversing commits"):
    
        for mod in commit.modified_files:
            filename = os.path.basename(mod.new_path or "")
            
            if filename in TARGET_FILES:
                try:
                    # Chama a função que o Lucca implementou
                    parsed = parse_dependency_file(filename, mod.source_code)
                    #parsed = None # Temporário
                    
                except Exception as e:
                    # Captura erros no parsing e registra
                    print(f"Erro ao analisar o arquivo {filename} no commit {commit.hash}: {e}")
                    parsed_before = None

                for dep in parsed:
                                    
                    version_floor = None
                    for cond in dep.version_rules:
                        if cond.operator in ['==', '>=', '^']:
                            version_floor = cond.version
                            
                    if version_floor == None:
                        version_floor = '*'
                    
                    records.append({
                        "Origem": repo_full_name,
                        "Hash_Commit": commit.hash,
                        "Autor": commit.author.name,
                        "Data_Commit": commit.author_date.isoformat(),
                        "file": filename,
                        "Dependencia": dep.name, 
                        "Versao": version_floor,
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