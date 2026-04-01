#!/usr/bin/env python3
"""
安全检查器 - 嵌入自 Skill Test 安全评审器
检查恶意模式、凭证和个人数据
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any


class SafetyChecker:
    """skill 安全预检"""
    
    # 危险模式
    DANGEROUS_PATTERNS = [
        # 系统修改
        (r'rm\s+-rf\s+/', '危险删除命令'),
        (r'>\s*/etc/', '系统文件修改'),
        (r'chmod\s+777', '过度宽松权限'),
        (r'curl.*\|.*sh', '管道到 shell（危险）'),
        (r'wget.*-O-\s*\|', '管道到 shell（危险）'),
        
        # 网络外泄
        (r'curl\s+.*http', '外部网络调用'),
        (r'wget\s+.*http', '外部下载'),
        (r'requests\.post\s*\(', 'HTTP POST（潜在外泄）'),
        (r'fetch\s*\(', '网络获取'),
        
        # 加密货币挖矿指标
        (r'xmrig|minerd|stratum\+tcp', '加密货币挖矿模式'),
        (r'--donate-level', '挖矿软件标志'),
        
        # 后门指标
        (r'nc\s+-[lve]', 'Netcat 监听器（后门）'),
        (r'python\s+-m\s+http\.server', '简单 HTTP 服务器（可疑）'),
        (r'bind\s*\(\s*0\.0\.0\.0', '绑定所有接口'),
    ]
    
    # 凭证模式
    CREDENTIAL_PATTERNS = [
        (r'api[_-]?key\s*[=:]\s*["\']\w+', '硬编码 API key'),
        (r'secret[_-]?key\s*[=:]\s*["\']\w+', '硬编码 secret key'),
        (r'password\s*[=:]\s*["\'][^"\']+', '硬编码密码'),
        (r'token\s*[=:]\s*["\']\w{20,}', '硬编码 token'),
        (r'aws_access_key_id', 'AWS 凭证'),
        (r'private[_-]?key', '私钥'),
        (r'ssh[_-]?key', 'SSH key'),
    ]
    
    # 个人数据模式
    PERSONAL_DATA_PATTERNS = [
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '邮箱地址'),
        (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN 模式'),
        (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '信用卡模式'),
        (r'\b\d{10,}\b', '长数字（潜在 ID）'),
    ]
    
    # 模型特定引用（不危险，只是记录）
    MODEL_PATTERNS = [
        (r'Claude', '模型特定引用'),
        (r'GPT-4', '模型特定引用'),
        (r'Codex', '模型特定引用'),
    ]
    
    def __init__(self, skill_path: Path):
        self.skill_path = skill_path
        self.issues = []
        self.warnings = []
    
    def check(self) -> Dict[str, Any]:
        """运行所有安全检查"""
        self._check_files()
        self._check_skill_md()
        
        # 确定状态
        # 注意：self.issues 中的所有条目均为严重问题（包括硬编码凭证），
        # 任何 issue 都应触发 failed，不能再次过滤。
        if self.issues:
            status = 'failed'
        elif self.warnings:
            status = 'warning'
        else:
            status = 'passed'
        
        return {
            'status': status,
            'issues': self.issues,
            'warnings': self.warnings,
            'checked_files': self._get_checked_files()
        }
    
    def _get_checked_files(self) -> List[str]:
        """获取已检查文件列表"""
        files = []
        for pattern in ['**/*.md', '**/*.py', '**/*.js', '**/*.sh', '**/*.json']:
            files.extend([str(f.relative_to(self.skill_path)) 
                         for f in self.skill_path.glob(pattern)])
        return files
    
    def _check_files(self):
        """检查 skill 目录中的所有文件"""
        for file_path in self.skill_path.rglob('*'):
            if file_path.is_file() and file_path.stat().st_size < 1024 * 1024:  # 跳过 > 1MB 的文件
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    self._scan_content(content, str(file_path.relative_to(self.skill_path)))
                except Exception:
                    pass  # 跳过不可读文件
    
    def _check_skill_md(self):
        """SKILL.md 特定检查"""
        skill_md = self.skill_path / 'SKILL.md'
        if not skill_md.exists():
            self.issues.append("SKILL.md 未找到")
            return
        
        content = skill_md.read_text(encoding='utf-8')
        
        # 检查 frontmatter
        if not content.startswith('---'):
            self.warnings.append("SKILL.md 缺少 YAML frontmatter")
        
        # 检查 description
        if 'description:' not in content:
            self.warnings.append("SKILL.md frontmatter 中缺少 description")
    
    def _scan_content(self, content: str, filename: str):
        """扫描内容中的模式"""
        # 检查危险模式
        for pattern, description in self.DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                issue = f"[{filename}] {description}: {pattern}"
                if '危险' in description or '后门' in description:
                    self.issues.append(issue)
                else:
                    self.warnings.append(issue)
        
        # 检查凭证模式
        for pattern, description in self.CREDENTIAL_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                # 检查是否只是占位符
                value = match.group(0)
                if not self._is_placeholder(value):
                    self.issues.append(f"[{filename}] {description}: {value[:30]}...")
        
        # 检查个人数据模式
        for pattern, description in self.PERSONAL_DATA_PATTERNS:
            matches = re.finditer(pattern, content)
            for match in matches:
                value = match.group(0)
                # 跳过明显的示例
                if not self._is_example(value):
                    self.warnings.append(f"[{filename}] {description}: {value}")
        
        # 检查模型特定引用（只是警告）
        for pattern, description in self.MODEL_PATTERNS:
            if re.search(pattern, content):
                self.warnings.append(f"[{filename}] {description}")
    
    def _is_placeholder(self, value: str) -> bool:
        """检查值是否为占位符"""
        placeholders = [
            '"your', "'your", 'your_', 'your-',
            'xxx', 'yyy', 'placeholder', 'example', 'demo',
            'test', 'fake', 'replace', 'insert', 'put_',
            'sk-xxx', 'sk-your', 'key_here', 'key-here',
        ]
        return any(p in value.lower() for p in placeholders)
    
    def _is_example(self, value: str) -> bool:
        """检查值是否为明显示例"""
        examples = ['example.com', 'test@', 'user@', 'demo@', '1234567890']
        return any(e in value.lower() for e in examples)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("用法: safety_checker.py <skill-path>")
        sys.exit(1)
    
    checker = SafetyChecker(Path(sys.argv[1]))
    result = checker.check()
    
    print(json.dumps(result, indent=2, ensure_ascii=False))