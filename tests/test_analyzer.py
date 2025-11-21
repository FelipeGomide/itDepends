import pytest
from itdepends.analyzer import analyze_repository

def test_requirements_txt_lifecycle(git_repo, commit_file):
    # Commit 1
    commit_file(git_repo, "requirements.txt", "requests==1.0.0", "Initial")
    
    # Commit 2
    commit_file(git_repo, "requirements.txt", "requests==2.0.0\nflask==2.2.0", "Update")

    # Execução
    df = analyze_repository(str(git_repo))

    assert not df.empty
    
    # Pegamos o último registro
    last_record = df.iloc[-1]
    parsed = last_record["parsed_after"]
    
    # Validação: parsed é uma lista de DICTS
    requests = next(d for d in parsed if d["name"] == "requests")
    
    # Verifica se extraiu a versão corretamente do "==2.0.0"
    assert requests["version"] == "2.0.0"
    assert requests["specifier"] == "==2.0.0"