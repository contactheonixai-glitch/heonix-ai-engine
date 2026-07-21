"""HEONIX GEN-5 — late-binding registry.

Three module-level globals in the original single file are rebound at runtime
(`_db_pool` in startup(), `_rag_ready` in init_rag(), `_openai_client` in
_init_ai_providers()). A plain `from x import name` would freeze the pre-boot
value in every consumer module. Consumers therefore register here, and the
owning module publishes the live object once — before any request is served —
which stamps it into every registered module's namespace. Zero call sites in
the original code needed rewriting for this.
"""
import sys
from typing import Any, Dict, Set

_consumers: Dict[str, Set[str]] = {}


def register(name: str, module_name: str) -> None:
    _consumers.setdefault(name, set()).add(module_name)


def publish(name: str, value: Any) -> None:
    for mod_name in _consumers.get(name, ()):
        mod = sys.modules.get(mod_name)
        if mod is not None:
            setattr(mod, name, value)
