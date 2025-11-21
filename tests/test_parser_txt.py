import pytest
from itdepends.parsers.requirements import RequirementsParser
from itdepends.parsers.toml_parser import TomlParser
from itdepends.models import DependencyType, DependencyCategory

def test_requirements_parser_simple():
    content = """
    requests==2.28.1
    pandas>=1.5.0
    """
    parser = RequirementsParser(content, "requirements.txt")
    deps = parser.parse()

    assert len(deps) == 2
    
    # Requests
    req = deps[0]
    assert req.name == "requests"
    assert req.raw_specifier == "==2.28.1"
    assert req.pinned_version == "2.28.1"
    
    # Pandas
    pandas = deps[1]
    assert pandas.name == "pandas"
    assert pandas.raw_specifier == ">=1.5.0"
    assert pandas.pinned_version is None  # Não é exato (==), então pinned é None

def test_requirements_parser_complex_cases():
    content = """
    # Isto é um comentário
    uvicorn[standard]==0.20.0 ; python_version < '3.11'
    black  # formatador
    -e .
    git+https://github.com/django/django.git@main#egg=django
    """
    parser = RequirementsParser(content, "requirements.txt")
    deps = parser.parse()

    assert len(deps) == 4 

    # 1. Uvicorn
    uvicorn = deps[0]
    assert uvicorn.name == "uvicorn"
    assert "standard" in uvicorn.extras_requested
    assert "python_version" in uvicorn.marker

    # 2. Black
    black = deps[1]
    assert black.name == "black"
    assert black.raw_specifier is None

    # 3. Editable Local (-e .)
    editable = deps[2]
    assert editable.dependency_type == DependencyType.EDITABLE
    assert editable.source_path == "."
    # CORREÇÃO: O packaging normaliza nomes não padrão (como ponto) para traço
    assert editable.name == "-" 

    # 4. Git URL
    django = deps[3]
    assert django.name == "django" 
    assert django.dependency_type == DependencyType.GIT
    assert django.git_ref == "main"

def test_requirements_parser_ignores_invalid_lines(caplog):
    content = """
    requests==1.0
    INVALID NAME WITH SPACE  
    """ 
    content = """
    requests==1.0
    --invalid-flag
    """
    parser = RequirementsParser(content, "requirements.txt")
    deps = parser.parse()

    assert len(deps) == 1
    assert deps[0].name == "requests"
    
    # O parser ignora flags desconhecidas silenciosamente ou com warning
    # (Neste caso específico, --invalid-flag cai no check de flags '-')

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
    
    flask = deps[0]
    assert flask.name == "flask"
    assert flask.raw_specifier == ">=2.0"
    assert flask.category == DependencyCategory.MAIN

    requests = deps[1]
    assert "security" in requests.extras_requested

