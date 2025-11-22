import os
import pytest
import pandas as pd
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock

from itdepends.new_history import (
    extract_dependencies_from_commit,
    analyze_repository_stream,
    _sanitize_str,
    MAX_FILE_SIZE_BYTES
)

class MockDependency:
    """Simula o objeto Dependency retornado pelo parser"""
    def __init__(self, name, version, dep_type="package", source_url=None):
        self.name = name
        self.pinned_version = version
        self.raw_specifier = f"=={version}"
        self.dependency_type = dep_type
        self.category = "main"
        self.source_url = source_url
        self.source_path = None
        self.git_ref = None
        self.marker = None
        self.extras_requested = ["security"] if name == "requests" else []

    def to_dict(self):
        return {
            "name": self.name,
            "pinned_version": self.pinned_version,
            "raw_specifier": self.raw_specifier,
            "dependency_type": self.dependency_type,
            "category": self.category,
            "source_url": self.source_url,
            "source_path": self.source_path,
            "git_ref": self.git_ref,
            "marker": self.marker,
            "extras_requested": self.extras_requested
        }

def make_mock_mod(filename, content="fake content", change_type="MODIFY", size=100):
    """Cria um arquivo fake do Pydriller"""
    mod = MagicMock()
    mod.new_path = filename
    mod.change_type.name = change_type
    mod.source_code = content
    mod.source_code_len = size
    return mod

def make_mock_commit(hash_id, author, date, mods):
    """Cria um commit fake do Pydriller"""
    commit = MagicMock()
    commit.hash = hash_id
    commit.author.name = author
    commit.author.email = f"{author.lower()}@test.com"
    commit.author_date = date
    commit.modified_files = mods
    return commit

# -------------------------------------------------------------------------
# Testes Unitários: Helpers
# -------------------------------------------------------------------------

def test_sanitize_str():
    assert _sanitize_str("teste") == "teste"
    assert _sanitize_str("teste\nnova linha") == "teste nova linha"
    assert _sanitize_str(None) == ""
    assert _sanitize_str(123) == "123"
    assert _sanitize_str("  espacos  ") == "espacos"

# -------------------------------------------------------------------------
# Testes de Lógica Extração (Generator)
# -------------------------------------------------------------------------

@patch("itdepends.new_history.Repository")
@patch("itdepends.new_history.parse_dependency_file")
def test_extract_happy_path(mock_parser, mock_repo_cls):
    """
    Testa se o generator extrai corretamente dados de um commit válido,
    converte datas para UTC e chama o parser.
    """
    mock_parser.return_value = [
        MockDependency("requests", "2.28.1"),
        MockDependency("django", "4.0.0", dep_type="git", source_url="http://git.com")
    ]

    # Configura o Commit Fake
    date_now = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    commit = make_mock_commit("abc1234", "Alice", date_now, [
        make_mock_mod("pyproject.toml")
    ])

    # Configura o Repository do Pydriller
    mock_repo_instance = mock_repo_cls.return_value
    mock_repo_instance.traverse_commits.return_value = [commit]

    results = list(extract_dependencies_from_commit("fake/path"))

    assert len(results) == 2 
    
    # Valida normalização de dados no primeiro item
    item = results[0]
    assert item["repository"] == "fake/path"
    assert item["commit_hash"] == "abc1234"
    assert item["author_name"] == "Alice"
    assert item["date_utc"] == "2023-01-01T12:00:00+00:00" # ISO format
    assert item["file_name"] == "pyproject.toml"
    assert item["dep_name"] == "requests"
    assert item["dep_extras"] == "security"
    
    # Valida segundo item
    item2 = results[1]
    assert item2["dep_name"] == "django"
    assert item2["dep_source_url"] == "http://git.com"

@patch("itdepends.new_history.Repository")
def test_extract_ignores_irrelevant_files(mock_repo_cls):
    """Arquivos que não são requirements/toml/lock devem ser ignorados"""
    commit = make_mock_commit("hash1", "Bob", datetime.now(timezone.utc), [
        make_mock_mod("README.md"),
        make_mock_mod("main.py")
    ])
    mock_repo_cls.return_value.traverse_commits.return_value = [commit]

    results = list(extract_dependencies_from_commit("repo"))
    assert len(results) == 0

@patch("itdepends.new_history.Repository")
def test_extract_ignores_deleted_files(mock_repo_cls):
    """Arquivos deletados não devem ser processados"""
    commit = make_mock_commit("hash2", "Bob", datetime.now(timezone.utc), [
        make_mock_mod("requirements.txt", change_type="DELETE")
    ])
    mock_repo_cls.return_value.traverse_commits.return_value = [commit]

    results = list(extract_dependencies_from_commit("repo"))
    assert len(results) == 0

