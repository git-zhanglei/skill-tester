#!/usr/bin/env python3
"""
Spec Checker — Skill 规范结构检查
参考 terwox/skill-evaluator 的 eval-skill.py 扩展而来，适配中文/混合语言 Skill。

14项检查，分 6 类：structure / trigger / documentation / scripts / security / agent_specific
评分公式：pass=2分 / warn=1分 / fail=0分，最终归一到 0-100

用法:
  python3 spec_checker.py <skill_path>
  python3 spec_checker.py <skill_path> --json
  python3 spec_checker.py <skill_path> --verbose
"""

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

PASS = 'pass'
WARN = 'warn'
FAIL = 'fail'

# Python 标准库模块集合（用于外部依赖检测）
STDLIB_MODULES = {
    'abc', 'argparse', 'ast', 'base64', 'bisect', 'calendar',
    'cmd', 'codecs', 'collections', 'configparser', 'contextlib', 'copy',
    'csv', 'dataclasses', 'datetime', 'decimal', 'difflib', 'email',
    'enum', 'errno', 'fnmatch', 'fractions', 'functools',
    'getopt', 'getpass', 'glob', 'gzip', 'hashlib', 'heapq', 'hmac',
    'html', 'http', 'importlib', 'inspect', 'io', 'ipaddress',
    'itertools', 'json', 'keyword', 'linecache', 'locale', 'logging',
    'math', 'mimetypes', 'multiprocessing', 'operator', 'os',
    'pathlib', 'pickle', 'platform', 'pprint', 'queue', 'random',
    're', 'readline', 'reprlib', 'secrets', 'select', 'shlex',
    'shutil', 'signal', 'smtplib', 'socket', 'sqlite3', 'ssl',
    'stat', 'statistics', 'string', 'struct', 'subprocess', 'sys',
    'tarfile', 'tempfile', 'textwrap', 'threading', 'time', 'timeit',
    'token', 'tokenize', 'traceback', 'types', 'typing', 'unicodedata',
    'unittest', 'urllib', 'uuid', 'warnings', 'weakref', 'xml',
    'zipfile', 'zlib', '_thread', '__future__', 'concurrent',
    'contextlib', 'dataclasses',
}


# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

def _read_skill_md(skill_path: str) -> Tuple[str, Dict[str, str], str]:
    """返回 (full_content, frontmatter_dict, body)"""
    path = Path(skill_path) / 'SKILL.md'
    if not path.exists():
        return '', {}, ''
    content = path.read_text(encoding='utf-8')
    fm: Dict[str, str] = {}
    body = content
    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if match:
        for line in match.group(1).split('\n'):
            if ':' in line:
                k, _, v = line.partition(':')
                fm[k.strip()] = v.strip().strip('"\'')
        body = content[match.end():]
    return content, fm, body


def _result(id_: str, category: str, status: str, message: str) -> Dict:
    return {'id': id_, 'category': category, 'status': status, 'message': message}


# ─────────────────────────────────────────────
# 检查项（structure）
# ─────────────────────────────────────────────

def check_skill_md_exists(skill_path: str) -> Dict:
    exists = (Path(skill_path) / 'SKILL.md').exists()
    return _result('skill_md_exists', 'structure',
                   PASS if exists else FAIL,
                   'SKILL.md 存在' if exists else 'SKILL.md 不存在，这是必须文件')


def check_valid_frontmatter(skill_path: str) -> Dict:
    _, fm, _ = _read_skill_md(skill_path)
    if not fm:
        return _result('valid_frontmatter', 'structure', FAIL,
                       '缺少 YAML frontmatter（文件需以 --- 开头）')
    missing = [f for f in ('name', 'description') if not fm.get(f)]
    if missing:
        return _result('valid_frontmatter', 'structure', FAIL,
                       f'frontmatter 缺少必要字段: {", ".join(missing)}')
    return _result('valid_frontmatter', 'structure', PASS,
                   f'frontmatter 完整（name={fm["name"]}）')


def check_name_matches_dir(skill_path: str) -> Dict:
    dir_name = Path(skill_path).resolve().name
    _, fm, _ = _read_skill_md(skill_path)
    skill_name = fm.get('name', '')
    if not skill_name:
        return _result('name_matches_dir', 'structure', WARN,
                       'frontmatter 中无 name 字段，无法比较目录名')
    if skill_name == dir_name:
        return _result('name_matches_dir', 'structure', PASS,
                       f'name="{skill_name}" 与目录名一致')
    return _result('name_matches_dir', 'structure', WARN,
                   f'name="{skill_name}" 与目录名 "{dir_name}" 不一致（ClawHub 发布要求两者一致）')


