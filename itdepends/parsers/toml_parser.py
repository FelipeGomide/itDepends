try:
    import tomllib
except ImportError:
    import tomli as tomllib

from typing import List, Dict, Any
from packaging.requirements import Requirement, InvalidRequirement
from itdepends.models import Dependency, DependencyType, DependencyCategory, VersionRule
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
        
        # Detecção de Lock File (Poetry)
        if "package" in data and isinstance(data["package"], list):
            self._parse_lock_packages(data["package"], dependencies)
            return dependencies
        
        # Detecção PEP 621 (Padrão moderno [project])
        project_deps = data.get("project", {}).get("dependencies", [])
        if project_deps:
            self._parse_pep621_list(project_deps, dependencies, DependencyCategory.MAIN)
        
        # Opcionais do PEP 621
        optional_deps = data.get("project", {}).get("optional-dependencies", {})
        for group, deps in optional_deps.items():
            cat = DependencyCategory.DEV if group in ["dev", "test"] else DependencyCategory.OPTIONAL
            self._parse_pep621_list(deps, dependencies, cat)

        # Detecção Poetry (Legacy/Padrão atual do Poetry [tool.poetry])
        poetry_section = data.get("tool", {}).get("poetry", {})
        if poetry_section:
            main_deps = poetry_section.get("dependencies", {})
            self._parse_poetry_dict(main_deps, dependencies, DependencyCategory.MAIN)

            dev_deps = poetry_section.get("dev-dependencies", {})
            self._parse_poetry_dict(dev_deps, dependencies, DependencyCategory.DEV)
            groups = poetry_section.get("group", {})
            for group_name, group_data in groups.items():
                cat = DependencyCategory.DEV if group_name in ["dev", "test"] else DependencyCategory.OPTIONAL
                group_deps = group_data.get("dependencies", {})
                self._parse_poetry_dict(group_deps, dependencies, cat)

        return dependencies

    def _parse_lock_packages(self, packages: List[Dict], dep_list: List[Dependency]):
        """Lê a lista exata de versões do poetry.lock"""
        for pkg in packages:
            name = pkg.get("name")
            version = pkg.get("version")
            
            cat_str = pkg.get("category", "main")
            category = DependencyCategory.MAIN if cat_str == "main" else DependencyCategory.DEV
            
            if name:
                rules = [VersionRule(operator="==", version=version)] if version else []
                dep_list.append(Dependency(
                    name=name,
                    source_file=self.filename,
                    dependency_type=DependencyType.PACKAGE,
                    category=category,
                    raw_specifier=f"=={version}" if version else None,
                    version_rules=rules,
                    extras_requested=pkg.get("extras", []),
                ))

    def _parse_pep621_list(self, raw_list: List[str], dep_list: List[Dependency], category: DependencyCategory):
        """Lê lista de strings estilo requirements.txt (PEP 621)"""
        for line in raw_list:
            try:
                req = Requirement(line)
                rules = []
                if req.specifier:
                    for spec in req.specifier:
                        rules.append(VersionRule(operator=spec.operator, version=spec.version))

                dep_list.append(Dependency(
                    name=req.name,
                    source_file=self.filename,
                    dependency_type=DependencyType.PACKAGE,
                    category=category,
                    raw_specifier=str(req.specifier) if req.specifier else None,
                    version_rules=rules,
                    marker=str(req.marker) if req.marker else None,
                    extras_requested=list(req.extras)
                ))
            except InvalidRequirement:
                logger.warning(f"Dependência inválida no TOML {self.filename}: {line}")

    def _parse_poetry_dict(self, raw_dict: Dict[str, Any], dep_list: List[Dependency], category: DependencyCategory):
        """Lê dicionário chave-valor do Poetry"""
        if not raw_dict:
            return

        for name, value in raw_dict.items():
            if name.lower() == "python": continue

            if isinstance(value, list):
                for item in value:
                    self._process_poetry_item(name, item, dep_list, category)
            else:
                self._process_poetry_item(name, value, dep_list, category)
    
    def _parse_specifier_string(self, spec_str: str) -> List[VersionRule]:
        """Converte strings como '^1.0,!=1.2' ou '>=1.0 || <2.0' em regras"""
        rules = []
        if not spec_str:
            return rules
        
        normalized_spec = spec_str.replace("||", ",")
        
        # Separa por vírgula
        parts = [p.strip() for p in normalized_spec.split(',')]
        
        for part in parts:
            if not part: continue
            
            found_op = False
            # Verifica operadores (ordem importa: >= antes de >)
            for op in ["==", ">=", "<=", "!=", ">", "<", "~=", "^", "~"]:
                if part.startswith(op):
                    ver = part[len(op):].strip()
                    rules.append(VersionRule(operator=op, version=ver))
                    found_op = True
                    break
            
            if not found_op:
                # Fallback: se começa com dígito ou *, assume ==
                if part[0].isdigit() or part[0] == '*':
                     rules.append(VersionRule(operator="==", version=part))

        return rules

    def _process_poetry_item(self, name: str, value: Any, dep_list: List[Dependency], category: DependencyCategory):
        """Processa um item individual"""
        raw_specifier = None
        extras = []
        marker = None
        dep_type = DependencyType.PACKAGE
        source_url = None
        source_path = None
        git_ref = None

        if isinstance(value, str):
            raw_specifier = value
        
        elif isinstance(value, dict):
            raw_specifier = value.get("version", None)
            extras = value.get("extras", [])
            marker = value.get("markers", None) 
            
            if "git" in value:
                dep_type = DependencyType.GIT
                source_url = value["git"]
                git_ref = value.get("rev") or value.get("tag") or value.get("branch")
            elif "path" in value:
                dep_type = DependencyType.PATH
                source_path = value["path"]
            elif "url" in value:
                dep_type = DependencyType.URL
                source_url = value["url"]
        
        else:
            return
        
        is_valid_dependency = (
            raw_specifier is not None or 
            source_url is not None or 
            source_path is not None
        )

        if not is_valid_dependency:
            return

        parsed_rules = []
        if raw_specifier:
            parsed_rules = self._parse_specifier_string(raw_specifier)

        dep_list.append(Dependency(
            name=name,
            source_file=self.filename,
            dependency_type=dep_type,
            category=category,
            raw_specifier=raw_specifier,
            version_rules=parsed_rules,
            marker=marker,
            extras_requested=extras,
            source_url=source_url,
            source_path=source_path,
            git_ref=git_ref
        ))