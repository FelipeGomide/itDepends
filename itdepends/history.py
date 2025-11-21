import os
import sys

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

        for mod in commit.modified_files:
            filename = os.path.basename(mod.new_path or "")
            print(filename)

            if filename in TARGET_FILES:
                # Dentro do loop de modificações
                try:
                    #print(filename, mod.source_code)
                    
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

def create_results_directories(project_folder_name):
    nested_path = f"results/{project_folder_name}"
    
    os.makedirs(nested_path, exist_ok=True)

def save_to_csv(df, repo_name):
    folder_repo_name = repo_name.replace('/', '_')
    
    create_results_directories(folder_repo_name)
    
    output_file = f"results/{repo_name.replace('/', '_')}/data.csv"
    
    df.to_csv(output_file, index=False)
    
    return output_file

def main():
    if len(sys.argv) < 2:
        sys.exit(1)

    repo_name = sys.argv[1]

    df = analyze_repository(repo_name)

    print(f"\nTotal de commits relevantes: {len(df)}")
    print(df.head())

    # output_file = f"results/{repo_name.replace('/', '_')}/{repo_name.replace('/', '_')}_dependency_changes.csv"
    # df.to_csv(output_file, index=False)
    
    output_file = save_to_csv(df, repo_name)

    print(f"\nArquivo salvo: {output_file}")

if __name__ == "__main__":
    main()
