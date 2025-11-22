import pytest
from itdepends.parsers.toml_parser import TomlParser
from itdepends.models import DependencyType, DependencyCategory

def test_parse_pep621_standard_dependencies():
    content = """
    [project]
    name = "my-project"
    dependencies = [
        "requests>=2.28.0",
        "numpy==1.24.0"
    ]
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    assert len(deps) == 2
    
    req = next(d for d in deps if d.name == "requests")
    assert req.raw_specifier == ">=2.28.0"
    assert req.category == DependencyCategory.MAIN

    numpy = next(d for d in deps if d.name == "numpy")
    assert numpy.raw_specifier == "==1.24.0"

def test_parse_pep621_optional_dependencies():
    content = """
    [project.optional-dependencies]
    test = [
        "pytest>=7.0",
        "coverage"
    ]
    doc = [
        "mkdocs"
    ]
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    assert len(deps) == 3

    # Grupo 'test' deve ser mapeado para DEV
    pytest_dep = next(d for d in deps if d.name == "pytest")
    assert pytest_dep.category == DependencyCategory.DEV

    # Outros grupos devem ser mapeados para OPTIONAL
    mkdocs = next(d for d in deps if d.name == "mkdocs")
    assert mkdocs.category == DependencyCategory.OPTIONAL

def test_parse_poetry_simple_dependencies():
    content = """
    [tool.poetry.dependencies]
    python = "^3.10"  # Deve ser ignorado
    flask = "^2.0"
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    assert len(deps) == 1
    assert deps[0].name == "flask"
    assert deps[0].raw_specifier == "^2.0"
    assert deps[0].category == DependencyCategory.MAIN

def test_parse_poetry_complex_types():
    """Testa Git, Path, URL e Extras no formato Poetry"""
    content = """
    [tool.poetry.dependencies]
    # 1. Git com branch/rev
    django = { git = "https://github.com/django/django.git", branch = "main" }
    
    # 2. Path local
    my-lib = { path = "./libs/my-lib", develop = true }
    
    # 3. URL direta
    legacy-pkg = { url = "https://example.com/pkg-1.0.zip" }
    
    # 4. Versão com extras
    uvicorn = { version = "^0.20", extras = ["standard"] }
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    assert len(deps) == 4

    # Git
    django = next(d for d in deps if d.name == "django")
    assert django.dependency_type == DependencyType.GIT
    assert django.source_url == "https://github.com/django/django.git"
    assert django.git_ref == "main"

    # Path
    mylib = next(d for d in deps if d.name == "my-lib")
    assert mylib.dependency_type == DependencyType.PATH
    assert mylib.source_path == "./libs/my-lib"

    # URL
    legacy = next(d for d in deps if d.name == "legacy-pkg")
    assert legacy.dependency_type == DependencyType.URL
    assert legacy.source_url == "https://example.com/pkg-1.0.zip"

    # Extras
    uvicorn = next(d for d in deps if d.name == "uvicorn")
    assert uvicorn.raw_specifier == "^0.20"
    assert "standard" in uvicorn.extras_requested

