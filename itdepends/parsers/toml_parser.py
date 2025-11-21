try:
    import tomllib
except ImportError:
    import tomli as tomllib

from typing import List, Dict, Any
from itdepends.models import Dependency
from itdepends.parsers.base import BaseParser, logger

class TomlParser(BaseParser):
    def parse(self) -> List[Dependency]:
        dependencies = []
        if not self.content:
            return []

        try:
            data = tomllib.loads(self.content)
        except Exception as e:
            logger.error(f"TOML inválido em {self.filename}: {e}")
            return []

        # 1. Estratégia: Poetry Lock ([[package]])
        # (Erro 1): Detecta estrutura de lista de pacotes
        if "package" in data and isinstance(data["package"], list):
            self._parse_lock_packages(data["package"], dependencies)
            return dependencies

        # 2. Estratégia: PEP 621 ([project.dependencies])
        project_deps = data.get("project", {}).get("dependencies", [])
        if project_deps:
            self._parse_pep621_list(project_deps, dependencies, "main")
        
        # 3. Estratégia: Poetry Manifesto ([tool.poetry.dependencies])
        poetry_section = data.get("tool", {}).get("poetry", {})
        if poetry_section:
            self._parse_poetry_dict(poetry_section.get("dependencies", {}), dependencies, "main")
            self._parse_poetry_dict(poetry_section.get("dev-dependencies", {}), dependencies, "dev")
            
            for group_name, group_data in poetry_section.get("group", {}).items():
                self._parse_poetry_dict(group_data.get("dependencies", {}), dependencies, group_name)

        return dependencies

    def _parse_lock_packages(self, packages: List[Dict], dep_list: List[Dependency]):
        """Lê a lista exata de versões do poetry.lock"""
        for pkg in packages:
            name = pkg.get("name")
            version = pkg.get("version")
            category = pkg.get("category", "main")
            
            if name:
                dep_list.append(Dependency(
                    name=name,
                    specifier=f"=={version}" if version else "*",
                    version=version,
                    source_file=self.filename,
                    category=category,
                    extras=pkg.get("extras", [])
                ))

    def _parse_pep621_list(self, raw_list: List[str], dep_list: List[Dependency], category: str):
        from packaging.requirements import Requirement, InvalidRequirement
        for line in raw_list:
            try:
                req = Requirement(line)
                dep_list.append(Dependency(
                    name=req.name,
                    specifier=str(req.specifier) if req.specifier else "*",
                    marker=str(req.marker) if req.marker else None,
                    source_file=self.filename,
                    category=category,
                    extras=list(req.extras)
                ))
            except InvalidRequirement:
                pass

    def _parse_poetry_dict(self, raw_dict: Dict[str, Any], dep_list: List[Dependency], category: str):
        for name, value in raw_dict.items():
            if name.lower() == "python": continue

            specifier = "*"
            extras = []
            marker = None

            if isinstance(value, str):
                specifier = value
            elif isinstance(value, dict):
                specifier = value.get("version", "*")
                extras = value.get("extras", [])
                marker = value.get("markers", None)

            dep_list.append(Dependency(
                name=name,
                specifier=specifier,
                marker=marker,
                source_file=self.filename,
                category=category,
                extras=extras
            ))