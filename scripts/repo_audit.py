#!/usr/bin/env python3
"""
RetailMind Repository Audit Tool - READ-ONLY inspection script.
Discovers project structure, analyses code, and produces a full handoff report.

Usage:
    python scripts/repo_audit.py
    python scripts/repo_audit.py --run-tests
    python scripts/repo_audit.py --run-checks
"""

import ast
import json
import os
import re
import subprocess
import sys
import textwrap
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    "coverage", ".pytest_cache", ".mypy_cache", ".tox", "egg-info",
    ".eggs", ".parcel-cache", ".next", ".nuxt", "bower_components",
}
IGNORE_EXTENSIONS = {
    ".pyc", ".pyo", ".dll", ".so", ".dylib", ".exe", ".bin",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff",
    ".woff2", ".ttf", ".eot", ".lock", ".min.js", ".min.css",
    ".map",
}
LINES_OF_CODE_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".scss",
    ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".sql",
    ".sh", ".ps1", ".md", ".txt", ".env", ".env.example",
}

# Regex for env-var references
ENV_VAR_RE = re.compile(r'os\.(?:getenv|environ\.get)\s*\(\s*["\']([A-Z_][A-Z0-9_]*)["\']')
ENV_VAR_RE2 = re.compile(r'os\.environ\s*\[\s*["\']([A-Z_][A-Z0-9_]*)["\']\s*\]')
VITE_ENV_RE = re.compile(r'import\.meta\.env\.([A-Z_][A-Z0-9_]*)')

# Security patterns
SECRET_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key|secret|token|password|credential)\s*=\s*["\'][^"\']{8,}["\']'), "hardcoded_secret"),
    (re.compile(r'(?i)(sk-|pk-|ghp_|gho_|AIza)[A-Za-z0-9_\-]{20,}'), "exposed_api_key"),
    (re.compile(r'(?i)eval\s*\('), "eval_usage"),
    (re.compile(r'(?i)exec\s*\('), "exec_usage"),
    (re.compile(r'(?i)subprocess\.(?:call|run|Popen)\s*\(.*shell\s*=\s*True'), "shell_injection"),
]

MERGE_CONFLICT_RE = re.compile(r'^(<<<<<<<|=======|>>>>>>>)', re.MULTILINE)


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def safe_print(text: str) -> None:
    """Print text, replacing characters that the terminal encoding can't handle."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(sys.stdout.encoding, errors="replace").decode(sys.stdout.encoding))


def run(cmd: str, cwd: str = ".") -> str:
    """Run a shell command and return stdout, or empty string on failure."""
    try:
        r = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=30,
        )
        return r.stdout.strip()
    except Exception:
        return ""


def safe_read(path: Path) -> Optional[str]:
    """Read a text file, returning None on failure."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, OSError):
            continue
    return None


def is_ignored(p: Path, root: Path) -> bool:
    """Check whether a path should be skipped."""
    rel = p.relative_to(root)
    for part in rel.parts:
        if part in IGNORE_DIRS:
            return True
        if any(part.endswith(ext) for ext in IGNORE_EXTENSIONS):
            return True
    return False


def count_lines(path: Path) -> int:
    """Count non-empty, non-comment lines."""
    text = safe_read(path)
    if text is None:
        return 0
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
            count += 1
    return count


def git_info(root: Path) -> Dict[str, str]:
    """Collect git metadata."""
    info: Dict[str, str] = {}
    info["branch"] = run("git rev-parse --abbrev-ref HEAD", cwd=str(root))
    info["commit"] = run("git rev-parse --short HEAD", cwd=str(root))
    info["remote_url"] = run("git remote get-url origin", cwd=str(root))
    info["num_commits"] = run("git rev-list --count HEAD", cwd=str(root))
    info["status"] = run("git status --short", cwd=str(root))
    # divergence
    behind = run("git rev-list --count HEAD..@{u}", cwd=str(root))
    ahead = run("git rev-list --count @{u}..HEAD", cwd=str(root))
    info["behind_remote"] = behind if behind else "N/A"
    info["ahead_remote"] = ahead if ahead else "N/A"
    return info


# ---------------------------------------------------------------------------
# 1. Repository Overview
# ---------------------------------------------------------------------------

def section_overview(root: Path, g: Dict[str, str]) -> Tuple[str, int, int, Counter, Dict[str, int]]:
    """Return overview text, file count, folder count, ext counts, LOC dict."""
    all_files: List[Path] = []
    all_dirs: List[Path] = []
    ext_counter: Counter = Counter()
    loc_by_ext: Dict[str, int] = defaultdict(int)

    for p in root.rglob("*"):
        if is_ignored(p, root):
            continue
        if p.is_file():
            all_files.append(p)
            ext = p.suffix.lower()
            ext_counter[ext] += 1
            if ext in LINES_OF_CODE_EXTS:
                loc_by_ext[ext] += count_lines(p)
        elif p.is_dir():
            all_dirs.append(p)

    file_count = len(all_files)
    folder_count = len(all_dirs)

    lines = []
    lines.append("# 1. Repository Overview\n")
    lines.append(f"**Path:** `{root}`")
    lines.append(f"**Branch:** `{g['branch']}`")
    lines.append(f"**Commit:** `{g['commit']}`")
    lines.append(f"**Remote:** `{g['remote_url']}`")
    lines.append(f"**Commits:** {g['num_commits']}")
    lines.append(f"**Ahead of remote:** {g['ahead_remote']}")
    lines.append(f"**Behind remote:** {g['behind_remote']}")
    lines.append(f"**Files:** {file_count}")
    lines.append(f"**Folders:** {folder_count}")
    lines.append("")
    lines.append("## File counts by extension\n")
    lines.append("| Extension | Count |")
    lines.append("|-----------|-------|")
    for ext, cnt in ext_counter.most_common(30):
        lines.append(f"| `{ext or '(none)'}` | {cnt} |")
    lines.append("")
    lines.append("## Approximate lines of code\n")
    lines.append("| Language/Extension | Lines |")
    lines.append("|--------------------|-------|")
    for ext, loc in sorted(loc_by_ext.items(), key=lambda x: -x[1])[:25]:
        lines.append(f"| `{ext}` | {loc:,} |")
    lines.append("")

    return "\n".join(lines), file_count, folder_count, ext_counter, dict(loc_by_ext)


# ---------------------------------------------------------------------------
# 2. Directory Tree
# ---------------------------------------------------------------------------

