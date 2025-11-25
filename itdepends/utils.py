import os

def create_results_directories(repo_name):
    nested_path = f"results/{repo_name.replace('/', '_')}"
    
    os.makedirs(nested_path, exist_ok=True)

def save_to_csv(df, output_name, repo_name):
    folder_repo_name = repo_name.replace('/', '_')
    
    create_results_directories(folder_repo_name)
    
    output_file = f"results/{repo_name.replace('/', '_')}/{output_name}.csv"
    
    df.to_csv(output_file, index=False)
    
    return output_file

def diff_in_months(d1, d2):
    return (d2.year - d1.year) * 12 + d2.month - d1.month

def file_is_suitable(dirname, filename):
    if "test" in dirname: return False

    if filename.endswith('.toml'): return True

    if 'requirements' in filename: return True

    return False