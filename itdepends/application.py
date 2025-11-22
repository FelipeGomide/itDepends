from .history import analyze_repository_commit_history
from .deprecation import full_deprecation_analysis
from .utils import create_results_directories, save_to_csv
from .report import get_template_padrao, gerar_relatorio_dependencias

from datetime import datetime
from dateutil.relativedelta import relativedelta

import click
from pydriller import Repository

def run(repo_name, path=None, since_months = 12, max_months = 12):
    repo_url = f"https://github.com/{repo_name}.git"
    
    if path:
        repo_origin = path
    else:
        repo_origin = repo_url
        
    try:
        since_date = datetime.now() - relativedelta(months= since_months)
        
        cloned_repo = Repository(repo_origin, since=since_date,
                                only_modifications_with_file_types=['.txt','.toml', '.pip'])
                
        click.echo('Evaluating commits history.')
        history_df = analyze_repository_commit_history(cloned_repo, repo_name)
        
        click.echo('Analyzing last version dependencies.')
        #deprecation_df = full_deprecation_analysis(cloned_repo, max_months)
        
        create_results_directories(repo_name)
        save_to_csv(history_df, 'history', repo_name)
        #save_to_csv(deprecation_df, 'deprecation', repo_name)
        
        # chamar o gerador de saida do Lucas
        
        template = get_template_padrao()
        
        print(history_df["Data_Commit"])
        
        gerar_relatorio_dependencias(history_df,
                                     nome_projeto=repo_name,
                                     template_html=template,
                                     output_path=f'results/{repo_name.replace('/', '_')}/report.html')
        
        return 0
    
    except Exception as e:
        print(e)
        return 1