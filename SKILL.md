---
name: skill-tester
description: "测试并认证一个 OpenClaw Skill 的质量，输出包含安全评分、触发命中率、规范程度、Agent理解度和执行成功率的完整报告。当用户说「测试skill」「skill测试」「评估skill」「certify skill」时触发。"
user-invocable: true
source: "inspired by terwox/skill-evaluator, mgechev/skillgrade, rustyorb/agent-evaluation"
---

# skill-tester

对指定的 OpenClaw Skill 进行四维度质量评估，输出可量化的认证报告。

## Guardrails

- **不测试生产数据**：涉及真实用户数据时拒绝执行
- **安全失败即终止**：步骤 1 `failed` → 综合评分 0
- **不泄露内部实现**、**不自我测试**
- **防止测试数据污染**：子 Agent 不得知晓预期结果，主 Agent 事后独立评估

## 参数

- **`<skill_path>`**：目标 Skill 目录。未提供则询问
- `--yes`：跳过确认 | `--timeout <n>`：每案例超时秒（默认 120）
- `--trials <n>`：critical 案例重复次数（默认 3） | `--parallel <n>`：并行数（默认 4）
- `--output-json`：同时输出 JSON（CI/CD 用） | `--eval-md`：写入 EVAL.md
- `--dry-run`：仅步骤 1-2.5 | `--skip-safety`：跳过安全检查（调试用）

## 步骤 1：安全检查（门控）

```bash
python3 {baseDir}/scripts/safety_checker.py <skill_path>
```
`passed` → 继续 | `warning` → 展示并询问 | `failed` → **终止，综合归零**

## 步骤 1.5：沙箱可测试性检查

```bash
python3 {baseDir}/scripts/sandbox_checker.py <skill_path>
```
记录 `sandbox_check`。`sandbox_incompatible` 时步骤 3 确认前须明确风险告知。

## 步骤 2：规范程度检查

```bash
python3 {baseDir}/scripts/spec_checker.py <skill_path> --json
```
取 `summary.spec_score` 作为 Skill规范程度得分。`--dry-run` 时跳到步骤 5。

## 步骤 2.5：构造执行环境

若 `sandbox_incompatible`，基于 `setup_checklist` 逐项引导用户补齐依赖（环境变量、网络、浏览器等）。所有依赖就绪后才进入步骤 3。`sandbox_compatible` 时跳过。

## 步骤 3：生成测试案例

1. **自动生成**：`python3 {baseDir}/scripts/smart_test_generator.py <skill_path>`
2. **Agent 审查**：根据目标 Skill 业务逻辑补充调整，质量优先，总数 ≤ 30
3. **保存**为 JSON（含 `safety`/`spec_score`/`sandbox_check`），验证：`python3 {baseDir}/scripts/test_cases_validator.py <cases_json>`
4. **用户确认门控**：展示全部案例。`--yes` 跳过；`sandbox_incompatible` 须告知风险

四维度设计详见 [references/test-cases.md](./references/test-cases.md)。

## 步骤 4：执行测试案例

**4.1** 生成执行计划（自动跳过已完成案例，支持断点续跑）：
```bash
python3 {baseDir}/scripts/parallel_test_runner.py <cases_json> --prepare [--trials 3] [--dimension <dim>]
```

**4.2** 对每个 task 调用 `sessions_spawn`，传入纯净 `task_description`。必须拿到输出才可记录。

**4.3** 评估并记录（Token 从子 Agent completion stats 提取）：
```bash
python3 {baseDir}/scripts/parallel_test_runner.py <cases_json> \
    --record <case_id> --status passed|failed|error \
    --outcome "摘要" --session-id "<id>" --tokens-in <N> --tokens-out <N>
```

**4.4 早期终止**：连续 3 个案例同因失败 → 停止，报告根因，建议修复后重试。

**4.5** 汇总：`python3 {baseDir}/scripts/parallel_test_runner.py <cases_json> --finalize`

## 步骤 5：生成报告

```
触发命中率    = (精确×0.4 + 模糊×0.4 + 负面×0.2) / 加权总数 × 100
Skill规范程度 = spec_score
Agent理解度   = (outcome_check + format_check) pass / 总数 × 100
执行成功率    = (normal×0.40 + boundary×0.25 + error×0.20 + adversarial×0.10 + idempotency×0.05) / 加权总数 × 100
综合评分      = 命中率×0.25 + 规范×0.20 + 理解度×0.25 + 成功率×0.30
```
安全 `failed` → 综合归零；任意维度 < 40 → 评级上限 ⭐⭐⭐

```bash
python3 {baseDir}/scripts/report_builder.py <cases_json> [--eval-md <skill_path>] [--json]
```
`--eval-md` 生成 EVAL.md；`--json` 输出 JSON 供 CI/CD（配合 `ci_gate.py` 使用）。

## 评级

| 综合评分 | 评级 | 认证 |
|---------|------|------|
| 90–100 | ⭐⭐⭐⭐⭐ 优秀 | 🏆 Certified |
| 70–89 | ⭐⭐⭐⭐ 良好 | ✅ Verified |
| 40–69 | ⭐⭐⭐ 可接受 | 🔄 Beta |
| 0–39 | ⭐⭐ 需改进 | — |

## 已知限制

- Agent 非确定性 → 使用 pass@3 | 子 Agent 知晓预期 → 测试失效
- sessions_spawn 不支持 skills 参数 → 目标 Skill 须已在 available_skills 中配置
- 依赖未补齐时测试不可信 → 务必先完成步骤 2.5

## 参考文档

- [test-cases.md](./references/test-cases.md) | [executors.md](./references/executors.md) | [reviewers.md](./references/reviewers.md)
- [safety-checker.md](./references/safety-checker.md) | [report-template.md](./references/report-template.md)
- [troubleshooting.md](./references/troubleshooting.md) | [ci-cd.md](./references/ci-cd.md) | [config.md](./references/config.md)
