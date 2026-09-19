#!/usr/bin/env python3
"""
Conservative static auditor for research benchmark artifacts.

Goal: find mechanically-checkable experiment wiring defects without claiming
that paper results are wrong. Findings have confidence levels:
  HIGH   - direct control/data-flow defect visible in released code
  MEDIUM - strong static smell that needs human confirmation
  INFO   - methodological metadata, not a defect by itself
"""
from __future__ import annotations
import argparse, ast, json, re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Iterable

TEXT_EXTS={".py",".cpp",".cc",".cxx",".c",".h",".hpp",".cmake",".md",".sh",".txt"}

@dataclass
class Finding:
    rule: str
    confidence: str
    path: str
    line: int
    message: str
    evidence: str

def safe_read(p: Path) -> str:
    try:
        return p.read_text(errors="replace")
    except Exception:
        return ""

def iter_files(root: Path, exts: set[str] | None=None) -> Iterable[Path]:
    skip={".git","build","cmake-build-debug","cmake-build-release","node_modules","vendor","third_party"}
    for p in root.rglob("*"):
        if not p.is_file() or any(x in skip for x in p.parts):
            continue
        if exts is None or p.suffix.lower() in exts or p.name=="CMakeLists.txt":
            yield p

def names_in_target(node):
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, (ast.Tuple,ast.List)):
        out=[]
        for x in node.elts: out += names_in_target(x)
        return out
    return []

def assignment_source_names(tree):
    out=set()
    for n in ast.walk(tree):
        if isinstance(n,(ast.Assign,ast.AnnAssign)):
            targets=n.targets if isinstance(n,ast.Assign) else [n.target]
            for t in targets:
                if isinstance(t,ast.Name) and (
                    t.id.endswith("_LIST") or t.id.endswith("_VALUES")
                    or "THRESHOLD" in t.id or "INTERVAL" in t.id
                ):
                    out.add(t.id)
    return out

def render_expr(node):
    """Best-effort symbolic rendering of shell/list command expressions."""
    if isinstance(node, ast.JoinedStr):
        s=""
        for v in node.values:
            if isinstance(v,ast.Constant): s += str(v.value)
            elif isinstance(v,ast.FormattedValue):
                if isinstance(v.value,ast.Name): s += "{"+v.value.id+"}"
                else: s += "{EXPR}"
        return s
    if isinstance(node,ast.Constant) and isinstance(node.value,str):
        return node.value
    if isinstance(node,ast.Name):
        return "{VAR:"+node.id+"}"
    if isinstance(node,(ast.List,ast.Tuple)):
        return " ".join(render_expr(x) for x in node.elts)
    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):
        return render_expr(node.left)+render_expr(node.right)
    return ""

def is_shell_call(node):
    if not isinstance(node,ast.Call): return False
    f=node.func
    if isinstance(f,ast.Attribute) and isinstance(f.value,ast.Name):
        return (f.value.id,f.attr) in {
            ("os","system"),("subprocess","run"),("subprocess","call"),
            ("subprocess","Popen"),("subprocess","check_call"),("subprocess","check_output")
        }
    return False

class PySweepVisitor(ast.NodeVisitor):
    def __init__(self, path, source, sweep_sources):
        self.path=path; self.source=source; self.sweep_sources=sweep_sources
        self.active=[]  # [(loop_var, source_name)]
        self.findings=[]

    def loop_bindings(self,node):
        targets=names_in_target(node.target)
        it=node.iter
        if isinstance(it,ast.Name) and it.id in self.sweep_sources and len(targets)==1:
            return [(targets[0],it.id)]
        if isinstance(it,ast.Call) and isinstance(it.func,ast.Name) and it.func.id=="zip":
            args=[a.id if isinstance(a,ast.Name) else "" for a in it.args]
            return [(t,a) for t,a in zip(targets,args) if a in self.sweep_sources]
        return []

    def visit_For(self,node):
        binds=self.loop_bindings(node)
        self.active.extend(binds)
        for stmt in node.body: self.visit(stmt)
        if binds: del self.active[-len(binds):]
        for stmt in node.orelse: self.visit(stmt)

    def visit_Call(self,node):
        if is_shell_call(node) and node.args:
            cmd=render_expr(node.args[0])
            # If a variable command was prebuilt, recover a simple assignment in enclosing source
            if cmd.startswith("{VAR:"):
                var=cmd[5:-1]
                upto=self.source[:getattr(node,"lineno",1)]
                # best-effort: latest "var = f'...'" or f"..."
                pat=re.compile(rf"^\s*{re.escape(var)}\s*=\s*(f?[\"\'].*)$",re.M)
                ms=list(pat.finditer(upto))
                if ms: cmd=ms[-1].group(1)
            # Shell redirection and output paths do not configure the executable.
            execution=cmd.split(">",1)[0]
            for loop_var,src_name in self.active:
                token="{"+loop_var+"}"
                if token in cmd and token not in execution:
                    self.findings.append(Finding(
                        "SWEEP_VALUE_NOT_PROPAGATED","HIGH",str(self.path),node.lineno,
                        f"Sweep variable '{loop_var}' from {src_name} affects output/labeling but not the executed command.",
                        cmd.strip().replace("\n"," ")[:500]
                    ))
        self.generic_visit(node)

