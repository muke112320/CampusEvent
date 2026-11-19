from __future__ import annotations

import pathlib
import re
import sqlite3
import sys

root = pathlib.Path("app")
py_files = sorted(root.rglob("*.py"))
src_lines = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in py_files)
test_files = sorted(pathlib.Path("tests").glob("test_*.py"))
test_lines = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in test_files)
classes = []
for p in py_files:
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"class\s+(\w+)", line)
        if m:
            classes.append(m.group(1))
print("app py files:", len(py_files))
print("app lines:", src_lines)
print("test files:", len(test_files), "test lines:", test_lines)
print("classes:", len(classes))
print(", ".join(classes))
import flask
import pytest
print("versions:", sys.version.split()[0], flask.__version__, pytest.__version__, sqlite3.sqlite_version)
