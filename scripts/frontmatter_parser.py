#!/usr/bin/env python3
"""
Frontmatter Parser — 统一的 YAML frontmatter 解析器
支持多行 YAML 值（> / | 块标量）和引号内含冒号的值。
不引入 pyyaml 依赖。
"""

import re
from pathlib import Path
from typing import Dict, Tuple


def parse_skill_md(skill_path: str) -> Tuple[str, Dict[str, str], str]:
    """
    解析 SKILL.md 文件，返回 (full_content, frontmatter_dict, body)。

    支持：
    - 标准 key: value
    - 引号包裹的值（含冒号）：key: "value: with colon"
    - YAML 块标量：key: > 或 key: |
    """
    path = Path(skill_path) / 'SKILL.md'
    if not path.exists():
        return '', {}, ''

    content = path.read_text(encoding='utf-8')
    fm: Dict[str, str] = {}
    body = content

    match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        return content, {}, content

    raw_fm = match.group(1)
    body = content[match.end():]

    # 简易 YAML 解析
    current_key = None
    current_value_lines = []

    for line in raw_fm.split('\n'):
        # 续行（以空格/tab开头）
        if current_key and (line.startswith(' ') or line.startswith('\t')):
            current_value_lines.append(line.strip())
            continue

        # 新键值对
        if ':' in line:
            # 先保存上一个键
            if current_key:
                fm[current_key] = ' '.join(current_value_lines).strip().strip('"\'')

            key, _, value = line.partition(':')
            current_key = key.strip()
            value = value.strip()

            # 处理引号包裹的值
            if value.startswith('"') and value.endswith('"'):
                current_value_lines = [value[1:-1]]
            elif value.startswith("'") and value.endswith("'"):
                current_value_lines = [value[1:-1]]
            elif value in ('|', '>', '|+', '>-', '|-', '>+'):
                current_value_lines = []
            elif value:
                current_value_lines = [value]
            else:
                current_value_lines = []

    # 保存最后一个键
    if current_key:
        fm[current_key] = ' '.join(current_value_lines).strip().strip('"\'')

    return content, fm, body
