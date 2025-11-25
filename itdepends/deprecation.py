from .integrations import GitHubClient, PyPiClient
import pandas as pd

import os

from .parsers import parse_dependency_file
from .utils import file_is_suitable

TARGET_FILES = {"pyproject.toml", "requirements.txt"}

def full_deprecation_analysis(repo_name, max_months):
    dependency_files = get_dependency_files(repo_name)
    
    dependencies = {}
    for file in dependency_files:
        deps = parse_dependency_file(filename=file['name'], content=file['content'])
        for dep in deps:
            dependencies[dep.name] = dep

    dependencies = list(dependencies.values())
    
    results = []
    for dependency in dependencies:
        archived, repo, inactive, status, available = check_deprecation(dependency.name, max_months)
        
        results.append({
            'Nome': dependency.name,
            'Github_encontrado': repo,
            'Arquivado': archived,
            'Inativo': inactive,
            'Status (PyPi)': status,
        })
    
    df = pd.DataFrame(results)
    return df
    
TARGET_FILES = {"pyproject.toml", "requirements.txt"}

def get_dependency_files(repo_name):
    gh = GitHubClient()
    
    branch = gh.get_default_branch_name(repo_name)
    tree = gh.get_file_tree(repo_name, branch)
    
    dep_files = []
    
    for file in tree:
        name = file.get('path')

        dirname = os.path.dirname(name)
        filename = os.path.basename(name)
        
        #if file_is_suitable(dirname, filename):
        if filename in TARGET_FILES:
            url = file.get('url')
            
            contents = gh.get_file_contents(url)
            dep_files.append({"name": filename, "content": contents})
            
    return dep_files

def check_deprecation(package_name, max_months):
    repo = []
    repo, status = get_dependency_pypi_info(package_name)
    
    if status == False:
        return False, None, False, False, False

    archived, inactive, available = get_github_info(repo, max_months)
    
    return archived, repo, inactive, status, available
    
def get_dependency_pypi_info(package_name):
    pypi = PyPiClient()

    success_gh, repo_name = pypi.get_github_repo_name(package_name)
    succes_pypi, stage = pypi.verify_development_status(package_name)
    
    if success_gh and succes_pypi:
        return repo_name, stage

    return "no_repo_found", False

def get_github_info(repo_name, max_months):
    gh = GitHubClient()
    
    if gh.verify_repo_existance(repo_name):
        archived = gh.verify_archived(repo_name)
        inactive = gh.verify_inactivity(repo_name, max_months)
    
        return archived, inactive, True
    
    return False, False, False