def audit_python(root):
    findings=[]
    for p in iter_files(root,{".py"}):
        src=safe_read(p)
        try: tree=ast.parse(src)
        except SyntaxError: continue
        sweep_sources=assignment_source_names(tree)
        v=PySweepVisitor(p.relative_to(root),src,sweep_sources)
        v.visit(tree)
        findings.extend(v.findings)
        # Single-repeat is informational and only interesting in experiment-like scripts.
        if any(k in p.name.lower() for k in ("bench","experiment","eval","figure","table","lazy","size")) or "scripts" in p.parts:
            for n in ast.walk(tree):
                if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant) and n.value.value==1:
                    for t in n.targets:
                        if isinstance(t,ast.Name) and re.search(r"(REPEAT|TRIAL|RUNS?)",t.id,re.I):
                            findings.append(Finding(
                                "SINGLE_REPEAT_EXPERIMENT","INFO",str(p.relative_to(root)),n.lineno,
                                f"{t.id}=1; released experiment uses a single repetition.",
                                ast.get_source_segment(src,n) or t.id+"=1"
                            ))
    return findings

def audit_cpp(root):
    findings=[]
    for p in iter_files(root,{".cpp",".cc",".cxx",".c"}):
        src=safe_read(p)
        rel=str(p.relative_to(root))
        # Direct fall-through from a case into default with no break/return.
        for m in re.finditer(r"case\s+([^:]+):(?P<body>.*?)(?=\bcase\s+[^:]+:|\bdefault\s*:)",src,re.S):
            body=m.group("body")
            following=src[m.end():m.end()+80]
            if re.match(r"\s*default\s*:",following) and re.search(r"\b(?:strto\w*|sto\w*|atoi|atof)\s*\(",body):
                if not re.search(r"\b(break|return|continue|throw)\b",body):
                    line=src.count("\n",0,m.start())+1
                    findings.append(Finding(
                        "CLI_CASE_FALLTHROUGH_TO_DEFAULT","HIGH",rel,line,
                        "CLI option case parses a value then falls through directly to default without break/return.",
                        re.sub(r"\s+"," ",m.group(0))[:350]
                    ))
        # Parsed-but-never-used variable heuristic within the translation unit.
        # Require a getopt-style assignment and exactly two token occurrences:
        # declaration + parse assignment.
        for m in re.finditer(r"case\s+['\"](?P<char>.)['\"]\s*:\s*(?P<var>[A-Za-z_]\w*)\s*=\s*(?:strto\w*|sto\w*|atoi|atof)\s*\(",src):
            var=m.group("var")
            occ=len(re.findall(rf"\b{re.escape(var)}\b",src))
            if occ <= 2:
                line=src.count("\n",0,m.start())+1
                findings.append(Finding(
                    "CLI_VALUE_PARSED_BUT_UNUSED","MEDIUM",rel,line,
                    f"CLI value is assigned to '{var}', but that variable has only {occ} occurrences in this translation unit.",
                    re.sub(r"\s+"," ",m.group(0))[:220]
                ))
    return findings