def check_no_extraneous_files(skill_path: str) -> Dict:
    # README.md 是 GitHub 仓库标准文件，不视为冗余
    extraneous = {'CHANGELOG.md', 'INSTALLATION_GUIDE.md', 'QUICK_REFERENCE.md'}
    found = [f for f in os.listdir(skill_path)
             if f.upper() in {e.upper() for e in extraneous}]
    if found:
        return _result('no_extraneous_files', 'structure', WARN,
                       f'发现冗余文件：{", ".join(found)}（建议使用 references/ 替代）')
    return _result('no_extraneous_files', 'structure', PASS, '无冗余文件')


def check_has_guardrails(skill_path: str) -> Dict:
    _, _, body = _read_skill_md(skill_path)
    has = bool(re.search(r'^#+\s*Guardrails', body, re.MULTILINE | re.IGNORECASE))
    if not has:
        return _result('has_guardrails', 'structure', WARN,
                       '缺少 ## Guardrails 章节（OpenClaw 规范推荐的必备章节）')
    return _result('has_guardrails', 'structure', PASS, '有 Guardrails 章节')


# ─────────────────────────────────────────────
# 检查项（trigger）
# ─────────────────────────────────────────────

def check_description_length(skill_path: str) -> Dict:
    """description 有效字符数检查（中英混合）"""
    _, fm, _ = _read_skill_md(skill_path)
    desc = fm.get('description', '')
    # 对中英混合，以去掉空白和标点后的字符数衡量
    effective = len(re.sub(r'[\s\W]', '', desc))
    word_count = len(desc.split())

    if effective < 20:
        return _result('description_length', 'trigger', FAIL,
                       f'description 过短（{effective} 有效字符），触发命中率会受影响')
    if word_count > 150:
        return _result('description_length', 'trigger', WARN,
                       f'description 过长（{word_count} 词），占用过多 context token')
    return _result('description_length', 'trigger', PASS,
                   f'description 长度合适（{effective} 有效字符，{word_count} 词）')


def check_description_trigger_context(skill_path: str) -> Dict:
    """description 是否包含触发上下文短语"""
    _, fm, _ = _read_skill_md(skill_path)
    desc = fm.get('description', '').lower()
    trigger_phrases = [
        'use when', 'use for', 'when the user', 'when asked',
        '当用户', '当需要', '触发', '使用时', 'use if', 'for tasks like',
    ]
    found = [p for p in trigger_phrases if p in desc]
    if not found:
        return _result('description_trigger_context', 'trigger', WARN,
                       '未包含触发上下文短语（如"Use when..."、"当用户..."），可能影响触发精确率')
    return _result('description_trigger_context', 'trigger', PASS,
                   f'包含触发上下文（{", ".join(found[:3])}）')


# ─────────────────────────────────────────────
# 检查项（documentation）
# ─────────────────────────────────────────────

def check_token_cost(skill_path: str) -> Dict:
    """
    SKILL.md 正文行数 — token 开销评级
    参考 skill-evaluator rubric 3.1（严格标准）：
      ≤150  → pass（优秀）
      151-250 → pass（良好）
      251-400 → warn（建议优化）
      >400  → fail（过重）
    """
    _, _, body = _read_skill_md(skill_path)
    lines = len(body.splitlines())

    if lines <= 150:
        return _result('token_cost', 'documentation', PASS,
                       f'SKILL.md 正文 {lines} 行（优秀，≤150）')
    if lines <= 250:
        return _result('token_cost', 'documentation', PASS,
                       f'SKILL.md 正文 {lines} 行（良好，151-250）')
    if lines <= 400:
        return _result('token_cost', 'documentation', WARN,
                       f'SKILL.md 正文 {lines} 行（一般，建议将详情移入 references/）')
    return _result('token_cost', 'documentation', FAIL,
                   f'SKILL.md 正文 {lines} 行（过重，>400，会挤占有效上下文）')


def check_has_workflow(skill_path: str) -> Dict:
    _, _, body = _read_skill_md(skill_path)
    patterns = [r'##\s*Workflow', r'##\s*执行步骤', r'##\s*Steps', r'##\s*工作流']
    if any(re.search(p, body, re.IGNORECASE) for p in patterns):
        return _result('has_workflow', 'documentation', PASS, '有 Workflow / 执行步骤 章节')
    return _result('has_workflow', 'documentation', WARN,
                   '缺少 ## Workflow / ## 执行步骤 章节，Agent 难以理解操作顺序')


