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
- **测试案例禁止包含真实危险操作**：adversarial 案例中不得出现 `rm -rf`、`mkfs`、`dd if=`、`:(){:|:&};:`、`> /dev/sda` 等破坏性命令。用无害占位符替代（如 `echo SIMULATED_DANGEROUS_COMMAND`）。原因：子 Agent 可能拥有高权限且不一定拒绝执行，后果不可逆

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

## 步骤 2.5：依赖分析与环境准备

**2.5.1 确认 Skill 已安装**（必须）：检查目标 Skill 是否出现在当前 `available_skills` 中。若不在，**停止测试**并告知用户：
> ⚠️ 目标 Skill `{name}` 未被 OpenClaw 发现。请先安装到 `~/.openclaw/skills/` 或 `<workspace>/skills/`，然后重新开始测试。

**2.5.2 依赖项分析**（`sandbox_incompatible` 时）：阅读目标 SKILL.md + `sandbox_checker` 输出，提取结构化依赖清单，填入案例 JSON 的 `dependencies.items`：
```json
{
  "id": "ak",
  "name": "ALI_1688_AK",
  "type": "env_var",
  "description": "1688 API Access Key，用于调用所有业务接口",
  "configure_hint": "执行 cli.py configure YOUR_AK 或 export ALI_1688_AK=xxx",
  "verify_command": "python3 {baseDir}/cli.py check",
  "verify_expect": "configured",
  "status": "unverified"
}
```
每个依赖须有 `verify_command`（可执行的验证命令）和 `verify_expect`（输出中应包含的关键词）。

**2.5.3 向用户展示依赖状态**：列出所有依赖及其当前状态，告知用户：
- 测试将分两阶段：先测无依赖场景（Phase A），再测有依赖场景（Phase C）
- Phase C 执行前需要配置依赖项
- 用户可以选择现在配置、稍后配置、或跳过 Phase C

`sandbox_compatible` 时跳过 2.5.2 和 2.5.3。

## 步骤 3：生成测试案例

1. **生成骨架**：`python3 {baseDir}/scripts/smart_test_generator.py <skill_path> --skeleton`
2. **Agent 填充**：读目标 SKILL.md，为每个骨架案例填充 `input` 和 `expected`（参考 `hints` 但以自身理解为准），可增删案例，总数 ≤ 30
3. **保存** JSON 到 `<workspace>/.skill-tester/test-cases/test-cases-{skill_name}-{YYYYMMDD}.json`（`<workspace>` 即 Agent 的工作目录，通常为 `~/.openclaw/workspace`）。骨架已包含 `version`/`cases`/`execution`，Agent 补充 `safety`/`spec_score`/`sandbox_check` 字段后验证：`python3 {baseDir}/scripts/test_cases_validator.py <cases_json>`
4. **用户确认门控（强制）**：在执行前**必须**将全部案例以列表形式展示给用户确认。格式要求：
   - 按维度分组，每个案例显示：`id` | `type` | `input`（完整）| `expected`（完整）
   - 末尾附总数统计
   - 用户确认后才进入步骤 4；`--yes` 跳过此门控
   - `sandbox_incompatible` 须同时告知风险

四维度设计详见 [references/test-cases.md](./references/test-cases.md)。

**跨步骤变量**（Agent 须在全流程中保持）：
- `safety_status`: 步骤 1 输出（passed/warning/failed）
- `spec_score`: 步骤 2 输出（float）
- `sandbox_check`: 步骤 1.5 输出（compatible/incompatible + setup_checklist）
- `cases_json`: 步骤 3 保存路径

## 步骤 4：执行测试案例

执行流程由案例 JSON 中的 `phases` 状态机驱动。Agent 每次操作后通过 CLI 更新 JSON，确保可断点续跑。

### Phase A：无依赖测试

1. `--prepare --phase phase_a` 获取任务列表
2. 逐个执行 + `--record` 记录
3. 全部完成后 `--advance-phase` 推进状态

### Phase B：依赖配置门控

1. `--phase-status` 确认进入 Phase B
2. `--verify-all-deps` 检查依赖状态
3. 未通过的依赖 → 向用户展示 `configure_hint`，等待用户配置
4. 用户配置后 → `--verify-dep <id>` 逐项验证
5. 全部通过 → `--advance-phase` 进入 Phase C
6. 用户选择跳过 → Phase C 案例标记为 `skipped`，直接进入步骤 5

### Phase C：有依赖测试

1. `--prepare --phase phase_c` 获取任务列表
2. 逐个执行 + `--record` 记录
3. 全部完成后 `--advance-phase` 完成所有阶段

**早期终止**：任意 phase 中连续 3 个同因失败 → 停止当前 phase，报告根因。

按 [references/executors.md](./references/executors.md) 了解详细命令用法。

## 步骤 5：生成报告

```bash
python3 {baseDir}/scripts/report_builder.py <cases_json> [--eval-md <skill_path>] [--json]
```
安全 `failed` → 综合归零；任意维度 < 40 → 评级上限 ⭐⭐⭐。评分公式详见 [references/reviewers.md](./references/reviewers.md)。

**报告展示（强制）**：将 `report_builder.py` 生成的 Markdown 报告**完整原文**展示给用户（不得摘取、总结或省略）。如有根因分析或优化建议，**追加在报告原文之后**，明确标注为 Agent 补充分析。

`--eval-md` 生成 EVAL.md；`--json` 输出 JSON 供 CI/CD（配合 `ci_gate.py` 使用）。

## 评级

- **90–100** ⭐⭐⭐⭐⭐ 优秀 → 🏆 Certified
- **70–89** ⭐⭐⭐⭐ 良好 → ✅ Verified
- **40–69** ⭐⭐⭐ 可接受 → 🔄 Beta
- **0–39** ⭐⭐ 需改进

## 已知限制

- Agent 非确定性 → 使用 pass@3 | 子 Agent 知晓预期 → 测试失效
- sessions_spawn 不支持 skills 参数 → 目标 Skill 必须已正确安装（步骤 2.5.1 检查）
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
