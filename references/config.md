# skill-tester — 配置说明

## 命令行参数（唯一配置方式）

所有配置通过命令行参数传入，无配置文件。

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--timeout <n>` | 120 | 每个测试案例超时（秒） |
| `--trials <n>` | 3 | critical 案例（exact_match/normal_path）重复次数 |
| `--yes` | - | 跳过用户确认门控 |
| `--dry-run` | - | 仅执行步骤 1-2.5（静态分析） |
| `--skip-safety` | - | 跳过安全检查（仅调试用） |
| `--output-json` | - | 同时输出 JSON 报告（CI/CD 用） |
| `--eval-md` | - | 写入 EVAL.md 到目标 Skill 目录 |
| `--dimension <dim>` | - | 只执行指定维度（切片测试） |

## 环境变量

| 变量 | 说明 |
|------|------|
| `OPENCLAW_WORKSPACE` | 工作目录（默认 `~/.openclaw/workspace`），影响测试产物存储位置 |

## 评分权重（固定）

| 维度 | 权重 | 说明 |
|------|------|------|
| 触发命中率 | 25% | 触发词不重要的工具类 Skill 可考虑降低 |
| Skill规范程度 | 20% | 静态分析 |
| Agent理解度 | 25% | 结果导向评估 |
| 执行成功率 | 30% | 核心能力，建议不低于 25% |

权重当前为代码硬编码（`constants.py`），暂不支持运行时调整。

## 早期终止

连续 3 个案例因相同原因失败时，`--finalize` 会建议终止。Agent 在执行过程中也应自行检测并停止。

根因分类：`skill_not_activated`、`timeout`、`spawn_unavailable`、`dependency_missing`。
