import pytest
import subprocess
import os
from pathlib import Path

@pytest.fixture
def git_repo(tmp_path):
    """
    Fixture global: Cria um repositório git temporário para testes de integração.
    Disponível automaticamente para qualquer teste na pasta tests/.
    """
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "bot@test.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Bot"], cwd=tmp_path, check=True, capture_output=True)
    
    return tmp_path

@pytest.fixture
def commit_file():
    """
    Retorna uma FUNÇÃO helper para commitar arquivos.
    """
    def _commit(repo_path: Path, filename: str, content: str, msg: str = "update"):
        path = repo_path / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.run(["git", "add", filename], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", msg], cwd=repo_path, check=True, capture_output=True)
    
    return _commit