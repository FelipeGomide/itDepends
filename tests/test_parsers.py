import pytest
from itdepends.parsers.requirements import RequirementsParser
from itdepends.parsers.toml_parser import TomlParser

def test_requirements_parser_simple():
    content = """
    requests==2.28.1
    pandas>=1.5.0
    """
    parser = RequirementsParser(content, "requirements.txt")
    deps = parser.parse()

    assert len(deps) == 2
    assert deps[0].name == "requests"
    assert deps[0].specifier == "==2.28.1"
    
    assert deps[1].name == "pandas"
    assert deps[1].specifier == ">=1.5.0"

def test_requirements_parser_complex_cases():
    content = """
    # Isto é um comentário
    uvicorn[standard]==0.20.0 ; python_version < '3.11'
    black  # formatador
    """
    parser = RequirementsParser(content, "requirements.txt")
    deps = parser.parse()

    assert len(deps) == 2

    uvicorn = deps[0]
    assert uvicorn.name == "uvicorn"
    assert "standard" in uvicorn.extras
    assert uvicorn.marker is not None
    assert "python_version" in uvicorn.marker

    black = deps[1]
    assert black.name == "black"
    assert black.specifier == "*"

def test_requirements_parser_ignores_invalid_lines(caplog):
    content = """
    requests==1.0
    INVALID NAME WITH SPACE  
    """ 
    parser = RequirementsParser(content, "requirements.txt")
    deps = parser.parse()

    assert len(deps) == 1
    assert deps[0].name == "requests"
    
    assert "Requirement inválido em" in caplog.text

def test_toml_parser_pep621_modern():
    content = """
    [project]
    name = "my-project"
    dependencies = [
        "flask>=2.0",
        "requests[security]"
    ]
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    assert len(deps) == 2
    assert deps[0].name == "flask"
    assert deps[0].specifier == ">=2.0"

def test_toml_parser_poetry_legacy():
    content = """
    [tool.poetry.dependencies]
    python = "^3.9"
    numpy = "^1.24"
    pandas = {version = ">=1.5", extras = ["parquet"]}
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    assert len(deps) == 2
    
    numpy = next(d for d in deps if d.name == "numpy")
    assert numpy.specifier == "^1.24"
    
    pandas = next(d for d in deps if d.name == "pandas")
    assert "parquet" in pandas.extras

def test_toml_parser_invalid_format(caplog):
    content = """
    [tool.poetry
    ISSO ESTA QUEBRADO = "sim"
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    assert deps == []
    assert "TOML inválido em" in caplog.text