from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

class DependencyType(str, Enum):
    PACKAGE = "package"
    GIT = "git"
    URL = "url"
    PATH = "path"
    EDITABLE = "editable"

class DependencyCategory(str, Enum):
    MAIN = "main"
    DEV = "dev"
    OPTIONAL = "optional"
    TEST = "test"

@dataclass(slots=True, frozen=True)
class VersionRule:
    operator: str   # Ex: "==", ">="
    version: str    # Ex: "1.2.3"

@dataclass(slots=True)
class Dependency:
    name: str
    source_file: str                  
    
    dependency_type: DependencyType = DependencyType.PACKAGE
    category: DependencyCategory = DependencyCategory.MAIN
    
    raw_specifier: Optional[str] = None   # 'raw_specifier' guarda o texto original (ex: "^1.0")
    version_rules: List[VersionRule] = field(default_factory=list) # 'version_rules' guarda a lógica

    marker: Optional[str] = None  # Ex: ">=1.0.0,<2.0.0" (O texto exato que estava no arquivo)
    extras_requested: List[str] = field(default_factory=list)  # Ex: ["standard"] (para uvicorn[standard])

    # Origens Alternativas
    source_url: Optional[str] = None  
    source_path: Optional[str] = None 
    git_ref: Optional[str] = None     

    # Rastreabilidade
    line_number: Optional[int] = None
    required_by_extra: Optional[str] = None

    @property
    def pinned_version(self) -> Optional[str]:
        # Percorre a lista procurando o operador de igualdade exata
        for rule in self.version_rules:
            if rule.operator == "==":
                return rule.version
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source_file": self.source_file,
            "dependency_type": self.dependency_type.value,
            "category": self.category.value,
            "raw_specifier": self.raw_specifier,
            # Serializa lista de regras aninhadas
            "version_rules": [
                {"operator": v.operator, "version": v.version} 
                for v in self.version_rules
            ],
            "pinned_version": self.pinned_version, # Já salva pré-calculado para o Pandas
            "marker": self.marker,
            "extras_requested": self.extras_requested,
            "source_url": self.source_url,
            "source_path": self.source_path,
            "git_ref": self.git_ref,
            "line_number": self.line_number,
            "required_by_extra": self.required_by_extra,
        }