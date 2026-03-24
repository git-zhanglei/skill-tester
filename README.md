# skill-tester v3

> OpenClaw Skill 测试与认证框架

[![版本](https://img.shields.io/badge/version-3.0.0-blue.svg)](./_meta.json)
[![许可证](https://img.shields.io/badge/license-MIT-green.svg)](./SKILL.md)

## 概述

skill-tester 将 Skill 评估从主观的「好/坏」转变为客观、可量化的指标。通过 4 个阶段对目标 Skill 进行全面测试，输出包含安全状态、触发命中率、Skill规范程度、Agent理解度、执行成功率等维度的专业报告。

## 特性

### 🔒 安全门控
- 前置安全检查，发现严重问题立即终止
- 检查危险代码、凭证泄露、个人数据暴露

### 📊 4 维度量化评分

| 维度 | 权重 | 说明 |
|------|------|------|
| 触发命中率 | 25% | 触发词精确/模糊/负面测试 |
| Skill规范程度 | 20% | SKILL.md 格式与 OpenClaw 规范符合度 |
| Agent理解度 | 25% | Agent 是否准确理解并执行 Skill 意图 |
| 执行成功率 | 30% | 正常路径、边界、异常场景通过率 |

### 🤖 多 Agent 并行执行
- 默认 4 个 Agent 并行（可配置）
- 支持多模型分发：自动检测 OpenClaw 配置的模型，分散执行不同测试案例
- 独立会话隔离，测试互不干扰

### 🧠 Agent 泛化测试案例生成
- 调度 Agent 深度解析 SKILL.md
- 自动生成覆盖 4 个维度的多场景测试案例
- 支持自定义测试用例扩充

### 📝 专业报告
- Markdown 报告（人类可读）
- JSON 报告（CI/CD 集成）
- 多模型对比报告（启用 `--multi-model` 时）

## 快速开始

### 安装

```bash
# 复制到 skills 目录
cd ~/.openclaw/workspace/skills/skill-tester

# 验证安装
python3 verify.py
```

### 基本用法

```bash
# 基础测试（交互式）
测试skill ~/skills/my-skill/

# 自动确认（CI/CD）
测试skill ~/skills/my-skill/ --yes

# 多模型并行
测试skill ~/skills/my-skill/ --multi-model

# 完整认证
测试skill ~/skills/my-skill/ --yes --output-json --multi-model

# 使用已有测试案例集
测试skill ~/skills/my-skill/ --test-cases ./test-cases-my-skill-20260323.json

# 从断点继续
测试skill ~/skills/my-skill/ --resume
```

## 测试流程

```
┌─────────────────────────────────────────────────────────────┐
│                      skill-tester v3                         │
├─────────────────────────────────────────────────────────────┤
│  阶段 1: 安全检查（门控）                                   │
│  ├─ 危险代码模式 / 凭证泄露 / 个人数据检测                  │
│  └─ 通过→继续 / 警告→提示继续 / 失败→终止                  │
│                                                             │
│  阶段 2: 测试案例生成                                       │
│  ├─ Agent 解析 SKILL.md，泛化多场景测试案例                 │
│  ├─ 覆盖触发命中率/规范/理解度/执行成功率 4 维度            │
│  └─ 保存 JSON 测试案例集，用户确认                          │
│                                                             │
│  阶段 3: 多 Agent 并行执行                                  │
│  ├─ sessions_spawn 创建隔离会话                             │
│  ├─ 多模型分发（可选）                                      │
│  └─ 实时更新进度，持久化结果                                │
│                                                             │
│  阶段 4: 报告生成                                           │
│  └─ 4 维度评分 + 综合评分 + 优化建议                        │
└─────────────────────────────────────────────────────────────┘
```

## 评分体系

```
综合评分 = 触发命中率×25% + Skill规范程度×20% + Agent理解度×25% + 执行成功率×30%
```

**评级：**
- ⭐⭐⭐⭐⭐ 优秀（90–100）
- ⭐⭐⭐⭐ 良好（70–89）
- ⭐⭐⭐ 可接受（40–69）
- ⭐⭐ 需改进（0–39）
- ❌ 不合格（安全检查失败）

**特殊规则：**
- 安全检查失败 → 综合评分强制为 0
- 任意单维度低于 40 → 最终评级不超过 ⭐⭐⭐

## 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--yes` | `-y` | 跳过确认 | false |
| `--parallel` | `-p` | 并行度 | 4 |
| `--timeout` | `-t` | 超时时间（秒） | 60 |
| `--output-json` | — | 同时输出 JSON 报告 | false |
| `--multi-model` | — | 启用多模型分发 | false |
| `--models` | — | 指定模型列表 | 自动检测 |
| `--test-cases` | `-c` | 加载已有测试案例集 | — |
| `--resume` | `-r` | 断点续测 | false |
| `--skip-safety` | — | 跳过安全检查 | false |
| `--custom-tests` | — | 自定义测试用例 YAML | — |
| `--output` | `-o` | 报告输出路径 | 自动命名 |
| `--debug` | `-d` | 交互式调试模式 | false |

## 目录结构

```
skill-tester/
├── SKILL.md                    # 主文档（Agent 操作指南）
├── README.md                   # 本文件
├── verify.py                   # 安装验证脚本
├── install.py                  # 安装脚本
├── scripts/
│   ├── safety_checker.py       # 安全检查
│   ├── spec_checker.py         # 规范结构检查（14 项）
│   ├── smart_test_generator.py # Agent 泛化测试案例生成
│   ├── parallel_test_runner.py # 测试协调器（prepare/record/finalize）
│   ├── test_cases_validator.py # 测试案例格式验证
│   ├── report_builder.py       # 报告生成 + EVAL.md 输出
│   ├── error_analyzer.py       # 错误诊断
│   └── constants.py            # 常量定义
├── references/
│   ├── config.md               # 配置说明
│   ├── test-cases.md           # 测试案例格式与维度
│   ├── executors.md            # 多 Agent 执行细节
│   ├── reviewers.md            # 评分体系说明
│   ├── safety-checker.md       # 安全检查实现
│   ├── report-template.md      # 报告模板
│   ├── ci-cd.md                # CI/CD 集成指南
│   └── troubleshooting.md      # 故障排除
└── tests/
    ├── test_core.py            # 核心单元测试（70 个）
    └── test_integration.py     # 集成测试
```

## 社区发布标准

| 指标 | 最低要求 | 推荐标准 |
|------|----------|----------|
| 安全检查 | 通过 | 通过（无警告） |
| 触发命中率 | ≥ 85% | ≥ 95% |
| Skill规范程度 | ≥ 70% | ≥ 90% |
| Agent理解度 | ≥ 70% | ≥ 85% |
| 执行成功率 | ≥ 75% | ≥ 90% |
| 综合评分 | ≥ 70（⭐⭐⭐⭐） | ≥ 85（⭐⭐⭐⭐⭐） |

## 与历史版本对比

| 特性 | V1 | V2 | V3 |
|------|----|----|-----|
| 流程 | 5阶段连续 | 分阶段+确认 | 4阶段+门控安全 |
| 评分维度 | 5维度（混乱） | 3维度（不统一） | **4维度（统一）** |
| 多模型 | ❌ | ❌ | **✅** |
| Agent泛化测试案例 | ❌ | 部分 | **✅** |
| Agent理解度测试 | ❌ | ❌ | **✅** |
| Skill规范检查 | 基础 | 基础 | **完整** |
| CI/CD | 困难 | 支持 | **原生支持** |
| 断点续测 | ❌ | ✅ | ✅ |
| 文档一致性 | 低 | 低 | **高** |

## 故障排除

详见 [references/troubleshooting.md](./references/troubleshooting.md)（如不存在请参考 SKILL.md 故障排除章节）。

---

**为 OpenClaw 社区用 ❤️ 制作 — skill-tester v3**