def check_references_linked(skill_path: str) -> Dict:
    ref_dir = Path(skill_path) / 'references'
    if not ref_dir.exists():
        return _result('references_linked', 'documentation', PASS, '无 references/ 目录')
    ref_files = [f.name for f in ref_dir.iterdir() if not f.name.startswith('.')]
    if not ref_files:
        return _result('references_linked', 'documentation', PASS, 'references/ 目录为空')
    content, _, _ = _read_skill_md(skill_path)
    unlinked = [f for f in ref_files if f not in content]
    if unlinked:
        return _result('references_linked', 'documentation', WARN,
                       f'references/ 中有文件未在 SKILL.md 链接：{", ".join(unlinked[:5])}')
    return _result('references_linked', 'documentation', PASS,
                   f'所有 {len(ref_files)} 个 references 文件均已链接')


# ─────────────────────────────────────────────
# 检查项（scripts）
# ─────────────────────────────────────────────

def check_python_syntax(skill_path: str) -> Dict:
    scripts_dir = Path(skill_path) / 'scripts'
    if not scripts_dir.exists():
        return _result('python_syntax', 'scripts', PASS, '无 scripts/ 目录')
    errors = []
    checked = 0
    for f in scripts_dir.glob('*.py'):
        checked += 1
        try:
            ast.parse(f.read_text(encoding='utf-8', errors='ignore'))
        except SyntaxError as e:
            errors.append(f'{f.name}:{e.lineno}: {e.msg}')
    if not checked:
        return _result('python_syntax', 'scripts', PASS, '无 Python 脚本')
    if errors:
        return _result('python_syntax', 'scripts', FAIL,
                       f'语法错误：{"; ".join(errors[:3])}')
    return _result('python_syntax', 'scripts', PASS, f'{checked} 个脚本语法正确')


def check_no_external_deps(skill_path: str) -> Dict:
    scripts_dir = Path(skill_path) / 'scripts'
    if not scripts_dir.exists():
        return _result('no_external_deps', 'scripts', PASS, '无 scripts/ 目录')

    # 收集本地模块名（scripts/ 中的 .py 文件名，不含扩展名）
    local_modules = {f.stem for f in scripts_dir.glob('*.py')}

    ext_deps: List[str] = []
    for f in scripts_dir.glob('*.py'):
        try:
            tree = ast.parse(f.read_text(encoding='utf-8', errors='ignore'))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split('.')[0]
                    if top not in STDLIB_MODULES and top not in local_modules:
                        ext_deps.append(f'{f.name}: import {alias.name}')
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split('.')[0]
                    # 相对导入（level > 0）不计为外部依赖
                    is_relative = getattr(node, 'level', 0) > 0
                    if (not is_relative
                            and top not in STDLIB_MODULES
                            and top not in local_modules):
                        ext_deps.append(f'{f.name}: from {node.module}')
    if ext_deps:
        return _result('no_external_deps', 'scripts', WARN,
                       f'检测到外部依赖（需文档化安装要求）：{"; ".join(ext_deps[:5])}')
    return _result('no_external_deps', 'scripts', PASS, '脚本仅使用标准库或本地模块')


# ─────────────────────────────────────────────
# 检查项（security）
# ─────────────────────────────────────────────

def check_env_vars_documented(skill_path: str) -> Dict:
    scripts_dir = Path(skill_path) / 'scripts'
    if not scripts_dir.exists():
        return _result('env_vars_documented', 'security', PASS, '无 scripts/ 目录')
    env_vars: set = set()
    for f in scripts_dir.glob('*.py'):
        try:
            content = f.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for m in re.finditer(r'os\.environ(?:\.get)?\s*[\[(]\s*["\'](\w+)', content):
            v = m.group(1)
            if v not in ('VAR', 'KEY', 'VALUE', 'NAME', 'ENV'):
                env_vars.add(v)
    if not env_vars:
        return _result('env_vars_documented', 'security', PASS, '脚本中未使用环境变量')
    skill_content, _, _ = _read_skill_md(skill_path)
    undoc = [v for v in env_vars if v not in skill_content]
    if undoc:
        return _result('env_vars_documented', 'security', WARN,
                       f'以下环境变量未在 SKILL.md 文档化：{", ".join(sorted(undoc))}')
    return _result('env_vars_documented', 'security', PASS,
                   f'所有环境变量（{", ".join(sorted(env_vars))}）均已文档化')


# ─────────────────────────────────────────────
# 检查项（agent_specific）
# ─────────────────────────────────────────────

