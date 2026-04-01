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
- `--trials <n>`：critical 案例重复次数（默认 3）
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

1. **生成骨架**：`python3 {baseDir}/scripts/smart_test_generator.py <skill_path> --skeleton`
2. **Agent 填充**：读目标 SKILL.md，为每个骨架案例填充 `input` 和 `expected`（参考 `hints` 但以自身理解为准），可增删案例，总数 ≤ 30
3. **保存** JSON 到 `~/.skill-tester/test-cases/test-cases-{skill_name}-{YYYYMMDD}.json`。骨架已包含 `version`/`cases`/`execution`，Agent 补充 `safety`/`spec_score`/`sandbox_check` 字段后验证：`python3 {baseDir}/scripts/test_cases_validator.py <cases_json>`
4. **用户确认门控**：展示全部案例。`--yes` 跳过；`sandbox_incompatible` 须告知风险

四维度设计详见 [references/test-cases.md](./references/test-cases.md)。

**跨步骤变量**（Agent 须在全流程中保持）：
- `safety_status`: 步骤 1 输出（passed/warning/failed）
- `spec_score`: 步骤 2 输出（float）
- `sandbox_check`: 步骤 1.5 输出（compatible/incompatible + setup_checklist）
- `cases_json`: 步骤 3 保存路径

## 步骤 4：执行测试案例

按 [references/executors.md](./references/executors.md) 执行：

1. `--prepare` 生成执行计划（自动跳过已完成，支持断点续跑）
2. 对每个 task 调用 `sessions_spawn`，传入纯净 `task_description`
3. `--record` 评估并记录结果（含 token 统计）
4. **早期终止**：连续 3 个同因失败 → 停止，报告根因
5. `--finalize` 汇总

## 步骤 5：生成报告

```bash
python3 {baseDir}/scripts/report_builder.py <cases_json> [--eval-md <skill_path>] [--json]
```
安全 `failed` → 综合归零；任意维度 < 40 → 评级上限 ⭐⭐⭐。评分公式详见 [references/reviewers.md](./references/reviewers.md)。

`--eval-md` 生成 EVAL.md；`--json` 输出 JSON 供 CI/CD（配合 `ci_gate.py` 使用）。

## 评级

- **90–100** ⭐⭐⭐⭐⭐ 优秀 → 🏆 Certified
- **70–89** ⭐⭐⭐⭐ 良好 → ✅ Verified
- **40–69** ⭐⭐⭐ 可接受 → 🔄 Beta
- **0–39** ⭐⭐ 需改进

## 已知限制

- Agent 非确定性 → 使用 pass@3 | 子 Agent 知晓预期 → 测试失效
- sessions_spawn 不支持 skills 参数 → 目标 Skill 须已在 available_skills 中配置
- 依赖未补齐时测试不可信 → 务必先完成步骤 2.5

## 参考文档（按需加载）

- **步骤 3 详解** → [test-cases.md](./references/test-cases.md)：四维度案例格式与示例
- **步骤 4 详解** → [executors.md](./references/executors.md)：执行命令、断点续跑、错误处理
- **步骤 5 详解** → [reviewers.md](./references/reviewers.md)：评分公式与评审逻辑
- **报告格式** → [report-template.md](./references/report-template.md)：报告结构与输出样例
- **安全检查规则** → [safety-checker.md](./references/safety-checker.md)：步骤 1 的检查规则详情
- **CI/CD 集成** → [ci-cd.md](./references/ci-cd.md)：`ci_gate.py` 用法和 GitHub Actions 示例
- **常见问题** → [troubleshooting.md](./references/troubleshooting.md)：执行失败排查
- **高级配置** → [config.md](./references/config.md)：超时、早期终止等参数调整