def test_parse_poetry_groups_and_legacy_dev():
    content = """
    # Legacy dev-dependencies
    [tool.poetry.dev-dependencies]
    black = "*"

    # New Group syntax (test) -> DEV
    [tool.poetry.group.test.dependencies]
    pytest = "^7.0"

    # New Group syntax (docs) -> OPTIONAL
    [tool.poetry.group.docs.dependencies]
    mkdocs = "*"
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    assert len(deps) == 3

    black = next(d for d in deps if d.name == "black")
    assert black.category == DependencyCategory.DEV

    pytest_dep = next(d for d in deps if d.name == "pytest")
    assert pytest_dep.category == DependencyCategory.DEV

    mkdocs = next(d for d in deps if d.name == "mkdocs")
    assert mkdocs.category == DependencyCategory.OPTIONAL

def test_parse_poetry_lock_file():
    content = """
    [[package]]
    name = "certifi"
    version = "2022.12.7"
    description = "Python package..."
    category = "main"
    optional = false
    python-versions = ">=3.6"

    [[package]]
    name = "pytest"
    version = "7.2.0"
    category = "dev"
    """
    parser = TomlParser(content, "poetry.lock")
    deps = parser.parse()

    assert len(deps) == 2

    certifi = next(d for d in deps if d.name == "certifi")
    assert certifi.raw_specifier == "==2022.12.7"
    assert certifi.category == DependencyCategory.MAIN
    # Verifica se a regra de versão foi criada corretamente
    assert certifi.version_rules[0].operator == "=="
    assert certifi.version_rules[0].version == "2022.12.7"

    pytest_dep = next(d for d in deps if d.name == "pytest")
    assert pytest_dep.category == DependencyCategory.DEV
    assert pytest_dep.raw_specifier == "==7.2.0"


def test_parse_invalid_toml(caplog):
    content = """
    [tool.poetry
    ISSO ESTA INVALIDO = "sem fechar colchete
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    # Não deve crashar, deve retornar lista vazia e logar erro
    assert deps == []
    assert "TOML inválido em" in caplog.text

def test_parse_pep621_invalid_requirement_string(caplog):
    content = """
    [project]
    dependencies = [
        "pacote-valido",
        "INVALID NAME @@@" 
    ]
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    assert len(deps) == 1
    assert deps[0].name == "pacote-valido"
    assert "Dependência inválida no TOML" in caplog.text

def test_parse_poetry_multiple_constraints_list():
    content = """
    [tool.poetry.dependencies]
    # Caso simples
    requests = "^2.28"
    
    # Caso complexo: Lista de restrições (ex: suporte a múltiplos pythons)
    numpy = [
        { version = "^1.24", python = ">=3.8" },
        { version = "^1.19", python = "<3.8" }
    ]
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    # Esperamos 3 dependências: 1 requests + 2 entradas de numpy
    assert len(deps) == 3 
    
    numpy_entries = [d for d in deps if d.name == "numpy"]
    assert len(numpy_entries) == 2
    
    # Verifica se pegou as versões diferentes
    versions = sorted([d.raw_specifier for d in numpy_entries])
    assert versions == ["^1.19", "^1.24"]

def test_parse_poetry_version_rules_logic():
    """
    Testa se a string de versão é convertida corretamente em objetos VersionRule.
    """
    content = """
    [tool.poetry.dependencies]
    # Caso 1: Pinagem exata (Deve gerar pinned_version)
    exact-lib = "==1.5.0"
    
    # Caso 2: Múltiplas regras (virgula)
    range-lib = ">=1.0.0, <2.0.0"
    
    # Caso 3: Operador implícito (Poetry trata "1.0" como "^1.0", 
    # mas nosso parser deve ser robusto e extrair o número)
    implicit-lib = "1.2.3"
    
    # Caso 4: Operador Tilde/Caret
    caret-lib = "^2.0.0"
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    assert len(deps) == 4

    # Caso 1
    exact = next(d for d in deps if d.name == "exact-lib")
    assert exact.pinned_version == "1.5.0"
    assert len(exact.version_rules) == 1

    # Caso 2
    range_dep = next(d for d in deps if d.name == "range-lib")
    assert len(range_dep.version_rules) == 2
    ops = {r.operator for r in range_dep.version_rules}
    assert ">=" in ops and "<" in ops

    # Caso 3
    implicit = next(d for d in deps if d.name == "implicit-lib")
    assert implicit.version_rules[0].operator == "==" 
    assert implicit.version_rules[0].version == "1.2.3"

def test_parse_empty_or_partial_manifests():
    """
    Garante que o parser não quebra (KeyError/AttributeError) 
    se o arquivo existir mas não tiver as seções de dependência.
    """
    # 1. Arquivo vazio
    parser = TomlParser("", "pyproject.toml")
    assert parser.parse() == []

    # 2. Arquivo apenas com metadados de ferramenta
    content = """
    [tool.black]
    line-length = 88
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()
    assert deps == []

    # 3. Seção poetry existe mas está vazia
    content_empty_poetry = """
    [tool.poetry]
    name = "pacote"
    """
    parser = TomlParser(content_empty_poetry, "pyproject.toml")
    deps = parser.parse()
    assert deps == []

def test_parse_poetry_unknown_dict_format():
    """
    Se encontrarmos um dicionário que não tem 'version', 'git', 'path' ou 'url',
    devemos ignorar para não criar uma dependência "fantasma" ou dar erro.
    """
    content = """
    [tool.poetry.dependencies]
    # Um formato hipotético ou erro de digitação do usuário
    weird-lib = { some-unknown-key = "value", other = 123 }
    
    # Uma válida para garantir que o resto continua funcionando
    valid-lib = "1.0"
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()
    
    assert len(deps) == 1
    assert deps[0].name == "valid-lib"

def test_parse_pep621_mixed_specs():
    """
    Testa a robustez do parser de strings PEP 621 com espaços e operadores variados.
    """
    content = """
    [project]
    dependencies = [
        "django >= 3.0",    # Com espaços
        "pandas>1.0,<2.0",  # Sem espaços, multiplo
        "requests!=2.0"     # Operador diferente
    ]
    """
    parser = TomlParser(content, "pyproject.toml")
    deps = parser.parse()

    assert len(deps) == 3
    
    django = next(d for d in deps if d.name == "django")
    assert django.version_rules[0].operator == ">="
    assert django.version_rules[0].version == "3.0"

    requests_dep = next(d for d in deps if d.name == "requests")
    assert requests_dep.version_rules[0].operator == "!="