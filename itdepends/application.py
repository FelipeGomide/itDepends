from history import analyze_repository_commit_history
from deprecation import full_deprecation_analysis
from utils import create_results_directories, save_to_csv


from pydriller import Repository

def run(repo_name, max_months = 12):
    repo_url = f"https://github.com/{repo_name}.git"
    
    try:
        cloned_repo = Repository(repo_url, order='date-order')
        
        history_df = analyze_repository_commit_history(cloned_repo, repo_name)
        
        deprecation_df = full_deprecation_analysis(cloned_repo, max_months)
        
        create_results_directories(repo_name)
        save_to_csv(history_df, 'history', repo_name)
        save_to_csv(deprecation_df, 'deprecation', repo_name)
        
        # chamar o gerador de saida do Lucas
        
        return 0
    
    except Exception as e:
        return 1