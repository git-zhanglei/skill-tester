---
name: skill-tester
description: "测试并认证一个 OpenClaw Skill 的质量，输出包含安全评分、触发命中率、规范程度、Agent理解度和执行成功率的完整报告。当用户说「测试skill」「skill测试」「评估skill」「certify skill」时触发。"
user-invocable: true
source: "inspired by terwox/skill-evaluator, mgechev/skillgrade, rustyorb/agent-evaluation"
---

# skill-tester

对指定的 OpenClaw Skill 进行四维度质量评估，输出可量化的认证报告。

> `{baseDir}` = 本 Skill 的安装目录（即包含此 SKILL.md 的目录）。

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
- 环境变量 `OPENCLAW_WORKSPACE`：工作目录（默认 `~/.openclaw/workspace`），影响测试产物存储

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

**2.5.2 依赖项分析**（`sandbox_incompatible` 时）：阅读目标 SKILL.md + `sandbox_checker` 输出，提取结构化依赖清单，填入案例 JSON 的 `dependencies.items`。每个依赖须有 `verify_command` 和 `verify_expect`。格式详见 [test-cases.md](./references/test-cases.md)。

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

执行流程由案例 JSON 中的 `phases` 状态机驱动（Phase A → B → C），支持断点续跑。

- **sandbox_compatible** 的 Skill：只有 Phase A，直接执行所有案例
- **sandbox_incompatible** 的 Skill：Phase A（无依赖测试）→ Phase B（依赖配置门控，向用户收集配置）→ Phase C（有依赖测试）

每个案例通过 `sessions_spawn` 发给子 Agent 执行，主 Agent 对比输出与 expected 评估结果，再用 `--record` 记录。

**早期终止**：连续 3 个同因失败 → 停止执行，报告根因。

详细命令用法（prepare/record/advance-phase/verify-dep 等）见 [references/executors.md](./references/executors.md)。

## 步骤 5：生成报告

```bash
python3 {baseDir}/scripts/report_builder.py <cases_json> [--eval-md <skill_path>] [--json]
```
评分公式与特殊规则详见 [references/reviewers.md](./references/reviewers.md)。

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

- **步骤 3 详解** → [test-cases.md](./references/test-cases.md)：四维度案例格式、依赖项 JSON 结构与示例
- **步骤 4 详解** → [executors.md](./references/executors.md)：执行命令、断点续跑、分阶段流程
- **步骤 5 详解** → [reviewers.md](./references/reviewers.md)：评分公式与评审逻辑
- **安全检查规则** → [safety-checker.md](./references/safety-checker.md)：步骤 1 的检查规则详情
- **CI/CD 集成** → [ci-cd.md](./references/ci-cd.md)：`ci_gate.py` 用法和 GitHub Actions 示例
- **常见问题** → [troubleshooting.md](./references/troubleshooting.md)：执行失败排查
- **参数配置** → [config.md](./references/config.md)：命令行参数、评分权重
