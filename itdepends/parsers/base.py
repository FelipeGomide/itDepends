from abc import ABC, abstractmethod
from typing import List
import logging
from itdepends.models import Dependency

logger = logging.getLogger("itdepends.parser")

class BaseParser(ABC):
    def __init__(self, content: str, filename: str):
        self.content = content
        self.filename = filename

    @abstractmethod
    def parse(self) -> List[Dependency]:
        """Método abstrato que deve ser implementado pelos parsers concretos"""
        pass