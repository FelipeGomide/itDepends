from .integrations import GitHubClient, PyPiClient
import pandas as pd

TARGET_FILES = {"pyproject.toml", "requirements.txt"}

def full_deprecation_analysis(cloned_repo, max_months):
    
    commit = list(cloned_repo.traverse_commits())[-1]
    
    dependencies = []
    
    for modification in commit.modified_files:
        file_name = modification.new_path if modification.new_path else modification.old_path
        
        if file_name in TARGET_FILES and modification.change_type.name != 'DELETE':
            file_content = modification.source_code
            
            # Chama a função que o Lucca implementou
            # parsed = parse_dependency_file(filename, before)
            
            #dependencies.append({name: parsed.name,
            #                      })
            
    for dependency in dependencies:
        archived, inactive = check_deprecation(dependency.name, max_months)
        
        dependency['archived'] = archived
        dependency['inactive'] = inactive 
    
    df = pd.DataFrame(dependencies)
    return df
    

def check_deprecation(package_name, max_months):
    github_repo, status = get_dependency_pypi_info(package_name)
    
    archived, inactive = get_github_info(github_repo, max_months)
    
    return archived, inactive
    
def get_dependency_pypi_info(package_name):
    pypi = PyPiClient()
    
    success, repo_name = pypi.get_github_repo_name(package_name)
    stage = pypi.verify_development_status(package_name)
    
    if success:
        return repo_name, stage
    
    return "no_repo_found", stage

def get_github_info(repo_name, max_months):
    gh = GitHubClient()
    
    if gh.verify_repo_existance(repo_name):
        archived = gh.verify_archived(repo_name)
        inactive = gh.verify_inactivity(repo_name, max_months)
        
    return archived, inactive