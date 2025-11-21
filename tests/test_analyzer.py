import pytest
import pandas as pd
from itdepends.analyzer import analyze_repository

# Teste Ciclo de vida básico (Criação e Atualização)
def test_analyzer_requirements_lifecycle(git_repo, commit_file):
    # Commit 1: Criação
    commit_file(git_repo, "requirements.txt", "requests==1.0.0", "Add reqs")
    
    # Commit 2: Modificação (Upgrade)
    commit_file(git_repo, "requirements.txt", "requests==2.0.0\nflask==2.2.0", "Upgrade and Add Flask")

    # Executa a análise
    df = analyze_repository(str(git_repo))

    assert not df.empty
    assert len(df) == 2 # Esperamos 2 registros (um para cada commit que tocou no arquivo)

    # Verifica o último commit (Modificação)
    last_row = df.iloc[-1]
    
    # parsed_after deve conter requests v2 e flask
    deps_after = last_row["parsed_after"]
    assert len(deps_after) == 2
    
    # Helpers para buscar na lista de dicionários
    requests = next(d for d in deps_after if d["name"] == "requests")
    flask = next(d for d in deps_after if d["name"] == "flask")

    # VALIDAÇÃO CRÍTICA: Conferindo se o to_dict() do models.py funcionou
    assert requests["pinned_version"] == "2.0.0"  # O modelo calcula isso
    assert requests["raw_specifier"] == "==2.0.0"
    
    assert flask["pinned_version"] == "2.2.0"

# Teste Suporte a múltiplos arquivos (Requirements + Poetry)
def test_analyzer_supports_multiple_formats(git_repo, commit_file):
    # Commit 1: requirements.txt
    commit_file(git_repo, "requirements.txt", "django==4.0", "Add django")
    
    # Commit 2: pyproject.toml
    toml_content = """
    [tool.poetry.dependencies]
    fastapi = "^0.95"
    """
    commit_file(git_repo, "pyproject.toml", toml_content, "Add poetry")

    df = analyze_repository(str(git_repo))

    # Filtra as linhas pelo nome do arquivo
    req_row = df[df["file"] == "requirements.txt"].iloc[0]
    toml_row = df[df["file"] == "pyproject.toml"].iloc[0]

    # Valida Requirements
    deps_req = req_row["parsed_after"]
    assert deps_req[0]["name"] == "django"
    assert deps_req[0]["dependency_type"] == "package" # Enum convertido para string

    # Valida TOML
    deps_toml = toml_row["parsed_after"]
    fastapi = deps_toml[0]
    assert fastapi["name"] == "fastapi"
    assert fastapi["raw_specifier"] == "^0.95"
    # Nota: ^0.95 não gera pinned_version pois não é "==", está correto ser None
    assert fastapi["pinned_version"] is None 

# Teste Remoção de Arquivo
def test_analyzer_handles_file_deletion(git_repo, commit_file):
    # Commit 1: Cria
    commit_file(git_repo, "requirements.txt", "black==23.1.0", "Add black")
    
    # Commit 2: Deleta arquivo (simulando via rm do git)
    import subprocess
    subprocess.run(["git", "rm", "requirements.txt"], cwd=git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "Remove deps"], cwd=git_repo, check=True)

    df = analyze_repository(str(git_repo))
    
    # O último registro deve representar a deleção
    deletion_row = df.iloc[-1]
    
    # parsed_before deve ter dados, parsed_after deve ser vazio
    assert len(deletion_row["parsed_before"]) == 1
    assert len(deletion_row["parsed_after"]) == 0

# Teste Arquivos Malformados (Robustez)
def test_analyzer_resilience_to_bad_files(git_repo, commit_file):
    # Cria um TOML totalmente quebrado
    commit_file(git_repo, "pyproject.toml", "Isto não é um TOML válido [", "Bad TOML")

    df = analyze_repository(str(git_repo))

    assert not df.empty
    row = df.iloc[0]
    
    # Não deve crashar, apenas retornar lista vazia e logar erro (capturado pelo caplog se quiséssemos testar)
    assert row["parsed_after"] == []
    assert row["file"] == "pyproject.toml"

# Teste Repositório Vazio ou Sem Arquivos de Interesse
def test_analyzer_empty_or_ignored_repo(git_repo, commit_file):
    commit_file(git_repo, "README.md", "# Hello", "Init")
    
    df = analyze_repository(str(git_repo))
    
    # Deve retornar DataFrame vazio, mas COM as colunas corretas
    assert df.empty
    assert "parsed_after" in df.columns
    assert "commit_hash" in df.columns