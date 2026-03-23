# 安全检查实现

嵌入自 Skill Test 安全评审器。

## 检查类别

### 1. 危险模式

检查可能危害系统的命令：

| 模式 | 严重级别 | 描述 |
|---------|----------|-------------|
| `rm -rf /` | 严重 | 危险删除 |
| `> /etc/` | 严重 | 系统文件修改 |
| `chmod 777` | 高 | 过度宽松权限 |
| `curl \| sh` | 高 | 管道到 shell |
| `nc -l` | 高 | Netcat 监听 |
| 加密货币挖矿 | 严重 | 挖矿软件模式 |

### 2. 凭证模式

检查硬编码密钥：

| 模式 | 严重级别 | 描述 |
|---------|----------|-------------|
| `api_key = "xxx"` | 严重 | 硬编码 API key |
| `password = "xxx"` | 严重 | 硬编码密码 |
| `token = "xxx"` | 严重 | 硬编码 token |
| AWS 凭证 | 严重 | AWS access keys |
| 私钥 | 严重 | SSH 私钥 |

### 3. 个人数据模式

检查暴露的个人信息：

| 模式 | 严重级别 | 描述 |
|---------|----------|-------------|
| 邮箱地址 | 警告 | user@example.com |
| SSN 模式 | 严重 | 123-45-6789 |
| 信用卡号 | 严重 | 1234-5678-9012-3456 |
| 长数字 | 警告 | 可能的身份证号 |

### 4. 模型特定引用

不危险，但会记录：

- "Claude"
- "GPT-4"
- "Codex"

## 实现

查看 `../scripts/safety_checker.py` 了解完整实现。

## 用法

```python
from safety_checker import SafetyChecker

checker = SafetyChecker(Path('./my-skill'))
result = checker.check()

if result['status'] == 'failed':
    print("发现安全问题！")
    for issue in result['issues']:
        print(f"  - {issue}")
```

## 输出格式

```json
{
  "status": "passed|warning|failed",
  "issues": ["严重问题 1", "严重问题 2"],
  "warnings": ["警告 1", "警告 2"],
  "checked_files": ["SKILL.md", "scripts/helper.py"]
}
```