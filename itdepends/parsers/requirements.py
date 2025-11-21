from typing import List
from packaging.requirements import Requirement, InvalidRequirement
from itdepends.models import Dependency
from itdepends.parsers.base import BaseParser, logger

class RequirementsParser(BaseParser):
    def parse(self) -> List[Dependency]:
        dependencies = []
        if not self.content:
            return []

        for i, line in enumerate(self.content.splitlines()):
            line = line.strip()
            
            # Ignora vazio e comentários
            if not line or line.startswith('#'):
                continue

            # (Erro 2): Tratamento de Referências Recursivas (-r) e Constraints (-c)
            if line.startswith('-r') or line.startswith('-c'):
                ref_file = line.split()[-1]
                # Opcional: Adicionar uma dependência especial ou apenas logar
                logger.info(f"Referência recursiva encontrada em {self.filename}: {line}")
                # Nota: Não podemos parsear o arquivo referenciado pois não temos acesso ao disco,
                # apenas ao conteúdo string do commit atual.
                continue
            
            # Ignora outras flags do pip (ex: -e ., --extra-index-url)
            if line.startswith('-'):
                continue

            # Remove comentários inline (ex: flask==1.0 # importante)
            line_clean = line.split('#')[0].strip()

            try:
                req = Requirement(line_clean)
                
                specifier_str = str(req.specifier) if req.specifier else "*"
                # Lógica simples para extrair versão exata se houver '=='
                version_fixed = None
                if "==" in specifier_str:
                    version_fixed = specifier_str.replace("==", "").split(",")[0].strip()

                dependencies.append(Dependency(
                    name=req.name,
                    specifier=specifier_str,
                    version=version_fixed,
                    marker=str(req.marker) if req.marker else None,
                    source_file=self.filename,
                    line_number=i + 1,
                    category="main",
                    extras=list(req.extras)
                ))

            except InvalidRequirement:
                logger.warning(f"Requirement inválido em {self.filename}:{i+1} -> '{line}'")
            except Exception as e:
                logger.debug(f"Erro parsing linha {i+1}: {e}")

        return dependencies