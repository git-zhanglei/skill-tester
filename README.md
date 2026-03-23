# Skill Certifier

> OpenClaw skill 综合测试和认证框架

[![版本](https://img.shields.io/badge/version-1.0.0-blue.svg)](./_meta.json)
[![许可证](https://img.shields.io/badge/license-MIT-green.svg)](./SKILL.md)

## 概述

Skill Certifier 将 skill 评估从主观的"好/坏"转变为客观的、可量化的指标。它提供自动化测试、多维度质量评估和专业认证报告。

## 特性

### 🔒 安全第一
- 自动化安全预检
- 恶意代码检测
- 凭证泄露检测
- 个人数据暴露检查

### 📊 定量指标
- **触发命中率** (25%): 触发词激活准确度
- **任务成功率** (30%): 任务完成百分比
- **分支覆盖率** (20%): 代码路径覆盖
- **工具调用准确度** (15%): 工具选择精确度
- **错误处理** (10%): 异常覆盖

### 🤖 并行执行
- 多代理并行测试（默认：4 个代理）
- 可配置并行度
- 隔离测试环境
- 自动清理

### 📝 专业报告
- 带总分的执行摘要
- 按维度的详细测试结果
- 定性评估（结构/实用性/领域）
- 优先级排序的优化建议

## 快速开始

### 安装

```bash
# 克隆或复制到 skills 目录
cd ~/.openclaw/workspace/skills/skill-certifier

# 验证安装
python3 verify.py
```

### 基本用法

```bash
# 测试 skill
测试skill ./my-skill/

# 自定义并行度
测试skill ./my-skill/ --parallel 8

# 带 API key
测试skill ./my-skill/ --env API_KEY=xxx,SECRET=yyy

# JSON 输出
测试skill ./my-skill/ --format json --output report.json
```

## 测试流程

```
┌─────────────────────────────────────────────────────────────┐
│                   Skill-Certifier                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  阶段 1: 安全预检                                           │
│  ├─ 恶意代码检测                                            │
│  ├─ 凭证泄露检查                                            │
│  └─ 个人数据暴露扫描                                        │
│                                                             │
│  阶段 2: 深度分析                                           │
│  ├─ 解析 SKILL.md                                           │
│  ├─ 提取触发词、工具、工作流                                │
│  └─ 生成测试策略                                            │
│                                                             │
│  阶段 3: 多维度测试                                         │
│  ├─ 命中率测试（并行）                                      │
│  ├─ 成功率测试（并行）                                      │
│  ├─ 分支覆盖测试（并行）                                    │
│  └─ 工具准确度测试（并行）                                  │
│                                                             │
│  阶段 4: 定性评估                                           │
│  ├─ 结构评审器                                              │
│  ├─ 实用性评审器                                            │
│  └─ 领域评审器                                              │
│                                                             │
│  阶段 5: 报告生成                                           │
│  └─ 集成定量 + 定性报告                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 配置

### 默认配置

```yaml
# ~/.skill-certifier/config.yaml
parallel_degree: 4
timeout_per_test: 60
max_test_cases_per_dimension: 20

weights:
  hit_rate: 25
  success_rate: 30
  branch_coverage: 20
  tool_accuracy: 15
  error_handling: 10

thresholds:
  excellent: 80
  good: 60
  acceptable: 40
```

### 环境变量

```bash
export SKILL_CERTIFIER_PARALLEL=8
export SKILL_CERTIFIER_TIMEOUT=120
export SKILL_CERTIFIER_FORMAT=markdown
```

## 报告示例

```markdown
# Skill 评估报告: my-skill

**生成时间:** 2024-01-15 10:30:00
**总分:** 87.5/100
**建议:** ⭐⭐⭐⭐⭐ 优秀

## 1. 执行摘要

此 skill 在所有指标上表现出色...

### 关键指标

| 指标 | 分数 | 状态 |
|--------|-------|--------|
| 总分 | 87.5/100 | ✅ |
| 安全 | ✅ 通过 | 通过 |
| 触发命中率 | 92.0% | ✅ |
| 任务成功率 | 85.0% | ✅ |

## 6. 优化建议

### 高优先级
1. **结构：添加代码示例**
   - 影响：结构分数 85/100
   - 建议：添加代码示例以提高清晰度

### 中优先级
1. **领域：添加认证说明**
   - 影响：领域分数 75/100
   - 建议：添加获取 API key 的章节
```

## 架构

```
skill-certifier/
├── SKILL.md                    # 主文档
├── skill-certifier             # CLI 入口
├── _meta.json                  # 元数据
├── scripts/                    # 核心脚本
│   ├── certifier.py           # 主协调器
│   ├── safety_checker.py      # 安全检查
│   ├── test_generator.py      # 测试用例生成
│   ├── test_executor.py       # 并行测试执行
│   ├── qualitative_reviewers.py # 质量评估
│   └── report_generator_cn.py # 报告生成（中文）
├── references/                 # 文档
│   ├── config.md              # 配置指南
│   ├── test-cases.md          # 测试用例指南
│   ├── executors.md           # 执行详情
│   ├── reviewers.md           # 评审器文档
│   ├── safety-checker.md      # 安全检查指南
│   └── report-template.md     # 报告模板
└── examples/                   # 用法示例
    └── example-usage.md
```

## 与 Skill Test 对比

| 特性 | Skill Test | Skill Certifier |
|---------|-----------|-----------------|
| 目标用户 | 最终用户 | Skill 开发者 |
| 测试阶段 | 安装前 | 发布前 |
| 指标 | 定性 | 定量 + 定性 |
| 并行执行 | ❌ | ✅（默认 4 代理） |
| 工具调用测试 | ❌ | ✅ |
| 命中率指标 | ❌ | ✅ |
| 分支覆盖 | ❌ | ✅ |
| 专业报告 | 简单 | 综合 |
| CI/CD 集成 | ❌ | ✅ |

## 故障排除

### 测试挂起

```bash
# 增加超时
测试skill ./my-skill/ --timeout 120

# 降低并行度
测试skill ./my-skill/ --parallel 2
```

### 覆盖率低

```bash
# 添加自定义测试用例
# 编辑 ~/.skill-certifier/custom-tests.yaml

# 详细输出运行
测试skill ./my-skill/ --verbose
```

### 安全警告

```bash
# 先检查安全问题
测试skill ./my-skill/ --skip-safety
```

## 贡献

1. Fork 仓库
2. 创建功能分支
3. 进行更改
4. 彻底测试
5. 提交 pull request

## 许可证

MIT - 详情见 [SKILL.md](./SKILL.md)

## 致谢

- 嵌入逻辑来自 [Skill Test](https://clawhub.ai/ivangdavila/skill-test) by @ivangdavila
- 受软件测试最佳实践启发
- 为 OpenClaw 社区构建

---

**为 OpenClaw 社区用 ❤️ 制作**