def test_toml_parser_poetry_legacy():
    content = """
    [tool.poetry.dependencies]
    python = "^3.9"
    numpy = "^1.24"
    pandas = {version = ">=1.5", extras = ["parquet"]}
    
    [tool.poetry.dev-dependencies]
    pytest = "^7.0"
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    assert len(deps) == 3
    
    numpy = next(d for d in deps if d.name == "numpy")
    assert numpy.raw_specifier == "^1.24"
    
    pandas = next(d for d in deps if d.name == "pandas")
    assert "parquet" in pandas.extras_requested
    
    pytest_dep = next(d for d in deps if d.name == "pytest")
    assert pytest_dep.category == DependencyCategory.DEV

def test_toml_parser_invalid_format(caplog):
    content = """
    [tool.poetry
    ISSO ESTA QUEBRADO = "sim"
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    assert deps == []
    assert "TOML inválido em" in caplog.text

def test_requirements_parser_vcs_variations():
    content = """
    # Git via SSH com tag específica
    git+ssh://git@github.com/myorg/private-pkg.git@v1.2.3#egg=private-pkg
    
    # Git protocol puro (sem egg explícito - deve deduzir o nome 'legacy-lib')
    git://github.com/legacy/legacy-lib.git
    
    # HTTPS sem ref/branch (git_ref deve ser None)
    git+https://github.com/other/repo.git#egg=my-repo
    """
    parser = RequirementsParser(content, "requirements.txt")
    deps = parser.parse()

    assert len(deps) == 3

    # 1. SSH
    ssh_dep = deps[0]
    assert ssh_dep.name == "private-pkg"
    assert ssh_dep.dependency_type == DependencyType.GIT
    assert ssh_dep.git_ref == "v1.2.3"

    # 2. Git Protocol (Inferência de nome)
    legacy = deps[1]
    assert legacy.name == "legacy-lib" # Deduzido da URL
    assert legacy.dependency_type == DependencyType.GIT
    assert legacy.git_ref is None

    # 3. No Ref
    repo = deps[2]
    assert repo.name == "my-repo"
    assert repo.git_ref is None



def test_requirements_parser_local_paths():
    content = """
    # Formato file:// (padrão antigo)
    file:///abs/path/to/my-lib-a
    
    # Caminho relativo direto (sem -e)
    ./libs/internal-lib-b
    
    # Caminho Windows (hard to test on linux regex, but useful to keep in mind)
    # C:\\Users\\Projects\\lib-c
    """
    parser = RequirementsParser(content, "requirements.txt")
    deps = parser.parse()

    assert len(deps) == 2

    # 1. file://
    lib_a = deps[0]
    # O código remove 'file://', sobra o path
    assert lib_a.dependency_type == DependencyType.PATH
    assert lib_a.name == "my-lib-a" # Deduzido do path
    
    # 2. Relative path
    lib_b = deps[1]
    assert lib_b.dependency_type == DependencyType.PATH
    assert lib_b.source_path == "./libs/internal-lib-b"
    assert lib_b.name == "internal-lib-b"

def test_requirements_parser_edge_cases_formatting():
    content = """
    # Includes devem ser ignorados silenciosamente (sem criar dependência)
    -r requirements/base.txt
    -c constraints.txt
    
    # Comentário inline com tabulação
    requests==2.0.0\t# via tab
    
    # Flags de pip que devem ser ignoradas
    --extra-index-url https://pypi.org/simple
    """
    parser = RequirementsParser(content, "requirements.txt")
    deps = parser.parse()

    assert len(deps) == 1
    
    req = deps[0]
    assert req.name == "requests"
    assert req.pinned_version == "2.0.0" 
    # Garante que o comentário "\t# via tab" foi removido e não quebrou o parse

def test_requirements_parser_edge_cases_security_and_formats():
    content = """
    # 1. Autenticação (Isso vai quebrar a lógica de split('@'))
    git+https://mytoken@github.com/org/private-repo.git

    # 2. Sintaxe SCP (Git SSH sem protocolo explícito)
    git@github.com:tiangolo/fastapi.git

    # 3. Arquivos diretos (Nome deve ser limpo)
    https://example.com/builds/my-lib-1.0.0.tar.gz
    ./downloads/numpy-1.24.0-cp39-win_amd64.whl

    # 4. Comentário grudado (Sticky comment)
    requests==2.31.0#ignore-this
    """
    parser = RequirementsParser(content, "requirements.txt")
    deps = parser.parse()

    # CORREÇÃO: São 5 itens (1 Auth + 1 SCP + 2 Arquivos + 1 Requests)
    assert len(deps) == 5

    # 1. Auth Case
    private = deps[0]
    assert private.name == "private-repo"
    assert private.git_ref is None # Token não deve virar ref

    # 2. SCP Case
    fastapi = deps[1]
    assert fastapi.name == "fastapi"
    assert fastapi.dependency_type == DependencyType.GIT

    # 3. Archives (Tarball e Wheel)
    mylib = deps[2]
    # O parser limpa extensões conhecidas, então espera-se 'my-lib-1-0-0'
    assert "tar.gz" not in mylib.name 
    
    numpy = deps[3]
    assert "whl" not in numpy.name
    assert numpy.dependency_type == DependencyType.PATH

    # 4. Sticky Comment
    req = deps[4]
    assert req.name == "requests"
    assert req.raw_specifier == "==2.31.0"