def audit_docs(root):
    """Check executable/script paths written in project-facing reproduction docs.

    Fenced shell blocks track simple 'cd <relative-path>' commands so that
    './script.sh' is resolved relative to the documented working directory.
    """
    findings=[]
    cmd_pat=re.compile(r"(?P<cmd>(?:sudo\s+)?(?:python3?\s+|bash\s+|sh\s+)?)(?P<path>\./[A-Za-z0-9_./-]+\.(?:sh|py))")
    cd_pat=re.compile(r"^(?:\$\s*)?cd\s+(?P<path>[A-Za-z0-9_./-]+)\s*$")

    for p in iter_files(root,{".md"}):
        rel=p.relative_to(root)
        rel_lower=str(rel).lower()
        project_doc=(len(rel.parts)==1 or any(
            token in rel_lower for token in ("reproduce","reproduction","artifact","experiment")
        ))
        if not project_doc:
            continue

        src=safe_read(p)
        lines=src.splitlines()
        in_fence=False
        cwd=root
        cloned_dirs=set()

        for lineno,line in enumerate(lines,1):
            stripped=line.strip()

            if stripped.startswith("```"):
                if not in_fence:
                    in_fence=True
                    cwd=root
                    cloned_dirs=set()
                else:
                    in_fence=False
                    cwd=root
                    cloned_dirs=set()
                continue

            check_base=root
            command_text=line

            if in_fence:
                shell_line=stripped
                if shell_line.startswith("$ "):
                    shell_line=shell_line[2:].strip()

                # Map "git clone .../Repo.git" followed by "cd Repo" to the
                # audited repository root, since our checkout already *is*
                # that cloned directory.
                mclone=re.match(r"git\s+clone\s+\S+/([^/\s]+?)(?:\.git)?(?:\s+([A-Za-z0-9_.-]+))?\s*$",shell_line)
                if mclone:
                    repo_dir=mclone.group(2) or mclone.group(1)
                    if repo_dir.endswith(".git"):
                        repo_dir=repo_dir[:-4]
                    cloned_dirs.add(repo_dir)
                    continue

                mcd=cd_pat.match(shell_line)
                if mcd:
                    cd_arg=mcd.group("path")
                    if cwd==root and cd_arg in cloned_dirs:
                        cwd=root
                        continue
                    candidate=(cwd/cd_arg).resolve()
                    try:
                        candidate.relative_to(root.resolve())
                        cwd=candidate
                    except ValueError:
                        pass
                    continue

                check_base=cwd
                command_text=shell_line

            for m in cmd_pat.finditer(command_text):
                rel_path=m.group("path")[2:].rstrip(".,;:")
                target=(check_base/rel_path)
                if not target.exists():
                    findings.append(Finding(
                        "DOCUMENTED_COMMAND_PATH_MISSING","HIGH",str(rel),lineno,
                        f"Documentation invokes '{m.group('path')}', but that .sh/.py path does not exist relative to the documented working directory.",
                        m.group(0).strip()
                    ))
    return findings

def classify(root):
    readme=""
    for n in ("README.md","README","readme.md"):
        p=root/n
        if p.exists(): readme=safe_read(p); break
    py=list(iter_files(root,{".py"}))
    benchmarkish=bool(list(root.rglob("*bench*"))) or "benchmark" in readme.lower()
    repro_terms=sum(readme.lower().count(x) for x in ("reproduce","reproduction","figure ","table ","artifact"))
    if py and repro_terms>=2: return "paper_reproduction_artifact"
    if benchmarkish: return "benchmark_or_library_repo"
    return "library_or_source_repo"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--name",default="")
    ap.add_argument("--json-out")
    args=ap.parse_args()
    root=Path(args.repo).resolve()
    findings=audit_python(root)+audit_cpp(root)+audit_docs(root)
    # de-duplicate
    uniq={}
    for f in findings:
        key=(f.rule,f.path,f.line,f.message)
        uniq[key]=f
    findings=list(uniq.values())
    report={
        "name":args.name or root.name,
        "classification":classify(root),
        "findings":[asdict(f) for f in findings],
        "counts":{
            "HIGH":sum(f.confidence=="HIGH" for f in findings),
            "MEDIUM":sum(f.confidence=="MEDIUM" for f in findings),
            "INFO":sum(f.confidence=="INFO" for f in findings),
        }
    }
    print(f"ARTIFACT AUDIT: {report['name']}")
    print(f"classification={report['classification']}")
    print(f"counts={report['counts']}")
    for f in findings:
        print(f"[{f.confidence}] {f.rule} {f.path}:{f.line}")
        print("  "+f.message)
        print("  evidence: "+f.evidence)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
