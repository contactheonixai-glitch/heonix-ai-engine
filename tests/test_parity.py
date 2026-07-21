"""Structural guard: every top-level def/class from the GEN-4 monolith must
exist exactly once across the GEN-5 package. Catches accidental deletions or
duplications in future refactors."""
import ast
import glob
import json
import os

HERE = os.path.dirname(__file__)
MANIFEST = os.path.join(HERE, "..", "tools", "parity_manifest.json")
EXPECTED_EXTRA = {"_publish_db_pool", "register", "publish"}   # GEN-5 additions


def test_all_gen4_symbols_present_exactly_once():
    want = set(json.load(open(MANIFEST))["top_level_defs_and_classes"])
    seen = {}
    pkg = os.path.join(HERE, "..", "heonix")
    for f in glob.glob(os.path.join(pkg, "**", "*.py"), recursive=True):
        tree = ast.parse(open(f).read())
        for n in tree.body:
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
                assert n.name not in seen, f"{n.name} duplicated: {seen[n.name]} + {f}"
                seen[n.name] = f
    missing = want - set(seen)
    extra = set(seen) - want - EXPECTED_EXTRA
    assert not missing, f"lost from GEN-4: {sorted(missing)}"
    assert not extra, f"unexpected new top-level symbols: {sorted(extra)}"