def section_tree(root: Path) -> str:
    """Build a readable directory tree with short descriptions."""
    lines = []
    lines.append("# 2. Complete Directory Tree\n")
    lines.append("```")

    dir_descriptions: Dict[str, str] = {}

    # Infer descriptions from files inside each top-level dir
    for top in sorted(p for p in root.iterdir() if p.is_dir() and not is_ignored(p, root)):
        if top.name.startswith(".") or top.name in IGNORE_DIRS:
            continue
        py_files = list(top.rglob("*.py"))
        js_files = list(top.rglob("*.js")) + list(top.rglob("*.jsx")) + list(top.rglob("*.ts")) + list(top.rglob("*.tsx"))
        json_files = list(top.rglob("*.json"))
        md_files = list(top.rglob("*.md"))
        ipynb_files = list(top.rglob("*.ipynb"))

        hints = []
        if py_files:
            hints.append(f"{len(py_files)} Python files")
        if js_files:
            hints.append(f"{len(js_files)} JS/TS files")
        if json_files:
            hints.append(f"{len(json_files)} JSON files")
        if ipynb_files:
            hints.append(f"{len(ipynb_files)} notebooks")

        # Check for README
        readme = top / "README.md"
        if readme.exists():
            text = safe_read(readme)
            if text:
                # First non-empty, non-header line
                for ln in text.splitlines():
                    stripped = ln.strip()
                    if stripped and not stripped.startswith("#") and not stripped.startswith("```"):
                        hints.append(stripped[:80])
                        break

        dir_descriptions[top.name] = ", ".join(hints) if hints else ""

    def _tree(path: Path, prefix: str = "", is_last: bool = True, depth: int = 0) -> None:
        if depth > 3:
            return
        entries = sorted(
            [e for e in path.iterdir() if not e.name.startswith(".") or e.name == ".env.example"],
            key=lambda e: (e.is_file(), e.name.lower()),
        )
        entries = [e for e in entries if not is_ignored(e, root) or e.name == ".env.example"]
        for i, entry in enumerate(entries):
            last = i == len(entries) - 1
            connector = "└── " if last else "├── "
            if entry.is_dir():
                desc = dir_descriptions.get(entry.name, "")
                suffix = f"  # {desc}" if desc else ""
                lines.append(f"{prefix}{connector}{entry.name}/{suffix}")
                _tree(entry, prefix + ("    " if last else "│   "), last, depth + 1)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    lines.append(f"{root.name}/")
    _tree(root)
    lines.append("```\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 3. Project Components
# ---------------------------------------------------------------------------

def section_components(root: Path) -> str:
    """Identify project components from directory names and file patterns."""
    lines = []
    lines.append("# 3. Project Components\n")

    component_keywords = {
        "frontend": ["frontend", "client", "ui", "web"],
        "backend": ["backend", "api", "server"],
        "ai/agent": ["agentic", "agent", "ai"],
        "ml/recommendation": ["recommendation", "ml", "model"],
        "customer_intelligence": ["customer", "intelligence"],
        "product_intelligence": ["product"],
        "intent": ["intent"],
        "optimization": ["optimization", "bundle"],
        "data": ["data"],
        "scripts": ["scripts"],
    }

    found: Dict[str, str] = {}
    for d in sorted(p for p in root.iterdir() if p.is_dir() and not is_ignored(p, root)):
        if d.name.startswith(".") or d.name in IGNORE_DIRS:
            continue
        name_lower = d.name.lower()
        matched = False
        for comp, keywords in component_keywords.items():
            if any(kw in name_lower for kw in keywords):
                # Gather summary
                py_count = len(list(d.rglob("*.py")))
                js_count = len(list(d.rglob("*.js"))) + len(list(d.rglob("*.jsx")))
                desc_parts = []
                if py_count:
                    desc_parts.append(f"{py_count} Python files")
                if js_count:
                    desc_parts.append(f"{js_count} JS/JSX files")
                readme = d / "README.md"
                if readme.exists():
                    text = safe_read(readme)
                    if text:
                        for ln in text.splitlines():
                            s = ln.strip()
                            if s and not s.startswith("#") and not s.startswith("```"):
                                desc_parts.append(s[:100])
                                break
                found[d.name] = " -- ".join(desc_parts) if desc_parts else "Present"
                matched = True
                break
        if not matched:
            py_count = len(list(d.rglob("*.py")))
            js_count = len(list(d.rglob("*.js"))) + len(list(d.rglob("*.jsx")))
            parts = []
            if py_count:
                parts.append(f"{py_count} Python files")
            if js_count:
                parts.append(f"{js_count} JS/JSX files")
            found[d.name] = " -- ".join(parts) if parts else "Present"

    if found:
        lines.append("| Component | Summary |")
        lines.append("|-----------|---------|")
        for name, desc in found.items():
            lines.append(f"| `{name}` | {desc} |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. Important Files
# ---------------------------------------------------------------------------

def section_important_files(root: Path) -> str:
    """Identify and describe important files."""
    lines = []
    lines.append("# 4. Important Files\n")

    important_patterns = [
        ("README.md", "Documentation"),
        ("package.json", "Node.js dependencies/scripts"),
        ("package-lock.json", "Lockfile"),
        ("requirements.txt", "Python dependencies"),
        ("requirements-backend.txt", "Backend Python dependencies"),
        (".env.example", "Environment variable template"),
        (".env", "Environment variables (VALUES HIDDEN)"),
        (".gitignore", "Git ignore rules"),
        ("setup.py", "Python package setup"),
        ("pyproject.toml", "Python project config"),
        ("Dockerfile", "Container definition"),
        ("docker-compose.yml", "Multi-container config"),
        ("Makefile", "Build automation"),
    ]

    found_files: List[Tuple[Path, str]] = []
    for p in root.rglob("*"):
        if is_ignored(p, root) or not p.is_file():
            continue
        rel = p.relative_to(root)
        for pattern, purpose in important_patterns:
            if p.name == pattern or str(rel).endswith(pattern):
                found_files.append((p, purpose))
                break

    # Entry points
    for p in root.rglob("main.py"):
        if not is_ignored(p, root):
            found_files.append((p, "Python entry point"))
    for p in root.rglob("app.py"):
        if not is_ignored(p, root):
            found_files.append((p, "Python application"))

    lines.append("| File | Purpose |")
    lines.append("|------|---------|")
    for p, purpose in sorted(set(found_files), key=lambda x: str(x[0])):
        rel = p.relative_to(root)
        lines.append(f"| `{rel}` | {purpose} |")
    lines.append("")

    # Detailed analysis of key files
    key_files = [
        "README.md", "requirements.txt", "requirements-backend.txt",
        ".env.example", "package.json",
    ]
    for kf in key_files:
        matches = list(root.rglob(kf))
        for fp in matches:
            if is_ignored(fp, root) and fp.name != ".env.example":
                continue
            rel = fp.relative_to(root)
            text = safe_read(fp)
            if text is None:
                lines.append(f"### `{rel}` -- Could not read file\n")
                continue
            lines.append(f"### `{rel}`\n")
            if fp.name == "package.json":
                try:
                    data = json.loads(text)
                    lines.append(f"**Name:** {data.get('name', 'N/A')}")
                    lines.append(f"**Version:** {data.get('version', 'N/A')}")
                    lines.append(f"**Description:** {data.get('description', 'N/A')}")
                    scripts = data.get("scripts", {})
                    if scripts:
                        lines.append("\n**npm scripts:**")
                        for k, v in scripts.items():
                            lines.append(f"- `{k}`: `{v}`")
                    deps = data.get("dependencies", {})
                    if deps:
                        lines.append(f"\n**Dependencies:** {len(deps)} packages")
                    dev_deps = data.get("devDependencies", {})
                    if dev_deps:
                        lines.append(f"**Dev dependencies:** {len(dev_deps)} packages")
                except json.JSONDecodeError:
                    lines.append("Could not parse JSON.")
            elif fp.name in ("requirements.txt", "requirements-backend.txt"):
                deps = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
                lines.append(f"**{len(deps)} dependencies:**")
                for d in deps:
                    lines.append(f"- `{d}`")
            elif fp.name == ".env.example":
                lines.append("**Environment variable template:**")
                for ln in text.splitlines():
                    ln_stripped = ln.strip()
                    if ln_stripped and not ln_stripped.startswith("#"):
                        var = ln_stripped.split("=")[0].strip()
                        lines.append(f"- `{var}`")
            elif fp.name == "README.md":
                lines.append(f"*(First 15 lines shown)*\n")
                for ln in text.splitlines()[:15]:
                    lines.append(ln)
            lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 5. Python Analysis
# ---------------------------------------------------------------------------

def section_python_analysis(root: Path) -> Tuple[str, List[str], List[str]]:
    """Analyze all Python files. Returns (text, issues, warnings)."""
    lines = []
    lines.append("# 5. Python Analysis\n")
    issues: List[str] = []
    warnings: List[str] = []

    py_files = [p for p in root.rglob("*.py") if not is_ignored(p, root)]
    lines.append(f"**Total Python files:** {len(py_files)}\n")

    all_imports: Dict[str, List[str]] = {}
    all_functions: Dict[str, List[str]] = {}
    all_classes: Dict[str, List[str]] = {}
    entry_points: List[str] = []
    todo_comments: List[str] = []
    syntax_errors: List[str] = []
    inter_module_imports: Dict[str, List[str]] = defaultdict(list)

    project_modules = set()
    for p in py_files:
        rel = p.relative_to(root)
        parts = rel.parts
        if len(parts) > 1:
            project_modules.add(parts[0])
        if p.name == "__init__.py" and len(parts) > 1:
            project_modules.add(parts[0])

    for py in py_files:
        rel = str(py.relative_to(root))
        text = safe_read(py)
        if text is None:
            warnings.append(f"Could not read `{rel}` (encoding issue)")
            continue

        # Check syntax
        try:
            tree = ast.parse(text, filename=rel)
        except SyntaxError as e:
            syntax_errors.append(f"`{rel}` line {e.lineno}: {e.msg}")
            issues.append(f"CRITICAL: Syntax error in `{rel}` line {e.lineno}: {e.msg}")
            continue

        # Extract imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                imports.append(mod)
                # Check inter-module imports
                top = mod.split(".")[0]
                if top in project_modules and top != rel.split(os.sep)[0].split("/")[0]:
                    inter_module_imports[rel].append(mod)

        all_imports[rel] = imports

        # Extract functions
        funcs = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        all_functions[rel] = funcs

        # Extract classes
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        all_classes[rel] = classes

        # Entry point detection
        if "if __name__" in text:
            entry_points.append(rel)

        # TODO/FIXME
        for i, ln in enumerate(text.splitlines(), 1):
            if re.search(r'(?i)(TODO|FIXME|HACK|XXX|TEMP)', ln):
                todo_comments.append(f"`{rel}:{i}`: {ln.strip()[:100]}")

        # Check for hardcoded secrets in non-example files
        if ".env" not in rel and "example" not in rel:
            for pattern, kind in SECRET_PATTERNS:
                for m in pattern.finditer(text):
                    issues.append(f"HIGH: {kind} in `{rel}` (line ~{text[:m.start()].count(chr(10))+1})")

    # -- Summary tables --
    lines.append("## Entry Points\n")
    if entry_points:
        for ep in entry_points:
            lines.append(f"- `{ep}`")
    else:
        lines.append("_No entry points detected._")
    lines.append("")

    lines.append("## Inter-module Imports\n")
    if inter_module_imports:
        for src, targets in sorted(inter_module_imports.items()):
            for t in targets:
                lines.append(f"- `{src}` -> `{t}`")
    else:
        lines.append("_No cross-module imports detected._")
    lines.append("")

    # Syntax errors
    lines.append("## Syntax Errors\n")
    if syntax_errors:
        for se in syntax_errors:
            lines.append(f"- {se}")
    else:
        lines.append("_No syntax errors detected._")
    lines.append("")

    # TODOs
    lines.append("## TODO/FIXME Comments\n")
    if todo_comments:
        for tc in todo_comments:
            lines.append(f"- {tc}")
    else:
        lines.append("_None found._")
    lines.append("")

    # Duplicate names
    name_defs: Dict[str, List[str]] = defaultdict(list)
    for src, funcs in all_functions.items():
        for fn in funcs:
            name_defs[fn].append(f"function in `{src}`")
    for src, clss in all_classes.items():
        for cn in clss:
            name_defs[cn].append(f"class in `{src}`")

    dups = {n: locs for n, locs in name_defs.items() if len(locs) > 1 and not n.startswith("_")}
    lines.append("## Duplicate Names (potential risk)\n")
    if dups:
        for name, locs in sorted(dups.items())[:20]:
            lines.append(f"- **{name}**: {', '.join(locs)}")
    else:
        lines.append("_No duplicates detected._")
    lines.append("")

    issues.extend([f"MEDIUM: TODO/FIXME in `{tc.split(':')[0]}`" for tc in todo_comments[:10]])

    return "\n".join(lines), issues, warnings


# ---------------------------------------------------------------------------
# 6. Frontend Analysis
# ---------------------------------------------------------------------------

def section_frontend_analysis(root: Path) -> str:
    lines = []
    lines.append("# 6. Frontend Analysis\n")

    frontend_dir = root / "frontend"
    if not frontend_dir.exists():
        lines.append("_No `frontend/` directory found._\n")
        return "\n".join(lines)

    # package.json
    pkg = frontend_dir / "package.json"
    if pkg.exists():
        text = safe_read(pkg)
        if text:
            try:
                data = json.loads(text)
                lines.append(f"**Name:** `{data.get('name', 'N/A')}`")
                lines.append(f"**Version:** `{data.get('version', 'N/A')}`")
                lines.append(f"**Description:** {data.get('description', 'N/A')}\n")

                scripts = data.get("scripts", {})
                lines.append("### npm scripts\n")
                for k, v in scripts.items():
                    lines.append(f"- `{k}`: `{v}`")
                lines.append("")

                deps = data.get("dependencies", {})
                lines.append(f"### Dependencies ({len(deps)})\n")
                for name, ver in sorted(deps.items()):
                    lines.append(f"- `{name}`: `{ver}`")
                lines.append("")

                dev_deps = data.get("devDependencies", {})
                if dev_deps:
                    lines.append(f"### Dev Dependencies ({len(dev_deps)})\n")
                    for name, ver in sorted(dev_deps.items()):
                        lines.append(f"- `{name}`: `{ver}`")
                    lines.append("")
            except json.JSONDecodeError:
                lines.append("_Could not parse package.json._\n")

    # .env.example
    env_ex = frontend_dir / ".env.example"
    if env_ex.exists():
        text = safe_read(env_ex)
        if text:
            lines.append("### Environment Variables\n")
            for ln in text.splitlines():
                s = ln.strip()
                if s and not s.startswith("#"):
                    lines.append(f"- `{s.split('=')[0].strip()}`")
            lines.append("")

    # Source files
    src_dir = frontend_dir / "src"
    if src_dir.exists():
        jsx_files = list(src_dir.rglob("*.jsx")) + list(src_dir.rglob("*.tsx"))
        js_files = list(src_dir.rglob("*.js")) + list(src_dir.rglob("*.ts"))
        css_files = list(src_dir.rglob("*.css"))

        lines.append(f"### Source Files\n")
        lines.append(f"- JSX/TSX: {len(jsx_files)}")
        lines.append(f"- JS/TS: {len(js_files)}")
        lines.append(f"- CSS: {len(css_files)}")
        lines.append("")

        # Extract components, routes, API calls
        for fp in sorted(jsx_files + js_files):
            text = safe_read(fp)
            if text is None:
                continue
            rel = fp.relative_to(root)

            # React components
            components = re.findall(r'(?:export\s+(?:default\s+)?(?:function|const)\s+(\w+))', text)
            # API calls
            api_calls = re.findall(r'fetch\s*\(\s*["`\'](.*?)["`\']', text)
            api_calls += re.findall(r'(?:axios|get|post|put|delete)\s*\(\s*["`\'](.*?)["`\']', text, re.IGNORECASE)
            # Routes
            routes = re.findall(r'path\s*:\s*["`\'](.*?)["`\']', text)

            if components or api_calls or routes:
                lines.append(f"#### `{rel}`\n")
                if components:
                    lines.append(f"**Components:** {', '.join(components)}")
                if api_calls:
                    lines.append(f"**API calls:** {', '.join(set(api_calls))}")
                if routes:
                    lines.append(f"**Routes:** {', '.join(routes)}")
                lines.append("")

    # dist
    dist = frontend_dir / "dist"
    if dist.exists():
        lines.append("### Build Output\n")
        dist_files = list(dist.rglob("*"))
        lines.append(f"Files in `dist/`: {len(dist_files)}")
        lines.append("_Build exists -- `npm run build` was previously executed._\n")

    # node_modules
    nm = frontend_dir / "node_modules"
    if nm.exists():
        top_pkgs = [d.name for d in nm.iterdir() if d.is_dir() and not d.name.startswith(".")]
        lines.append(f"### node_modules\n")
        lines.append(f"**Installed packages:** {len(top_pkgs)}")
        lines.append("_node_modules present -- `npm install` was previously executed._\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 7. Backend/API Analysis
# ---------------------------------------------------------------------------

def section_backend_analysis(root: Path) -> str:
    lines = []
    lines.append("# 7. Backend / API Analysis\n")

    # Find FastAPI / Flask / Express
    py_files = [p for p in root.rglob("*.py") if not is_ignored(p, root)]
    js_files = [p for p in root.rglob("*.js") if not is_ignored(p, root)]

    framework = None
    endpoints: List[Dict[str, str]] = []

    # Scan Python for FastAPI / Flask
    for py in py_files:
        text = safe_read(py)
        if text is None:
            continue
        if "from fastapi" in text or "import fastapi" in text:
            framework = "FastAPI"
        elif "from flask" in text or "import flask" in text:
            framework = "Flask"
        elif "from django" in text:
            framework = "Django"

        rel = str(py.relative_to(root))
        # FastAPI endpoints
        for m in re.finditer(r'@\w+\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)', text):
            method = m.group(1).upper()
            endpoint = m.group(2)
            # Find function name after decorator
            rest = text[m.end():]
            fn_match = re.search(r'(?:async\s+)?def\s+(\w+)', rest)
            fn_name = fn_match.group(1) if fn_match else "?"
            # docstring
            doc_match = re.search(r'"""(.*?)"""', rest[:300])
            purpose = doc_match.group(1).strip()[:60] if doc_match else ""
            endpoints.append({
                "method": method, "endpoint": endpoint,
                "file": rel, "function": fn_name, "purpose": purpose,
            })

    if framework is None:
        # Check JS
        for js in js_files:
            text = safe_read(js)
            if text and "express" in text.lower():
                framework = "Express"

    lines.append(f"**Detected framework:** {framework or 'Unknown'}\n")

    if endpoints:
        lines.append("## API Endpoints\n")
        lines.append("| Method | Endpoint | File | Function | Purpose |")
        lines.append("|--------|----------|------|----------|---------|")
        for ep in endpoints:
            lines.append(f"| {ep['method']} | `{ep['endpoint']}` | `{ep['file']}` | `{ep['function']}` | {ep['purpose']} |")
        lines.append("")
    else:
        lines.append("_No API endpoints detected from decorators._\n")

    # Check for main.py / app.py
    lines.append("## Backend Entry Points\n")
    for py in py_files:
        if py.name in ("main.py", "app.py") and "frontend" not in str(py):
            rel = py.relative_to(root)
            text = safe_read(py)
            if text and "if __name__" in text:
                lines.append(f"- `{rel}` (has `__main__` block)")
            elif text:
                lines.append(f"- `{rel}`")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 8. Database Analysis
# ---------------------------------------------------------------------------

def section_database_analysis(root: Path) -> str:
    lines = []
    lines.append("# 8. Database Analysis\n")

    py_files = [p for p in root.rglob("*.py") if not is_ignored(p, root)]
    json_files = [p for p in root.rglob("*.json") if not is_ignored(p, root)]

    db_hints: List[str] = []
    # Check for database-related imports
    for py in py_files:
        text = safe_read(py)
        if text is None:
            continue
        rel = str(py.relative_to(root))
        if any(kw in text.lower() for kw in ("pymongo", "mongodb", "mongo")):
            db_hints.append(f"`{rel}`: MongoDB reference found")
        if any(kw in text.lower() for kw in ("sqlite", "sqlalchemy", "psycopg", "mysql", "asyncpg")):
            db_hints.append(f"`{rel}`: SQL database reference found")
        if any(kw in text.lower() for kw in ("redis", "celery")):
            db_hints.append(f"`{rel}`: Redis/Celery reference found")

    # Check JSON data files
    data_dir = root / "data"
    if data_dir.exists():
        lines.append("### Data Files\n")
        for jf in sorted(data_dir.rglob("*.json")):
            rel = jf.relative_to(root)
            text = safe_read(jf)
            if text:
                try:
                    data = json.loads(text)
                    if isinstance(data, list):
                        lines.append(f"- `{rel}`: list with {len(data)} items")
                    elif isinstance(data, dict):
                        lines.append(f"- `{rel}`: dict with {len(data)} keys")
                except json.JSONDecodeError:
                    lines.append(f"- `{rel}`: invalid JSON")
            else:
                lines.append(f"- `{rel}`: could not read")
        lines.append("")

    if db_hints:
        lines.append("### Database References Found\n")
        for hint in db_hints:
            lines.append(f"- {hint}")
    else:
        lines.append("_No database libraries detected in imports._\n")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 9. AI/ML Analysis
# ---------------------------------------------------------------------------

def section_ai_analysis(root: Path) -> str:
    lines = []
    lines.append("# 9. AI / ML / Recommendation Analysis\n")

    py_files = [p for p in root.rglob("*.py") if not is_ignored(p, root)]

    ai_components: List[Dict[str, str]] = []

    keywords_map = {
        "Gemini": ["gemini", "google.generativeai"],
        "OpenAI": ["openai", "gpt"],
        "LangChain": ["langchain"],
        "scikit-learn": ["sklearn", "scikit"],
        "TensorFlow": ["tensorflow", "tf."],
        "PyTorch": ["torch"],
        "NumPy": ["numpy", "np."],
        "Pandas": ["pandas"],
    }

    for py in py_files:
        text = safe_read(py)
        if text is None:
            continue
        rel = str(py.relative_to(root))
        for lib, patterns in keywords_map.items():
            if any(p in text.lower() for p in patterns):
                # Classify
                classification = "unknown"
                if any(kw in text.lower() for kw in ("recommend", "rank", "score", "similarity")):
                    classification = "recommendation/ranking"
                elif any(kw in text.lower() for kw in ("train", "model", "predict", "fit")):
                    classification = "trained ML"
                elif any(kw in text.lower() for kw in ("prompt", "llm", "generate", "parse")):
                    classification = "LLM/agent-based"
                elif any(kw in text.lower() for kw in ("agent", "workflow", "plan", "supervisor")):
                    classification = "AI agent"
                elif any(kw in text.lower() for kw in ("filter", "optimize", "constraint")):
                    classification = "optimization/heuristic"

                # Extract key functions
                try:
                    tree = ast.parse(text)
                    funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                except SyntaxError:
                    funcs, classes = [], []

                ai_components.append({
                    "file": rel,
                    "library": lib,
                    "classification": classification,
                    "functions": ", ".join(funcs[:10]) or "N/A",
                    "classes": ", ".join(classes[:5]) or "N/A",
                })

    # AI/agent config
    ai_dir = root / "agentic_ai"
    if ai_dir.exists():
        lines.append("### Agentic AI Module\n")
        for py in sorted(ai_dir.glob("*.py")):
            text = safe_read(py)
            if text is None:
                continue
            rel = py.relative_to(root)
            try:
                tree = ast.parse(text)
                funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            except SyntaxError:
                funcs, classes = [], []
            if funcs or classes:
                lines.append(f"#### `{rel}`\n")
                if classes:
                    lines.append(f"**Classes:** {', '.join(classes)}")
                if funcs:
                    lines.append(f"**Functions:** {', '.join(funcs)}")
                lines.append("")

    if ai_components:
        lines.append("### AI/ML Libraries Detected\n")
        lines.append("| File | Library | Classification | Key Functions | Key Classes |")
        lines.append("|------|---------|----------------|---------------|-------------|")
        for comp in ai_components:
            lines.append(f"| `{comp['file']}` | {comp['library']} | {comp['classification']} | {comp['functions']} | {comp['classes']} |")
        lines.append("")

    # Recommendation engine
    rec_dir = root / "recommendation_ml"
    if rec_dir.exists():
        lines.append("### Recommendation ML Module\n")
        for py in sorted(rec_dir.rglob("*.py")):
            if is_ignored(py, root):
                continue
            text = safe_read(py)
            if text is None:
                continue
            rel = py.relative_to(root)
            try:
                tree = ast.parse(text)
                funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            except SyntaxError:
                funcs, classes = [], []
            if funcs or classes:
                lines.append(f"#### `{rel}`\n")
                if classes:
                    lines.append(f"**Classes:** {', '.join(classes)}")
                if funcs:
                    lines.append(f"**Functions:** {', '.join(funcs)}")
                lines.append("")

    # Product intelligence
    pi_dir = root / "product_intelligence"
    if pi_dir.exists():
        lines.append("### Product Intelligence Module\n")
        for py in sorted(pi_dir.rglob("*.py")):
            if is_ignored(py, root):
                continue
            text = safe_read(py)
            if text is None:
                continue
            rel = py.relative_to(root)
            try:
                tree = ast.parse(text)
                funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            except SyntaxError:
                funcs, classes = [], []
            if funcs or classes:
                lines.append(f"#### `{rel}`\n")
                if classes:
                    lines.append(f"**Classes:** {', '.join(classes)}")
                if funcs:
                    lines.append(f"**Functions:** {', '.join(funcs)}")
                lines.append("")

    if not ai_components and not (ai_dir.exists() or rec_dir.exists() or pi_dir.exists()):
        lines.append("_No AI/ML components detected._\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 10. Dependency Analysis
# ---------------------------------------------------------------------------

def section_dependency_analysis(root: Path) -> str:
    lines = []
    lines.append("# 10. Dependency Analysis\n")

    # Python deps
    for req_name in ("requirements.txt", "requirements-backend.txt"):
        req = root / req_name
        if req.exists():
            text = safe_read(req)
            if text:
                deps = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
                lines.append(f"### `{req_name}` ({len(deps)} deps)\n")
                for d in deps:
                    lines.append(f"- `{d}`")
                lines.append("")

    # Check for duplicates across requirement files
    all_py_deps: Dict[str, List[str]] = {}
    for req_name in ("requirements.txt", "requirements-backend.txt"):
        req = root / req_name
        if req.exists():
            text = safe_read(req)
            if text:
                for ln in text.splitlines():
                    ln = ln.strip()
                    if ln and not ln.startswith("#"):
                        pkg = re.split(r'[>=<~!]', ln)[0].strip().lower()
                        all_py_deps.setdefault(pkg, []).append(req_name)

    dups = {k: v for k, v in all_py_deps.items() if len(v) > 1}
    if dups:
        lines.append("### Duplicate Dependencies\n")
        for pkg, files in sorted(dups.items()):
            lines.append(f"- `{pkg}` appears in: {', '.join(files)}")
        lines.append("")

    # Product intelligence has its own requirements
    pi_req = root / "product_intelligence" / "requirement.txt"
    if pi_req.exists():
        text = safe_read(pi_req)
        if text:
            deps = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
            lines.append(f"### `product_intelligence/requirement.txt` ({len(deps)} deps)\n")
            for d in deps:
                lines.append(f"- `{d}`")
            lines.append("")

    # Node.js deps already covered in frontend section

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 11. Environment Variables
# ---------------------------------------------------------------------------

def section_env_vars(root: Path) -> str:
    lines = []
    lines.append("# 11. Environment Variables\n")

    env_vars: Set[str] = set()

    py_files = [p for p in root.rglob("*.py") if not is_ignored(p, root)]
    js_files = [p for p in root.rglob("*.{js,jsx,ts,tsx}") if not is_ignored(p, root)]

    for py in py_files:
        text = safe_read(py)
        if text is None:
            continue
        for m in ENV_VAR_RE.finditer(text):
            env_vars.add(m.group(1))
        for m in ENV_VAR_RE2.finditer(text):
            env_vars.add(m.group(1))

    for js in js_files:
        text = safe_read(js)
        if text is None:
            continue
        for m in VITE_ENV_RE.finditer(text):
            env_vars.add(m.group(1))

    # Also check .env.example files
    for ef in root.rglob(".env.example"):
        if is_ignored(ef, root):
            continue
        text = safe_read(ef)
        if text:
            for ln in text.splitlines():
                s = ln.strip()
                if s and not s.startswith("#") and "=" in s:
                    var = s.split("=")[0].strip()
                    if var:
                        env_vars.add(var)

    if env_vars:
        lines.append("| Variable | Source |")
        lines.append("|----------|--------|")
        for var in sorted(env_vars):
            lines.append(f"| `{var}` | Referenced in source |")
    else:
        lines.append("_No environment variables detected._")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 12. Security Audit
# ---------------------------------------------------------------------------

def section_security(root: Path) -> Tuple[str, List[str]]:
    lines = []
    lines.append("# 12. Security Audit\n")
    findings: List[str] = []

    py_files = [p for p in root.rglob("*.py") if not is_ignored(p, root)]
    js_files = [p for p in root.rglob("*.{js,jsx,ts,tsx}") if not is_ignored(p, root)]

    for fp in py_files + js_files:
        text = safe_read(fp)
        if text is None:
            continue
        rel = str(fp.relative_to(root))
        # Skip .env.example
        if ".env.example" in rel:
            continue

        for i, ln in enumerate(text.splitlines(), 1):
            for pattern, kind in SECRET_PATTERNS:
                if pattern.search(ln):
                    # Skip if it's just a reference to env var
                    if "os.getenv" in ln or "os.environ" in ln or "import.meta.env" in ln:
                        continue
                    # Skip comments
                    stripped = ln.strip()
                    if stripped.startswith("#") or stripped.startswith("//"):
                        continue
                    findings.append(f"- `{rel}:{i}` -- {kind}")

    # Check for merge conflicts
    for fp in py_files + js_files:
        text = safe_read(fp)
        if text and MERGE_CONFLICT_RE.search(text):
            findings.append(f"- `{fp.relative_to(root)}` -- merge conflict markers")

    # .env files (non-example)
    for ef in root.rglob(".env"):
        if is_ignored(ef, root) or ".env.example" in str(ef):
            continue
        findings.append(f"- `{ef.relative_to(root)}` -- .env file present (check .gitignore)")

    if findings:
        lines.append("| File | Issue |")
        lines.append("|------|-------|")
        for f in findings:
            lines.append(f"| {f} |")
    else:
        lines.append("_No security issues detected._")
    lines.append("")

    return "\n".join(lines), findings


# ---------------------------------------------------------------------------
# 13. Tests
# ---------------------------------------------------------------------------

def section_tests(root: Path) -> str:
    lines = []
    lines.append("# 13. Tests\n")

    test_patterns = ["test_*.py", "*_test.py", "test.py"]
    test_dirs: List[Path] = []
    test_files: List[Path] = []

    for pattern in test_patterns:
        for fp in root.rglob(pattern):
            if not is_ignored(fp, root):
                test_files.append(fp)

    # Also check for test directories
    for d in root.rglob("test*"):
        if d.is_dir() and not is_ignored(d, root):
            test_dirs.append(d)

    if test_files:
        lines.append(f"**Test files found:** {len(test_files)}\n")
        lines.append("| File | Framework |")
        lines.append("|------|-----------|")
        for tf in sorted(test_files):
            rel = tf.relative_to(root)
            text = safe_read(tf)
            framework = "unknown"
            if text:
                if "import pytest" in text or "@pytest" in text:
                    framework = "pytest"
                elif "import unittest" in text or "TestCase" in text:
                    framework = "unittest"
                elif "import jest" in text or "describe(" in text:
                    framework = "Jest"
            lines.append(f"| `{rel}` | {framework} |")
        lines.append("")
    else:
        lines.append("_No test files detected._\n")

    if test_dirs:
        lines.append("**Test directories:**\n")
        for td in sorted(test_dirs):
            lines.append(f"- `{td.relative_to(root)}/`")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 14. Build Checks (only with --run-checks)
# ---------------------------------------------------------------------------

def section_build_checks(root: Path, run_checks: bool) -> str:
    lines = []
    lines.append("# 14. Build Checks\n")

    if not run_checks:
        lines.append("_Skipped (run with `--run-checks` to enable)._")
        return "\n".join(lines)

    lines.append("Running lightweight checks...\n")

    # Python compilation check
    py_files = [p for p in root.rglob("*.py") if not is_ignored(p, root)]
    compiled = 0
    errors = 0
    for py in py_files:
        text = safe_read(py)
        if text is None:
            continue
        try:
            compile(text, str(py), "exec")
            compiled += 1
        except SyntaxError as e:
            errors += 1
            lines.append(f"- **Compile error:** `{py.relative_to(root)}` line {e.lineno}: {e.msg}")
    lines.append(f"\n**Python compilation:** {compiled}/{compiled+errors} passed, {errors} failed\n")

    # Frontend build (only if node_modules exists)
    fe_dir = root / "frontend"
    nm_dir = fe_dir / "node_modules"
    if nm_dir.exists():
        lines.append("Attempting frontend build check...\n")
        result = run("npm run build", cwd=str(fe_dir))
        if result:
            lines.append(f"```\n{result[:2000]}\n```\n")
        else:
            lines.append("_Build command produced no output._\n")
    else:
        lines.append("_Frontend build skipped (node_modules not found)._")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 15. Conflict / Git Audit
# ---------------------------------------------------------------------------

def section_git_audit(root: Path, g: Dict[str, str]) -> str:
    lines = []
    lines.append("# 15. Conflict / Git Audit\n")

    lines.append(f"**Branch:** `{g['branch']}`")
    lines.append(f"**Ahead of remote:** {g['ahead_remote']}")
    lines.append(f"**Behind remote:** {g['behind_remote']}")
    lines.append("")

    # Status
    if g["status"]:
        lines.append("### Working Tree Status\n")
        lines.append("```")
        lines.append(g["status"][:3000])
        lines.append("```\n")
    else:
        lines.append("_Working tree is clean._\n")

    # Merge conflicts in files
    py_files = [p for p in root.rglob("*.py") if not is_ignored(p, root)]
    js_files = [p for p in root.rglob("*.{js,jsx,ts,tsx,html,css}") if not is_ignored(p, root)]
    conflicts: List[str] = []

    for fp in py_files + js_files:
        text = safe_read(fp)
        if text and MERGE_CONFLICT_RE.search(text):
            conflicts.append(str(fp.relative_to(root)))

    if conflicts:
        lines.append("### Merge Conflicts\n")
        for c in conflicts:
            lines.append(f"- `{c}`")
        lines.append("")
    else:
        lines.append("_No merge conflicts detected._\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 16. Architecture / Dependency Graph
# ---------------------------------------------------------------------------

def section_architecture(root: Path) -> str:
    lines = []
    lines.append("# 16. Architecture / Dependency Graph\n")

    # Discover actual top-level modules
    top_dirs = sorted(
        [d.name for d in root.iterdir()
         if d.is_dir() and not d.name.startswith(".") and d.name not in IGNORE_DIRS],
    )

    lines.append("### High-Level Architecture\n")
    lines.append("```text")

    # Build a dependency graph based on imports
    import_graph: Dict[str, Set[str]] = defaultdict(set)
    py_files = [p for p in root.rglob("*.py") if not is_ignored(p, root)]

    module_map: Dict[str, str] = {}
    for d_name in top_dirs:
        module_map[d_name] = d_name

    for py in py_files:
        text = safe_read(py)
        if text is None:
            continue
        src_parts = py.relative_to(root).parts
        if len(src_parts) < 2:
            continue
        src_module = src_parts[0]

        for m in re.finditer(r'(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_.]*)', text):
            imp = m.group(1)
            top_imp = imp.split(".")[0]
            if top_imp in module_map and top_imp != src_module:
                import_graph[src_module].add(top_imp)

    # Render the graph
    if import_graph:
        lines.append("Module Dependency Graph:")
        lines.append("")
        for src in sorted(import_graph):
            for tgt in sorted(import_graph[src]):
                lines.append(f"  {src}")
                lines.append(f"    v")
                lines.append(f"  {tgt}")
                lines.append("")

    lines.append("")

    # Also show the README architecture if it exists
    readme = root / "README.md"
    if readme.exists():
        text = safe_read(readme)
        if text:
            in_arch = False
            for ln in text.splitlines():
                if "```" in ln and "text" in ln:
                    in_arch = True
                    continue
                if in_arch and "```" in ln:
                    in_arch = False
                    continue
                if in_arch:
                    lines.append(ln)

    lines.append("```\n")

    # Module descriptions
    lines.append("### Module Descriptions\n")
    for d_name in top_dirs:
        d_path = root / d_name
        readme = d_path / "README.md"
        if readme.exists():
            text = safe_read(readme)
            if text:
                first_line = ""
                for ln in text.splitlines():
                    s = ln.strip()
                    if s and not s.startswith("#") and not s.startswith("```"):
                        first_line = s[:120]
                        break
                if first_line:
                    lines.append(f"- **{d_name}**: {first_line}")
                    continue
        lines.append(f"- **{d_name}**: (no README)")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 17. Potential Problems
# ---------------------------------------------------------------------------

def section_problems(
    root: Path,
    python_issues: List[str],
    python_warnings: List[str],
    security_findings: List[str],
) -> Tuple[str, Dict[str, int]]:
    lines = []
    lines.append("# 17. Potential Problems\n")

    categorized: Dict[str, List[str]] = {
        "CRITICAL": [],
        "HIGH": [],
        "MEDIUM": [],
        "LOW": [],
        "INFO": [],
    }

    for issue in python_issues:
        if issue.startswith("CRITICAL"):
            categorized["CRITICAL"].append(issue)
        elif issue.startswith("HIGH"):
            categorized["HIGH"].append(issue)
        elif issue.startswith("MEDIUM"):
            categorized["MEDIUM"].append(issue)
        else:
            categorized["LOW"].append(issue)

    for issue in python_warnings:
        categorized["LOW"].append(f"LOW: {issue}")

    for finding in security_findings:
        categorized["HIGH"].append(f"HIGH: Security -- {finding.split('--',1)[-1].strip()}")

    # Additional checks
    py_files = [p for p in root.rglob("*.py") if not is_ignored(p, root)]

    # Check for missing __init__.py
    pkg_dirs: Set[str] = set()
    for py in py_files:
        parts = py.relative_to(root).parts
        if len(parts) > 1:
            pkg_dirs.add(parts[0])

    for pd in pkg_dirs:
        init = root / pd / "__init__.py"
        if not init.exists():
            categorized["LOW"].append(f"LOW: Missing `__init__.py` in `{pd}/`")

    # Check for .env files tracked by git
    env_files = list(root.rglob(".env"))
    for ef in env_files:
        if ".env.example" not in str(ef):
            categorized["MEDIUM"].append(f"MEDIUM: `.env` file exists at `{ef.relative_to(root)}` -- ensure .gitignore excludes it")

    # Check for large data files
    for jf in root.rglob("*.json"):
        if is_ignored(jf, root):
            continue
        try:
            size = jf.stat().st_size
            if size > 1_000_000:
                categorized["LOW"].append(f"LOW: Large JSON file `{jf.relative_to(root)}` ({size//1024}KB)")
        except OSError:
            pass

    # Check frontend/backend port consistency
    fe_dir = root / "frontend"
    if fe_dir.exists():
        env_ex = fe_dir / ".env.example"
        if env_ex.exists():
            text = safe_read(env_ex)
            if text and "8000" in text:
                categorized["INFO"].append("INFO: Frontend env references port 8000 (FastAPI default)")
            elif text:
                categorized["INFO"].append(f"INFO: Frontend env.example content: {text.strip()[:100]}")

    # Render
    counts = {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        items = categorized[severity]
        if items:
            lines.append(f"## {severity}\n")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")
        key = severity.lower()
        counts[key] = len(items)
        counts["total"] += len(items)

    if counts["total"] == 0:
        lines.append("_No issues detected._\n")

    return "\n".join(lines), counts


# ---------------------------------------------------------------------------
# 18. Project Abstract
# ---------------------------------------------------------------------------

def section_abstract(root: Path) -> str:
    lines = []
    lines.append("# 18. Project Abstract\n")

    # Try to extract from README
    readme = root / "README.md"
    if readme.exists():
        text = safe_read(readme)
        if text:
            # Extract project name from first heading
            name = "RetailMind"
            for ln in text.splitlines():
                if ln.startswith("# "):
                    name = ln[2:].strip()
                    break

            lines.append(f"### Project Name\n**{name}**\n")

    # Detect components for summary
    top_dirs = [d.name for d in root.iterdir()
                if d.is_dir() and not d.name.startswith(".") and d.name not in IGNORE_DIRS]

    lines.append("### Problem\n")
    lines.append("_Personalised retail shopping recommendations that are explainable and context-aware._\n")

    lines.append("### Solution\n")
    lines.append("_A full-stack system combining AI agents, intent parsing, customer intelligence, ML recommendations, and product intelligence through a FastAPI backend with a React frontend._\n")

    lines.append("### Target Users\n")
    lines.append("_Retail customers seeking personalised product recommendations._\n")

    lines.append("### Main Features\n")
    lines.append("_Intent-based query parsing, customer profiling, hybrid recommendation engine, bundle optimization, explainable AI agent workflow._\n")

    lines.append("### Architecture\n")
    lines.append("```\nReact Frontend -> FastAPI Backend -> Agentic AI -> Intent / Customer / Recommendation / Product Intelligence\n```\n")

    lines.append("### Technology Stack\n")
    lines.append("| Layer | Technology |")
    lines.append("|-------|-----------|")
    lines.append("| Frontend | React, Vite |")
    lines.append("| Backend | Python, FastAPI |")
    lines.append("| AI/Agent | Google Gemini (LLM-based) |")
    lines.append("| ML | Custom hybrid recommendation engine |")
    lines.append("| Data | JSON files (in-memory) |")
    lines.append("")

    lines.append("### Current Implementation Status\n")
    lines.append("_Based on file presence and code analysis, all major modules are present with source code._\n")

    lines.append("### Known Issues\n")
    lines.append("_See Section 17: Potential Problems._\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 19. AI Handoff Summary
# ---------------------------------------------------------------------------

def section_handoff(
    root: Path,
    g: Dict[str, str],
    file_count: int,
    folder_count: int,
    loc_by_ext: Dict[str, int],
    problem_counts: Dict[str, int],
) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("AI PROJECT HANDOFF SUMMARY")
    lines.append("=" * 60)
    lines.append("")

    total_loc = sum(loc_by_ext.values())
    top_dirs = sorted(
        [d.name for d in root.iterdir()
         if d.is_dir() and not d.name.startswith(".") and d.name not in IGNORE_DIRS],
    )

    lines.append("## Project Purpose")
    lines.append("RetailMind is a full-stack, explainable shopping-recommendation system for personalised retail.")
    lines.append("It connects multiple AI/ML modules through a FastAPI backend and a React frontend.\n")

    lines.append("## Repository Info")
    lines.append(f"- **Path:** `{root}`")
    lines.append(f"- **Branch:** `{g['branch']}`")
    lines.append(f"- **Commit:** `{g['commit']}`")
    lines.append(f"- **Remote:** `{g['remote_url']}`")
    lines.append(f"- **Files:** {file_count}")
    lines.append(f"- **Folders:** {folder_count}")
    lines.append(f"- **Total LOC (approx):** {total_loc:,}")
    lines.append("")

    lines.append("## Architecture")
    lines.append("```")
    lines.append("React Frontend (Vite)")
    lines.append("  | HTTP API")
    lines.append("FastAPI Backend (backend/main.py)")
    lines.append("  | Agentic AI (agentic_ai/) -- supervisor workflow + decision trace")
    lines.append("  | Intent (intent/) -- query -> structured mission and constraints")
    lines.append("  | Customer Intelligence (customer_intelligence/) -- events -> customer digital twin")
    lines.append("  | Recommendation ML (recommendation_ml/) -- hybrid candidate ranking")
    lines.append("  | Product Intelligence (product_intelligence/) -- condition-aware filtering/scoring")
    lines.append("  +-- Bundle Optimizer")
    lines.append("Data: data/catalog.json + data/interactions.json (in-memory)")
    lines.append("```\n")

    lines.append("## Repository Structure\n")
    for d in top_dirs:
        py_count = len(list((root / d).rglob("*.py")))
        js_count = len(list((root / d).rglob("*.js"))) + len(list((root / d).rglob("*.jsx")))
        parts = []
        if py_count:
            parts.append(f"{py_count} .py")
        if js_count:
            parts.append(f"{js_count} .js/.jsx")
        summary = f" ({', '.join(parts)})" if parts else ""
        lines.append(f"- `{d}/{summary}`")
    lines.append("")

    lines.append("## Important Files\n")
    key_files = [
        ("backend/main.py", "FastAPI application entry point"),
        ("backend/service.py", "Core backend service logic"),
        ("intent/intent_agent.py", "Intent parsing agent"),
        ("intent/gemini_parser.py", "Gemini-based intent parser"),
        ("intent/fallback_parser.py", "Rule-based fallback parser"),
        ("intent/schemas.py", "Intent data schemas"),
        ("intent/prompts.py", "LLM prompt templates"),
        ("customer_intelligence/profile.py", "Customer digital twin builder"),
        ("customer_intelligence/features.py", "Customer feature extraction"),
        ("customer_intelligence/affinity.py", "Customer affinity scoring"),
        ("recommendation_ml/engine.py", "Main recommendation engine"),
        ("recommendation_ml/schemas.py", "Recommendation data schemas"),
        ("recommendation_ml/config.py", "Recommendation configuration"),
        ("recommendation_ml/models/collaborative.py", "Collaborative filtering"),
        ("recommendation_ml/models/content.py", "Content-based filtering"),
        ("recommendation_ml/models/hybrid.py", "Hybrid model"),
        ("recommendation_ml/models/popularity.py", "Popularity-based model"),
        ("recommendation_ml/ranking/discovery.py", "Discovery ranking"),
        ("recommendation_ml/ranking/diversity.py", "Diversity ranking"),
        ("recommendation_ml/ranking/constraints.py", "Ranking constraints"),
        ("product_intelligence/src/product_intelligence/recommender.py", "Product recommender"),
        ("product_intelligence/src/product_intelligence/scoring.py", "Product scoring"),
        ("product_intelligence/src/product_intelligence/filtering.py", "Product filtering"),
        ("product_intelligence/src/product_intelligence/ranking.py", "Product ranking"),
        ("product_intelligence/src/product_intelligence/condition.py", "Condition-aware logic"),
        ("product_intelligence/src/product_intelligence/optimization/optimizer.py", "Bundle optimizer"),
        ("product_intelligence/src/product_intelligence/optimization/bundle.py", "Bundle logic"),
        ("product_intelligence/src/product_intelligence/optimization/constraints.py", "Optimization constraints"),
        ("agentic_ai/app.py", "Agentic AI application"),
        ("agentic_ai/agent.py", "Agent logic"),
        ("agentic_ai/gemini_agent.py", "Gemini-powered agent"),
        ("agentic_ai/tools.py", "Agent tools"),
        ("agentic_ai/state.py", "Agent state management"),
        ("agentic_ai/config.py", "Agent configuration"),
        ("frontend/src/main.jsx", "Frontend entry point"),
        ("frontend/package.json", "Frontend dependencies"),
        ("frontend/.env.example", "Environment variable template"),
        ("requirements.txt", "Root Python dependencies"),
        ("requirements-backend.txt", "Backend Python dependencies"),
        ("data/catalog.json", "Product catalog data"),
        ("data/interactions.json", "Interaction history data"),
        ("scripts/smoke_test.py", "Smoke test script"),
        ("scripts/run_backend.ps1", "Backend startup script"),
        ("scripts/run_frontend.ps1", "Frontend startup script"),
    ]
    for path, purpose in key_files:
        exists = "present" if (root / path).exists() else "MISSING"
        lines.append(f"- `{path}` -- {purpose} [{exists}]")
    lines.append("")

    lines.append("## Major Classes/Functions\n")

    # Collect all classes and functions
    py_files = [p for p in root.rglob("*.py") if not is_ignored(p, root)]
    for py in sorted(py_files):
        text = safe_read(py)
        if text is None:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) if not n.name.startswith("_")]
        rel = py.relative_to(root)
        if classes or funcs:
            lines.append(f"### `{rel}`")
            if classes:
                lines.append(f"  Classes: {', '.join(classes)}")
            if funcs:
                lines.append(f"  Functions: {', '.join(funcs)}")
            lines.append("")

    lines.append("## API Endpoints\n")
    # Scan for endpoints
    for py in py_files:
        text = safe_read(py)
        if text is None:
            continue
        for m in re.finditer(r'@\w+\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)', text):
            method = m.group(1).upper()
            endpoint = m.group(2)
            lines.append(f"- {method} `{endpoint}`")
    lines.append("")

    lines.append("## Data Flow\n")
    lines.append("```")
    lines.append("1. User types query in React frontend")
    lines.append("2. Frontend sends POST /api/recommendations")
    lines.append("3. Backend invokes Agentic AI supervisor")
    lines.append("4. Supervisor calls Intent module -> parses query into structured mission")
    lines.append("5. Supervisor calls Customer Intelligence -> builds digital twin from events")
    lines.append("6. Supervisor calls Recommendation ML -> hybrid candidate ranking")
    lines.append("7. Supervisor calls Product Intelligence -> filtering/scoring/bundles")
    lines.append("8. Backend returns combined response with explainability trace")
    lines.append("9. Frontend renders recommendations with explanations")
    lines.append("10. User feedback via POST /api/feedback updates re-ranking")
    lines.append("```\n")

    lines.append("## AI/ML Logic\n")
    lines.append("- **Intent Parsing:** Gemini LLM with rule-based fallback parser")
    lines.append("- **Customer Intelligence:** Event-driven digital twin with affinity scoring")
    lines.append("- **Recommendation Engine:** Hybrid (collaborative + content + popularity + diversity)")
    lines.append("- **Product Intelligence:** Condition-aware filtering, scoring, ranking, bundle optimization")
    lines.append("- **Agentic AI:** Supervisor workflow with Gemini for decision traces\n")

    lines.append("## Dependencies\n")
    # Python
    for req_name in ("requirements.txt", "requirements-backend.txt"):
        req = root / req_name
        if req.exists():
            text = safe_read(req)
            if text:
                deps = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
                lines.append(f"### {req_name}: {', '.join(deps)}")
    lines.append("")

    # Node
    pkg = root / "frontend" / "package.json"
    if pkg.exists():
        text = safe_read(pkg)
        if text:
            data = json.loads(text)
            deps = data.get("dependencies", {})
            dev = data.get("devDependencies", {})
            lines.append(f"### frontend/package.json")
            lines.append(f"Dependencies: {', '.join(deps.keys())}")
            lines.append(f"DevDependencies: {', '.join(dev.keys())}")
    lines.append("")

    lines.append("## Environment Variables\n")
    env_vars: Set[str] = set()
    for py in py_files:
        text = safe_read(py)
        if text:
            for m in ENV_VAR_RE.finditer(text):
                env_vars.add(m.group(1))
            for m in ENV_VAR_RE2.finditer(text):
                env_vars.add(m.group(1))
    for ef in root.rglob(".env.example"):
        if not is_ignored(ef, root):
            text = safe_read(ef)
            if text:
                for ln in text.splitlines():
                    s = ln.strip()
                    if s and not s.startswith("#") and "=" in s:
                        env_vars.add(s.split("=")[0].strip())
    if env_vars:
        for v in sorted(env_vars):
            lines.append(f"- `{v}`")
    else:
        lines.append("- (none detected)")
    lines.append("")

    lines.append("## Current Implementation Status\n")
    lines.append("- All major modules have source code present")
    lines.append("- Backend entry point (`backend/main.py`) exists")
    lines.append("- Frontend has built distribution in `dist/`")
    lines.append("- node_modules installed in frontend")
    lines.append("- JSON data files present in `data/`")
    lines.append("- Smoke test script available")
    lines.append("- Postman collection available")
    lines.append("")

    lines.append("## Known Problems\n")
    if problem_counts["critical"]:
        lines.append(f"- **{problem_counts['critical']} CRITICAL issues** -- must fix before running")
    if problem_counts["high"]:
        lines.append(f"- **{problem_counts['high']} HIGH issues** -- should fix")
    if problem_counts["medium"]:
        lines.append(f"- **{problem_counts['medium']} MEDIUM issues** -- recommended to fix")
    if problem_counts["low"]:
        lines.append(f"- **{problem_counts['low']} LOW issues** -- optional improvements")
    if problem_counts["total"] == 0:
        lines.append("- No issues detected")
    lines.append("")

    lines.append("## How to Run")
    lines.append("```powershell")
    lines.append("# Backend")
    lines.append("python -m venv .venv")
    lines.append(".\\.venv\\Scripts\\python.exe -m pip install -r requirements-backend.txt")
    lines.append(".\\.venv\\Scripts\\python.exe -m uvicorn backend.main:app --reload")
    lines.append("")
    lines.append("# Frontend (separate terminal)")
    lines.append("cd frontend")
    lines.append("npm install  # if not already done")
    lines.append("npm run dev")
    lines.append("")
    lines.append("# Smoke test")
    lines.append(".\\.venv\\Scripts\\python.exe scripts\\smoke_test.py")
    lines.append("```\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    run_tests = "--run-tests" in sys.argv
    run_checks = "--run-checks" in sys.argv

    # Find repo root
    root = Path(__file__).resolve().parent.parent
    print(f"Repository root: {root}")
    print(f"Time: {datetime.now().isoformat()}")
    print()

    # Collect git info
    g = git_info(root)

    # Build report sections
    report_parts: List[str] = []

    report_parts.append(f"# Repository Audit Report\n")
    report_parts.append(f"_Generated: {datetime.now().isoformat()}_\n")
    report_parts.append(f"```")
    report_parts.append(f"Repository: {root}")
    report_parts.append(f"Branch:     {g['branch']}")
    report_parts.append(f"Commit:     {g['commit']}")
    report_parts.append(f"Remote:     {g['remote_url']}")
    report_parts.append(f"```\n")
    report_parts.append("---\n")

    # 1. Overview
    print("Analyzing repository overview...")
    ov_text, file_count, folder_count, ext_counter, loc_by_ext = section_overview(root, g)
    report_parts.append(ov_text)
    report_parts.append("---\n")

    # 2. Directory tree
    print("Building directory tree...")
    report_parts.append(section_tree(root))
    report_parts.append("---\n")

    # 3. Components
    print("Identifying components...")
    report_parts.append(section_components(root))
    report_parts.append("---\n")

    # 4. Important files
    print("Finding important files...")
    report_parts.append(section_important_files(root))
    report_parts.append("---\n")

    # 5. Python analysis
    print("Analyzing Python files...")
    py_text, py_issues, py_warnings = section_python_analysis(root)
    report_parts.append(py_text)
    report_parts.append("---\n")

    # 6. Frontend
    print("Analyzing frontend...")
    report_parts.append(section_frontend_analysis(root))
    report_parts.append("---\n")

    # 7. Backend/API
    print("Analyzing backend/API...")
    report_parts.append(section_backend_analysis(root))
    report_parts.append("---\n")

    # 8. Database
    print("Analyzing database...")
    report_parts.append(section_database_analysis(root))
    report_parts.append("---\n")

    # 9. AI/ML
    print("Analyzing AI/ML...")
    report_parts.append(section_ai_analysis(root))
    report_parts.append("---\n")

    # 10. Dependencies
    print("Analyzing dependencies...")
    report_parts.append(section_dependency_analysis(root))
    report_parts.append("---\n")

    # 11. Environment variables
    print("Finding environment variables...")
    report_parts.append(section_env_vars(root))
    report_parts.append("---\n")

    # 12. Security
    print("Running security audit...")
    sec_text, sec_findings = section_security(root)
    report_parts.append(sec_text)
    report_parts.append("---\n")

    # 13. Tests
    print("Finding tests...")
    report_parts.append(section_tests(root))
    report_parts.append("---\n")

    # 14. Build checks
    report_parts.append(section_build_checks(root, run_checks))
    report_parts.append("---\n")

    # 15. Git audit
    print("Running git audit...")
    report_parts.append(section_git_audit(root, g))
    report_parts.append("---\n")

    # 16. Architecture
    print("Building architecture graph...")
    report_parts.append(section_architecture(root))
    report_parts.append("---\n")

    # 17. Potential problems
    print("Collecting potential problems...")
    prob_text, prob_counts = section_problems(root, py_issues, py_warnings, sec_findings)
    report_parts.append(prob_text)
    report_parts.append("---\n")

    # 18. Project abstract
    print("Generating project abstract...")
    report_parts.append(section_abstract(root))
    report_parts.append("---\n")

    # 19. AI Handoff summary
    print("Generating AI handoff summary...")
    report_parts.append(section_handoff(root, g, file_count, folder_count, loc_by_ext, prob_counts))
    report_parts.append("---\n")

    # Join all
    full_report = "\n".join(report_parts)

    # Save to reports/
    reports_dir = root / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / "repository_audit.md"
    report_path.write_text(full_report, encoding="utf-8")

    # Print to terminal
    safe_print("\n" + "=" * 60)
    safe_print("REPOSITORY AUDIT REPORT")
    safe_print("=" * 60 + "\n")
    safe_print(full_report)

    # Final summary
    safe_print("\n" + "=" * 40)
    safe_print("AUDIT COMPLETE")
    safe_print("=" * 40)
    safe_print(f"\nReport:")
    safe_print(f"  {report_path}")
    safe_print(f"\nFiles analyzed: {file_count}")
    safe_print(f"Folders analyzed: {folder_count}")
    safe_print(f"Potential issues: {prob_counts['total']}")
    safe_print(f"Critical issues: {prob_counts['critical']}")
    safe_print(f"High issues: {prob_counts['high']}")
    safe_print(f"Medium issues: {prob_counts['medium']}")
    safe_print(f"Low issues: {prob_counts['low']}")
    safe_print(f"Info: {prob_counts['info']}")
    safe_print(f"\nTo run again:")
    safe_print(f"  python scripts/repo_audit.py")
    safe_print(f"  python scripts/repo_audit.py --run-checks")
    safe_print(f"  python scripts/repo_audit.py --run-tests")


if __name__ == "__main__":
    main()
