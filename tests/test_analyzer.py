import pandas as pd
from unittest.mock import MagicMock, patch
import pytest

from itdepends.history import (
    analyze_repository_commit_history,
    TARGET_FILES,
)
# troque "yourmodule" pelo nome real do pacote


# ------------------------------------------------------
# Helpers para criar objetos fake
# ------------------------------------------------------
def make_fake_mod(path):
    mod = MagicMock()
    mod.new_path = path
    return mod

def make_fake_commit(hash, author_name, date, modified_files):
    commit = MagicMock()
    commit.hash = hash
    commit.author.name = author_name
    commit.author_date = date
    commit.modified_files = modified_files
    return commit


# ------------------------------------------------------
# TESTE 1: Deve registrar commits com arquivos relevantes
# ------------------------------------------------------
def test_analyze_repository_with_target_files():
    # Commit com pyproject.toml
    commit1 = make_fake_commit(
        "abc123",
        "Alice",
        "2024-01-01",
        [make_fake_mod("pyproject.toml")]
    )

    # Commit com arquivo irrelevante
    commit2 = make_fake_commit(
        "def456",
        "Bob",
        "2024-01-02",
        [make_fake_mod("README.md")]
    )

    repo = MagicMock()
    repo.traverse_commits.return_value = [commit1, commit2]

    df = analyze_repository_commit_history(repo, "user/repo")

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1               # só o pyproject importa
    assert df.iloc[0]["file"] == "pyproject.toml"
    assert df.iloc[0]["commit_hash"] == "abc123"
    assert df.iloc[0]["author"] == "Alice"
    assert df.iloc[0]["repository"] == "user/repo"


# ------------------------------------------------------
# TESTE 2: Nenhum commit possui arquivos relevantes
# ------------------------------------------------------
def test_analyze_repository_no_target_files():
    commit = make_fake_commit(
        "zzz999",
        "Charles",
        "2024-01-03",
        [make_fake_mod("other.txt")]
    )

    repo = MagicMock()
    repo.traverse_commits.return_value = [commit]

    df = analyze_repository_commit_history(repo, "repo/x")

    assert len(df) == 0


# ------------------------------------------------------
# TESTE 3: Mesmo arquivo aparece em vários commits
# ------------------------------------------------------
def test_multiple_relevant_commits():
    commit1 = make_fake_commit(
        "111",
        "Ana",
        "2024-01-10",
        [make_fake_mod("requirements.txt")]
    )
    commit2 = make_fake_commit(
        "222",
        "Ana",
        "2024-01-11",
        [make_fake_mod("requirements.txt")]
    )

    repo = MagicMock()
    repo.traverse_commits.return_value = [commit1, commit2]

    df = analyze_repository_commit_history(repo, "org/proj")

    assert len(df) == 2
    assert set(df["commit_hash"]) == {"111", "222"}
    assert all(df["file"] == "requirements.txt")


# ------------------------------------------------------
# TESTE 4: Verifica se main() chama save_to_csv
# ------------------------------------------------------
@patch("yourmodule.analyzer.save_to_csv")
@patch("yourmodule.analyzer.analyze_repository_commit_history")
def test_main_calls_save(mock_analysis, mock_save, monkeypatch):
    from yourmodule.analyzer import main
    mock_analysis.return_value = pd.DataFrame([{"a": 1}])
    mock_save.return_value = "file.csv"

    # Simula sys.argv
    monkeypatch.setattr("sys.argv", ["script.py", "repo"])

    # Evita sys.exit
    monkeypatch.setattr("sys.exit", lambda code: None)

    main()

    mock_analysis.assert_called_once()
    mock_save.assert_called_once()