@patch("itdepends.new_history.Repository")
def test_extract_security_max_file_size(mock_repo_cls, caplog):
    """
    Verifica se arquivos gigantes acima do limite configurado são pulados.
    """
    huge_content = "a" * (MAX_FILE_SIZE_BYTES + 100)
    
    commit = make_mock_commit("hash3", "Dave", datetime.now(timezone.utc), [
        # Passamos o huge_content no parametro content
        make_mock_mod("poetry.lock", content=huge_content)
    ])
    mock_repo_cls.return_value.traverse_commits.return_value = [commit]

    results = list(extract_dependencies_from_commit("repo"))
    
    assert len(results) == 0
    assert "excede limite seguro" in caplog.text

@patch("itdepends.new_history.Repository")
def test_extract_resilience_encoding_error(mock_repo_cls, caplog):
    """
    Se houver erro de UnicodeDecodeError ao ler o arquivo, o script deve logar e continuar, não crashar.
    """
    mod_error = make_mock_mod("requirements.txt")
    type(mod_error).source_code = PropertyMock(side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'error'))

    commit = make_mock_commit("hash4", "Eve", datetime.now(timezone.utc), [mod_error])
    mock_repo_cls.return_value.traverse_commits.return_value = [commit]

    results = list(extract_dependencies_from_commit("repo"))

    assert len(results) == 0
    assert "Erro de encoding" in caplog.text

# -------------------------------------------------------------------------
# Testes de Streaming e CSV
# -------------------------------------------------------------------------

@patch("itdepends.new_history.extract_dependencies_from_commit")
def test_analyze_repository_stream_integration(mock_extract, tmp_path):
    """
    Testa o fluxo completo
    """
    output_csv = tmp_path / "results" / "test_new_history.csv"
    
    mock_extract.return_value = iter([
        {
            "repository": "repo", "commit_hash": "1", "author_name": "A", "author_email": "a@a.com",
            "date_utc": "2023-01-01", "file_name": "req.txt", "change_type": "MODIFY",
            "dep_name": "pandas", "dep_version_pinned": "1.0", "dep_raw_specifier": "==1.0",
            "dep_type": "package", "dep_category": "main", 
            "dep_source_url": "", "dep_source_path": "", "dep_git_ref": "", 
            "dep_marker": "", "dep_extras": ""
        },
        {
            "repository": "repo", "commit_hash": "2", "author_name": "B", "author_email": "b@b.com",
            "date_utc": "2023-01-02", "file_name": "req.txt", "change_type": "MODIFY",
            "dep_name": "numpy", "dep_version_pinned": "1.20", "dep_raw_specifier": "==1.20",
            "dep_type": "package", "dep_category": "dev",
            "dep_source_url": "", "dep_source_path": "", "dep_git_ref": "", 
            "dep_marker": "", "dep_extras": ""
        }
    ])

    df = analyze_repository_stream("repo/dummy", str(output_csv))

    assert os.path.exists(output_csv)
    assert len(df) == 2 
    assert df.iloc[0]["dep_name"] == "pandas"
    assert df.iloc[1]["dep_category"] == "dev"

@patch("itdepends.new_history.extract_dependencies_from_commit")
def test_analyze_repository_stream_empty(mock_extract, tmp_path):
    """Se o repo não tiver nada, deve retornar DF vazio e não criar CSV inválido"""
    output_csv = tmp_path / "empty.csv"
    mock_extract.return_value = iter([])

    df = analyze_repository_stream("repo/empty", str(output_csv))

    assert df.empty
    assert os.path.exists(output_csv)

@patch("itdepends.new_history.Repository")
@patch("itdepends.new_history.parse_dependency_file")
def test_extract_resilience_parser_crash(mock_parser, mock_repo_cls, caplog):
    """
    CRÍTICO: Se o parser externo lançar uma exceção genérica, o loop NÃO pode parar.
    """
    commit = make_mock_commit("crash1", "Dev", datetime.now(timezone.utc), [
        make_mock_mod("pyproject.toml")
    ])
    mock_repo_cls.return_value.traverse_commits.return_value = [commit]

    mock_parser.side_effect = ValueError("Erro interno do parser")

    results = list(extract_dependencies_from_commit("repo"))

    assert len(results) == 0
    assert "Erro de parser: pyproject.toml" in caplog.text

@patch("itdepends.new_history.Repository")
def test_extract_empty_file_content(mock_repo_cls):
    """
    Arquivos vazios devem ser pulados imediatamente sem tentar chamar o parser.
    """
    mod_empty = make_mock_mod("requirements.txt", content="")
    mod_none = make_mock_mod("pyproject.toml", content=None)

    commit = make_mock_commit("empty1", "Dev", datetime.now(timezone.utc), [mod_empty, mod_none])
    mock_repo_cls.return_value.traverse_commits.return_value = [commit]

    results = list(extract_dependencies_from_commit("repo"))
    assert len(results) == 0

