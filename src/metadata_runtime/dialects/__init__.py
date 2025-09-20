"""Dialect macro registry for metadata SQL compilation."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict

from jinja2 import Environment


class MacroRegistryError(LookupError):
    """Raised when macro resolution fails."""


@dataclass(frozen=True)
class MacroModule:
    """Container for callable macros loaded from a template."""

    functions: Dict[str, Callable[..., Any]]


class MacroRegistry:
    """Loads and resolves macros for SQL dialects."""

    def __init__(self) -> None:
        self._macros: Dict[str, Dict[str, Callable[..., Any]]] = {}

    def register(self, dialect: str, name: str, func: Callable[..., Any]) -> None:
        """Register a macro callable for a given dialect."""
        dialect_map = self._macros.setdefault(dialect, {})
        dialect_map[name] = func

    def load_from_file(self, dialect: str, path: Path) -> None:
        """Load macros defined in a Jinja2 template file."""
        if not path.exists():
            raise FileNotFoundError(f"Macro file not found: {path}")
        source = path.read_text(encoding="utf-8")
        env = Environment(autoescape=False)
        module = env.from_string(source).module
        functions = {
            name: getattr(module, name)
            for name in dir(module)
            if not name.startswith("_") and callable(getattr(module, name))
        }
        if not functions:
            raise MacroRegistryError(f"No macros found in {path}")
        for name, func in functions.items():
            self.register(dialect, name, func)

    def get_namespace(self, dialect: str) -> Dict[str, Callable[..., Any]]:
        """Return callable namespace for the dialect."""
        try:
            return self._macros[dialect]
        except KeyError as exc:
            raise MacroRegistryError(f"No macros registered for dialect '{dialect}'") from exc

    def resolve(self, dialect: str, name: str) -> Callable[..., Any]:
        """Retrieve a macro callable by dialect and name."""
        namespace = self.get_namespace(dialect)
        try:
            return namespace[name]
        except KeyError as exc:
            raise MacroRegistryError(f"Macro '{name}' not defined for dialect '{dialect}'") from exc


__all__ = ["MacroRegistry", "MacroRegistryError"]
