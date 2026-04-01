# skill-tester

> OpenClaw Skill 四维度质量测试与认证框架

## 概述

skill-tester 将 Skill 评估从主观的"好/坏"转变为客观、可量化的指标。通过安全门控、沙箱可测性预检与分阶段测试流程，对目标 Skill 进行全面测试，输出专业认证报告。

## 特性

- **🔒 安全门控** — 前置安全检查（危险代码、凭证泄露、个人数据），严重问题立即终止
- **📊 四维度量化评分** — 触发命中率(25%) + Skill规范程度(20%) + Agent理解度(25%) + 执行成功率(30%)
- **🧠 智能测试生成** — 解析 SKILL.md 自动生成骨架，Agent 填充具体案例
- **🔄 分阶段执行** — Phase A(无依赖) → Phase B(依赖配置门控) → Phase C(有依赖)，支持断点续跑
- **📝 专业报告** — Markdown 报告 + JSON 报告(CI/CD) + EVAL.md 写入目标 Skill

## 快速开始

作为 OpenClaw Skill 使用，对话触发即可：

```
测试skill ~/skills/my-skill/
帮我评估一下这个 Skill 的质量
```

Agent 会自动执行 5 个步骤：安全检查 → 沙箱预检+规范评分 → 测试案例生成 → 分阶段执行 → 报告生成。

## 测试流程

```
步骤 1: 安全检查（门控）
  └─ 通过→继续 / 警告→提示继续 / 失败→终止（评分归零）

步骤 2: 沙箱可测性 + 规范评分
  ├─ sandbox_checker.py → compatible / incompatible
  ├─ spec_checker.py → 14 项检查，百分制
  └─ incompatible 时：Agent 分析依赖项

步骤 3: 测试案例生成
  ├─ smart_test_generator.py → 骨架（空 input/expected）
  ├─ Agent 读 SKILL.md 填充具体内容
  └─ test_cases_validator.py 验证 → 用户确认

步骤 4: 分阶段执行
  ├─ Phase A: 无依赖测试（触发命中率、对抗性、边界）
  ├─ Phase B: 依赖配置门控（向用户收集 AK/环境变量等）
  └─ Phase C: 有依赖测试（正常路径、幂等性、格式检验）

步骤 5: 报告生成
  └─ report_builder.py → Markdown + JSON + EVAL.md
```

## 评分体系

```
综合评分 = 触发命中率×25% + Skill规范程度×20% + Agent理解度×25% + 执行成功率×30%
```

- ⭐⭐⭐⭐⭐ 优秀（90–100）→ 🏆 Certified
- ⭐⭐⭐⭐ 良好（70–89）→ ✅ Qualified
- ⭐⭐⭐ 可接受（40–69）→ 🔄 Beta
- ⭐⭐ 需改进（< 40）→ 🔄 Beta
- ❌ 不合格 — 安全检查失败 → 综合评分强制为 0

**特殊规则：** 任意单维度 < 40 → 最终评级不超过 ⭐⭐⭐。

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--yes` | 跳过用户确认 | - |
| `--timeout <n>` | 每案例超时（秒） | 120 |
| `--trials <n>` | critical 案例重复次数 | 3 |
| `--output-json` | 同时输出 JSON 报告 | - |
| `--eval-md` | 写入 EVAL.md 到目标 Skill 目录 | - |
| `--dry-run` | 仅步骤 1-2.5（静态分析） | - |
| `--skip-safety` | 跳过安全检查（调试用） | - |
| `--dimension <dim>` | 只执行指定维度 | - |

环境变量 `OPENCLAW_WORKSPACE`：工作目录（默认 `~/.openclaw/workspace`），影响测试产物存储位置。

## 目录结构

```
skill-tester/
├── SKILL.md                        # Agent 操作指南（触发后加载）
├── README.md                       # 本文件（人类阅读）
├── scripts/
│   ├── constants.py                # 常量定义（权重、阈值、路径）
│   ├── safety_checker.py           # 安全检查
│   ├── sandbox_checker.py          # 沙箱可测性检查
│   ├── spec_checker.py             # 规范检查（14 项）
│   ├── smart_test_generator.py     # 测试骨架生成
│   ├── test_cases_validator.py     # 案例格式验证
│   ├── parallel_test_runner.py     # 测试协调器（prepare/record/finalize）
│   ├── report_builder.py           # 报告生成 + EVAL.md
│   ├── frontmatter_parser.py       # YAML frontmatter 解析
│   └── ci_gate.py                  # CI/CD 门控脚本
├── references/
│   ├── test-cases.md               # 测试案例 JSON 格式与维度说明
│   ├── executors.md                # 分阶段执行命令详解
│   ├── reviewers.md                # 评分公式与评审逻辑
│   ├── safety-checker.md           # 安全检查规则详情
│   ├── config.md                   # 命令行参数与评分权重
│   ├── ci-cd.md                    # CI/CD 集成（GitHub Actions）
│   └── troubleshooting.md          # 常见问题排查
└── tests/
    ├── test_core.py                # 核心单元测试
    └── test_integration.py         # 集成测试
```

## 测试产物

所有产物存储在 `<workspace>/.skill-tester/`：

```
.skill-tester/
├── test-cases/     # 测试案例 JSON（含执行结果）
├── results/        # 中间结果
└── reports/        # 最终报告（Markdown + JSON）
```

## CI/CD 集成

```bash
# 门控检查（exit code 0=通过, 1=失败）
python3 scripts/ci_gate.py <report.json> --min-score 70
```

详见 [references/ci-cd.md](./references/ci-cd.md)。

## 开发

```bash
# 运行测试
python3 -m pytest tests/ -v

# 自测规范分数
python3 scripts/spec_checker.py . --json
```

## 许可证

MIT