@patch("itdepends.new_history.Repository")
@patch("itdepends.new_history.parse_dependency_file")
def test_extract_null_safety_in_extras(mock_parser, mock_repo_cls, caplog):
    """
    Garante que se 'extras_requested' for None, o código não quebra.
    """
    dep_broken = MockDependency("lib", "1.0")
    dep_broken.extras_requested = None 

    mock_parser.return_value = [dep_broken]
    commit = make_mock_commit("null_check", "Dev", datetime.now(timezone.utc), [
        make_mock_mod("requirements.txt") 
    ])
    mock_repo_cls.return_value.traverse_commits.return_value = [commit]

    results = list(extract_dependencies_from_commit("repo"))
    
    assert len(results) == 1
    assert results[0]["dep_extras"] == ""

@patch("itdepends.new_history.extract_dependencies_from_commit")
def test_analyze_stream_creates_nested_directories(mock_extract, tmp_path):
    """
    Verifica se a função cria pastas aninhadas caso elas não existam, evitando FileNotFoundError.
    """
    nested_output = tmp_path / "deep" / "folder" / "structure" / "new_history.csv"
    mock_extract.return_value = iter([])

    analyze_repository_stream("repo", str(nested_output))

    assert nested_output.exists()

@patch("itdepends.new_history.Repository")
@patch("itdepends.new_history.parse_dependency_file")
def test_extract_all_fields_mapping(mock_parser, mock_repo_cls):
    """
    Verifica se TODOS os campos do objeto Dependency são mapeados corretamente para o dicionário final, sem trocar colunas.
    """
    full_dep = MockDependency("complex-lib", "1.0")
    full_dep.source_url = "https://github.com/user/repo"
    full_dep.source_path = "./libs/local"
    full_dep.git_ref = "feature/branch"
    full_dep.marker = "sys_platform == 'linux'"
    full_dep.extras_requested = ["dev", "test"]
    
    mock_parser.return_value = [full_dep]

    commit = make_mock_commit("hash123", "Dev Author", datetime.now(timezone.utc), [
        make_mock_mod("pyproject.toml", change_type="ADD")
    ])
    mock_repo_cls.return_value.traverse_commits.return_value = [commit]

    results = list(extract_dependencies_from_commit("repo"))
    item = results[0]
    
    assert item["dep_name"] == "complex-lib"
    assert item["dep_source_url"] == "https://github.com/user/repo"
    assert item["dep_source_path"] == "./libs/local"
    assert item["dep_git_ref"] == "feature/branch"
    assert item["dep_marker"] == "sys_platform == 'linux'"
    assert item["dep_extras"] == "dev,test"
    assert item["change_type"] == "ADD"

@patch("itdepends.new_history.extract_dependencies_from_commit")
def test_csv_injection_resilience(mock_extract, tmp_path):
    """
    Verifica se dados contendo caracteres de quebra de CSV (newlines, delimiters)
    são tratados corretamente e não corrompem o arquivo final.
    """
    output_csv = tmp_path / "injection.csv"
    
    mock_extract.return_value = iter([
        {
            "repository": "repo", "commit_hash": "1", 
            "author_name": "Hack\nAuthor",  
            "author_email": "a@b.com", "date_utc": "2023-01-01", 
            "file_name": "req.txt", "change_type": "MODIFY",
            "dep_name": "lib; injection",   
            "dep_version_pinned": '1.0"',
            "dep_raw_specifier": "", "dep_type": "package", "dep_category": "main", 
            "dep_source_url": "", "dep_source_path": "", "dep_git_ref": "", 
            "dep_marker": "", "dep_extras": ""
        }
    ])

    analyze_repository_stream("repo", str(output_csv))
    df = pd.read_csv(output_csv)
    
    assert len(df) == 1
    assert df.iloc[0]["author_name"] == "Hack\nAuthor" or "Hack Author" in df.iloc[0]["author_name"]
    assert df.iloc[0]["dep_name"] == "lib; injection"

@patch("itdepends.new_history.extract_dependencies_from_commit")
def test_stream_writes_progressively(mock_extract, tmp_path):
    """
    Verifica se o arquivo é criado e escrito mesmo se o generator for infinito
    """
    output_csv = tmp_path / "stream.csv"
    
    def infinite_generator():
        yield {
            "repository": "repo", "commit_hash": "1", "author_name": "A", "author_email": "a",
            "date_utc": "2023", "file_name": "f", "change_type": "M",
            "dep_name": "lib", "dep_version_pinned": "1", "dep_raw_specifier": "",
            "dep_type": "pk", "dep_category": "m", "dep_source_url": "", 
            "dep_source_path": "", "dep_git_ref": "", "dep_marker": "", "dep_extras": ""
        }
        raise KeyboardInterrupt("Stop")

    mock_extract.return_value = infinite_generator()

    try:
        analyze_repository_stream("repo", str(output_csv))
    except KeyboardInterrupt:
        pass

    assert os.path.exists(output_csv)
    with open(output_csv) as f:
        lines = f.readlines()
        assert len(lines) >= 2