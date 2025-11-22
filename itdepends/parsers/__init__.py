from typing import List, Optional, Type
from itdepends.models import Dependency
from itdepends.parsers.base import BaseParser
from itdepends.parsers.requirements import RequirementsParser
from itdepends.parsers.toml_parser import TomlParser

def get_parser_class(filename: str) -> Optional[Type[BaseParser]]:
    """
    Factory method que decide qual parser usar baseado no nome do arquivo.
    """
    if "requirements" in filename and (filename.endswith(".txt") or filename.endswith(".pip")):
        return RequirementsParser
    
    if filename in ["pyproject.toml", "poetry.lock"]:
        return TomlParser
        
    return None

def parse_dependency_file(filename: str, content: Optional[str]) -> List[Dependency]:
    """
    Retorna Lista de Objetos Dependency.
    """
    if content is None:
        return []

    parser_class = get_parser_class(filename)
    
    if not parser_class:
        return []

    parser = parser_class(content, filename)
    return parser.parse()