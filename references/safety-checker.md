# 安全检查器

## 概述

安全检查是 Skill Certifier v3 的**前置门控**。检查失败将立即终止测试并将综合评分归零。安全检查结果不计入评分，但作为独立状态呈现在报告中。

## 检查类别

### 1. 危险代码模式

检测可能危害系统的命令或操作：

| 模式 | 严重级别 | 描述 |
|------|---------|------|
| `rm -rf /` 或 `rm -rf /*` | ❌ 严重 | 递归删除根目录 |
| `> /etc/` | ❌ 严重 | 覆写系统配置文件 |
| `chmod 777 /` | ❌ 严重 | 开放所有权限 |
| `curl ... \| sh` 或 `wget ... \| sh` | ❌ 严重 | 管道到 Shell 执行 |
| `nc -l` | ⚠️ 高 | Netcat 监听，可能开放后门 |
| 加密货币挖矿关键词 | ❌ 严重 | 挖矿软件特征 |
| `eval(` + 外部输入 | ⚠️ 高 | 动态代码执行风险 |
| `subprocess.call` + shell=True | ⚠️ 中 | Shell 注入风险 |

### 2. 凭证泄露模式

检测硬编码的敏感信息：

| 模式 | 严重级别 | 描述 |
|------|---------|------|
| `api_key\s*=\s*["'][^"']{8,}` | ❌ 严重 | 硬编码 API Key |
| `password\s*=\s*["'][^"']+` | ❌ 严重 | 硬编码密码 |
| `token\s*=\s*["'][^"']{16,}` | ❌ 严重 | 硬编码 Token |
| `AKIA[0-9A-Z]{16}` | ❌ 严重 | AWS Access Key |
| `-----BEGIN (RSA\|EC\|DSA) PRIVATE KEY` | ❌ 严重 | 私钥文件 |
| `ghp_[0-9a-zA-Z]{36}` | ❌ 严重 | GitHub PAT |

### 3. 个人数据暴露

检测可能包含个人信息的内容：

| 模式 | 严重级别 | 描述 |
|------|---------|------|
| 邮箱地址（非 example.com） | ⚠️ 警告 | 真实用户邮箱 |
| SSN 格式 `\d{3}-\d{2}-\d{4}` | ❌ 严重 | 美国社会安全号 |
| 信用卡格式 `\d{4}[- ]\d{4}[- ]\d{4}[- ]\d{4}` | ❌ 严重 | 信用卡号 |
| 手机号格式（11位）| ⚠️ 警告 | 可能的真实手机号 |

### 4. 模型特定引用（记录但不扣分）

以下内容会记录在报告中，但不影响安全状态：
- "Claude"、"GPT-4"、"Codex" 等特定模型名称
- 硬编码模型 API 端点

## 安全状态说明

| 状态 | 条件 | 对测试的影响 |
|------|------|------------|
| ✅ 通过 | 无严重问题，无警告 | 正常继续 |
| ⚠️ 警告 | 有警告但无严重问题 | 提示用户后继续 |
| ❌ 失败 | 发现任意严重问题 | **立即终止，综合评分归零** |

## 实现

实现细节见 `../scripts/safety_checker.py`。

### 使用方式

```python
from safety_checker import SafetyChecker
from pathlib import Path

checker = SafetyChecker(Path('./my-skill'))
result = checker.check()

print(result['status'])    # passed / warning / failed
print(result['issues'])    # 严重问题列表
print(result['warnings'])  # 警告列表
```

### 输出格式

```json
{
  "status": "passed",
  "issues": [],
  "warnings": [
    "发现邮箱地址：user@example.com（第 45 行）"
  ],
  "checked_files": [
    "SKILL.md",
    "scripts/helper.py",
    "references/config.md"
  ],
  "checked_at": "2026-03-23T10:00:00"
}
```

## 绕过安全检查

仅用于调试或已知安全的场景，**不推荐生产使用**：

```bash
测试skill ~/skills/my-skill/ --skip-safety
```

绕过时报告中会明确标注"安全检查已跳过"。