def check_composability(skill_path: str) -> Dict:
    """
    机器可读输出信号检测（Composability，来自 skill-evaluator 8.3）
    --json / JSON 输出 / exit code → 有利于 CI/CD 集成
    """
    content, _, _ = _read_skill_md(skill_path)
    signals: List[str] = []
    if re.search(r'--json', content):
        signals.append('--json 标志')
    if re.search(r'exit\s*code|sys\.exit|exit_code', content, re.IGNORECASE):
        signals.append('exit code')
    if re.search(r'json\.dumps|json output|JSON\s*输出|机器可读', content, re.IGNORECASE):
        signals.append('JSON 输出')

    if len(signals) >= 2:
        return _result('composability', 'agent_specific', PASS,
                       f'具备组合性信号：{", ".join(signals)}')
    if signals:
        return _result('composability', 'agent_specific', WARN,
                       f'部分组合性信号（{", ".join(signals)}），建议增加 --json 和明确 exit code')
    return _result('composability', 'agent_specific', WARN,
                   '未检测到机器可读输出信号，影响 CI/CD 集成能力')


# ─────────────────────────────────────────────
# 运行 & 评分
# ─────────────────────────────────────────────

ALL_CHECKS = [
    check_skill_md_exists,
    check_valid_frontmatter,
    check_name_matches_dir,
    check_no_extraneous_files,
    check_has_guardrails,
    check_description_length,
    check_description_trigger_context,
    check_token_cost,
    check_has_workflow,
    check_references_linked,
    check_python_syntax,
    check_no_external_deps,
    check_env_vars_documented,
    check_composability,
]


def run_checks(skill_path: str) -> List[Dict]:
    results: List[Dict] = []
    for fn in ALL_CHECKS:
        try:
            results.append(fn(skill_path))
        except Exception as e:
            results.append({
                'id': fn.__name__, 'category': 'error',
                'status': FAIL, 'message': f'检查崩溃：{e}',
            })
    return results


def compute_spec_score(results: List[Dict]) -> float:
    """pass=2 / warn=1 / fail=0；最终归一到 0-100"""
    total_possible = len(results) * 2
    if not total_possible:
        return 0.0
    actual = sum(
        2 if r['status'] == PASS else (1 if r['status'] == WARN else 0)
        for r in results
    )
    return round(actual / total_possible * 100, 1)


def print_report(results: List[Dict], skill_path: str, spec_score: float,
                 verbose: bool = False) -> None:
    by_cat: Dict[str, List] = {}
    for r in results:
        by_cat.setdefault(r['category'], []).append(r)

    name = Path(skill_path).resolve().name
    print(f'\n📋 Spec Check: {name}')
    print('=' * 60)

    icons = {PASS: '✅', WARN: '⚠️ ', FAIL: '❌'}
    for cat in ('structure', 'trigger', 'documentation', 'scripts', 'security', 'agent_specific'):
        if cat not in by_cat:
            continue
        print(f'\n  [{cat.upper()}]')
        for r in by_cat[cat]:
            icon = icons.get(r['status'], '?')
            print(f'  {icon} {r["id"]}')
            if r['message'] and (verbose or r['status'] != PASS):
                print(f'       {r["message"]}')

    counts = {s: sum(1 for r in results if r['status'] == s) for s in (PASS, WARN, FAIL)}
    print(f'\n{"=" * 60}')
    print(f'  ✅ Pass: {counts[PASS]}  ⚠️  Warn: {counts[WARN]}  ❌ Fail: {counts[FAIL]}')
    print(f'  规范得分（spec_score）: {spec_score:.1f}/100')
    print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Skill Spec Checker')
    parser.add_argument('path', help='Skill 目录路径')
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示通过项详情')
    args = parser.parse_args()

    if not Path(args.path).is_dir():
        print(f'错误："{args.path}" 不是有效目录', file=sys.stderr)
        sys.exit(1)

    results    = run_checks(args.path)
    spec_score = compute_spec_score(results)

    if args.json:
        counts = {s: sum(1 for r in results if r['status'] == s)
                  for s in (PASS, WARN, FAIL)}
        print(json.dumps({
            'skill':   Path(args.path).resolve().name,
            'path':    str(Path(args.path).resolve()),
            'checks':  results,
            'summary': {**counts, 'spec_score': spec_score},
        }, ensure_ascii=False, indent=2))
    else:
        print_report(results, args.path, spec_score, verbose=args.verbose)

    has_fail = any(r['status'] == FAIL for r in results)
    sys.exit(1 if has_fail else 0)
