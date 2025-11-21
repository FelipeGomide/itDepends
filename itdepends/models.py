from dataclasses import dataclass, asdict, field
from typing import Optional, List

@dataclass
class Dependency:
    name: str
    source_file: str
    specifier: str = "*"  # regra de versão declarada pelo usuário
    version: Optional[str] = None  
    marker: Optional[str] = None  # Condições de ambiente
    line_number: Optional[int] = None
    category: str = "main"
    extras: List[str] = field(default_factory=list)
    
    def to_dict(self):
        return asdict(self)