import re
from typing import List
from packaging.requirements import Requirement, InvalidRequirement
from packaging.utils import canonicalize_name
from itdepends.models import Dependency, DependencyType, DependencyCategory, VersionRule
from itdepends.parsers.base import BaseParser, logger

# Detecta editáveis
EDITABLE_RE = re.compile(r'^(?:-e|--editable)\s*', re.I)

# Detecta VCS: git+, git:// ou estilo SCP (git@github.com:...)
VCS_START_RE = re.compile(r'^(git\+|hg\+|bzr\+|svn\+|git://|git@)', re.I)

# Detecta URL HTTP/HTTPS/FTP
URL_START_RE = re.compile(r'^(https?|ftp)://', re.I)

# Extrai o egg=nome
EGG_RE = re.compile(r'(?:#|&|\?)egg=([^&\s]+)')

class RequirementsParser(BaseParser):
    def parse(self) -> List[Dependency]:
        dependencies = []
        if not self.content:
            return []

        for i, raw_line in enumerate(self.content.splitlines()):
            line = raw_line.strip()
            name = None 

            if not line or line.startswith('#'):
                continue

            if line.startswith(('-r', '-c', '-i', '--extra-index-url', '--trusted-host', '--find-links')):
                continue

            # Tratamento de Editable
            is_editable = False
            if EDITABLE_RE.match(line):
                is_editable = True
                line = EDITABLE_RE.sub('', line).strip()

            # Remoção de Comentários
            if '#' in line:
                if 'egg=' not in line and 'subdirectory=' not in line:
                    hash_idx = line.find('#')
                    if hash_idx != -1:
                        line = line[:hash_idx].strip()
            
            # Se linha começar  com VCS (git+, git@) evita que Requirement("git@...") ache que o pacote se chama "git"
            if VCS_START_RE.match(line):
                self._process_vcs_match(dependencies, line, i)
                continue

            try:
                req = Requirement(line)
                
                dep_type = DependencyType.PACKAGE
                source_url, source_path, git_ref = None, None, None
                
                name = req.name
                
                if req.url:
                    source_url = req.url
                    if not name:
                        egg_match = EGG_RE.search(req.url)
                        if egg_match:
                            name = egg_match.group(1)
                    
                    if VCS_START_RE.match(req.url):
                        dep_type = DependencyType.GIT
                        git_ref = self._extract_git_ref(req.url)
                    elif "file://" in req.url:
                        dep_type = DependencyType.PATH
                        source_path = req.url.replace("file://", "")
                    elif URL_START_RE.match(req.url):
                        dep_type = DependencyType.URL
                
                elif is_editable:
                    dep_type = DependencyType.EDITABLE
                    source_path = line
                
                if not name:
                    name = self._extract_name_fallback(line)

                self._add_dep(dependencies, name, dep_type, req.specifier, req.marker, req.extras, source_url, source_path, git_ref, i)

            except InvalidRequirement:
                # Fallback para URLs diretas, Paths e Editáveis que falharam no Requirement
                fallback_type = DependencyType.PACKAGE
                fallback_path = None
                fallback_url = None
                fallback_ref = None
                
                if is_editable:
                    fallback_type = DependencyType.EDITABLE
                    fallback_path = line
                    name = self._extract_name_fallback(line)
                
                elif URL_START_RE.match(line):
                    fallback_type = DependencyType.URL
                    fallback_url = line
                
                elif line.startswith('file://'):
                    fallback_type = DependencyType.PATH
                    fallback_path = line.replace('file://', '')

                elif re.match(r'^(\.|\/|[a-zA-Z]:\\)', line):
                    fallback_type = DependencyType.PATH
                    fallback_path = line
                
                else:
                    logger.warning(f"Ignorando linha inválida em {self.filename}:{i+1}: {line}")
                    continue

                if not name: 
                    egg_match = EGG_RE.search(line)
                    name = canonicalize_name(egg_match.group(1)) if egg_match else None
                
                if not name:
                    name = self._extract_name_fallback(line)

                self._add_dep(dependencies, name, fallback_type, None, None, [], fallback_url, fallback_path, fallback_ref, i)

            except Exception as e:
                logger.error(f"Erro crítico no parser {self.filename}:{i+1}: {e}")

        return dependencies

    def _process_vcs_match(self, deps, line, i):
        """Processa linhas que sabemos ser VCS (começam com git+, git@, etc)"""
        url = line
        ref = self._extract_git_ref(line)
        
        # Tenta extrair nome do egg
        egg_match = EGG_RE.search(line)
        name = egg_match.group(1) if egg_match else None
        
        if not name:
            name = self._extract_name_fallback(line)
            
        self._add_dep(deps, name, DependencyType.GIT, None, None, [], url, None, ref, i)

    def _extract_git_ref(self, url: str) -> str:
        clean_url = url.split('#')[0]
        if '@' not in clean_url:
            return None

        part1, sep, part2 = clean_url.rpartition('@')
        if sep:
            if '/' in part2 or 'github.com' in part2 or 'gitlab.com' in part2 or 'bitbucket.org' in part2:
                return None
            return part2
        return None

    def _extract_name_fallback(self, text: str) -> str:
        clean_seg = text.split('#')[0].strip().rstrip('/')
        extensions = ['.git', '.tar.gz', '.tar.bz2', '.whl', '.zip', '.tgz']
        normalized = clean_seg.lower() 
        for ext in extensions:
            if normalized.endswith(ext):
                clean_seg = clean_seg[:-len(ext)]
                normalized = normalized[:-len(ext)] 
        name = clean_seg.split('/')[-1].split('\\')[-1]
        return canonicalize_name(name) or "unknown"

    def _add_dep(self, deps, name, dtype, specifiers, marker, extras, url, path, ref, line_idx):
        name = canonicalize_name(name)
        rules = []
        if specifiers:
            for spec in specifiers:
                rules.append(VersionRule(operator=spec.operator, version=spec.version))
        
        deps.append(Dependency(
            name=name,
            source_file=self.filename,
            dependency_type=dtype,
            category=DependencyCategory.MAIN,
            raw_specifier=str(specifiers) if specifiers else None,
            version_rules=rules,
            marker=str(marker) if marker else None,
            extras_requested=list(extras) if extras else [],
            source_url=url,
            source_path=path,
            git_ref=ref,
            line_number=line_idx + 1
        ))