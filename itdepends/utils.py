import os

def create_results_directories(project_folder_name):
    nested_path = f"results/{project_folder_name}"
    
    os.makedirs(nested_path, exist_ok=True)

def save_to_csv(df, output_name, repo_name):
    folder_repo_name = repo_name.replace('/', '_')
    
    create_results_directories(folder_repo_name)
    
    output_file = f"results/{repo_name.replace('/', '_')}/{output_name}.csv"
    
    df.to_csv(output_file, index=False)
    
    return output_file