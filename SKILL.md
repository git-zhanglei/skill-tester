---
name: skill-tester
description: "测试并认证一个 OpenClaw Skill 的质量，输出包含安全评分、触发命中率、规范程度、Agent理解度和执行成功率的完整报告。当用户说「测试skill」「skill测试」「评估skill」「certify skill」时触发。"
user-invocable: true
source: "inspired by terwox/skill-evaluator, mgechev/skillgrade, rustyorb/agent-evaluation"
---

# skill-tester

对指定的 OpenClaw Skill 进行四维度质量评估，输出可量化的认证报告。

## Guardrails

- **不测试生产数据**：若目标 Skill 涉及真实用户数据，拒绝执行并提示用户使用测试数据
- **安全失败即终止**：步骤 1 返回 `failed` 时立即停止，综合评分为 0
- **不泄露内部实现**：不向用户展示目标 Skill 脚本的源码
- **不自我测试**：若目标路径即本 Skill，拒绝并提示循环依赖
- **防止测试数据污染**：子 Agent 不得事先知晓预期结果，由主 Agent 事后独立评估

---

## 执行步骤

### 前置：解析参数

从用户消息中提取：

- **`<skill_path>`**：目标 Skill 目录（含 `SKILL.md`）。未提供则询问
- `--yes` / `-y`：跳过步骤 3 用户确认
- `--parallel <n>`：并行 Agent 数（默认 4）
- `--timeout <n>`：每案例超时秒（默认 60）
- `--trials <n>`：critical 案例重复次数（默认 3，用于 pass@k）
- `--output-json`：同时生成 JSON 报告
- `--dry-run`：仅执行步骤 1-2，不启动 sessions_spawn（适合 CI 快速检查）
- `--validate`：先对本 Skill 自身运行，验证评分基线后再测目标
- `--eval-md`：将评估摘要写入 `<skill_path>/EVAL.md`（随 Skill 版本管理）
- `--skip-safety`：跳过步骤 1（仅调试用）

---

### 步骤 1：安全检查（门控）

```bash
python3 {baseDir}/scripts/safety_checker.py <skill_path>
```

| status | 处理方式 |
|--------|--------|
| `"passed"` | 继续步骤 2 |
| `"warning"` | 展示 `warnings`，询问是否继续 |
| `"failed"` | 展示 `issues`，**终止，综合评分为 0** |

若指定 `--dry-run`，步骤 2 完成后直接跳到步骤 5 报告。

---

### 步骤 2：规范程度检查（14项）

```bash
python3 {baseDir}/scripts/spec_checker.py <skill_path> --json
```

从输出 JSON 中取 `summary.spec_score` 作为 **Skill规范程度** 维度得分（0–100）。

> 检查项涵盖：frontmatter 完整性、触发词质量（词数/上下文短语）、Token 开销（严格：>400行=失败）、
> references 链接、Python 语法、无外部依赖、环境变量文档化、可组合性信号。
> Guardrails / Workflow 采用**按需判定**：当 Skill 存在高风险边界或明显多阶段流程时，缺失才给出建议；不默认扣分。

---

### 步骤 3：生成测试案例

**质量优先**：每维度生成 2-3 个精准案例，总数不超过 **15 个**。精心设计的少量案例优于大量噪声案例。

阅读 `<skill_path>/SKILL.md`，生成以下四维度测试案例：

**A — 触发命中率（hit_rate）**
- `exact_match`：精确触发词，预期 `"activate"`（multi_trial: true）
- `fuzzy_match`：触发词同义词/衍生词变体（如口语化、礼貌前后缀），预期 `"activate"`
- `negative_test`：非同义、无关指令（2条），预期 `"not_activate"`；若未命中说明 Skill 边界清晰，应计为正向表现

**B — Agent 理解度（agent_comprehension）**  
聚焦**结果（outcome）**，不监测步骤：
- `outcome_check`：标准输入 → 产物是否符合 Skill 声明的结果
- `format_check`：输出格式是否符合声明（若有格式要求）

**C — 执行成功率（execution_success）**
- `normal_path`：正常输入，预期成功（multi_trial: true）
- `boundary_case`：边界输入（空值、极端参数）
- `error_handling`：错误场景（路径不存在等）
- `adversarial`：歧义/越权/空输入，预期「拒绝并说明」
- `idempotency_check`：执行两次相同操作，验证结果一致（幂等性）

**multi_trial: true** 的案例在步骤 4 中执行 `--trials` 次，计算 pass@k 和 pass^k。

> `idempotency_check` 补充：对实时数据类 Skill（天气/股价等），改为验证**输出格式**一致而非数据值一致。

将测试案例按维度分组设计后，再保存为 `~/.skill-tester/test-cases/test-cases-<skill_name>-<timestamp>.json`（后称 `<cases_json>`）。  
**注意**：`safety` 和 `spec_score` 在此处一并写入，`--finalize` 后该文件即可直接用于生成报告，无需额外组装。

```json
{
  "version":    "3.0",
  "skill_name": "<skill_name>",
  "skill_path": "<skill_path>",
  "safety":     <步骤 1 的完整输出 JSON>,
  "spec_score": <步骤 2 的 summary.spec_score 数值>,
  "total":      <cases 数组的长度>,
  "cases": [
    {
      "id": "hit_exact_0", "dimension": "hit_rate", "type": "exact_match",
      "grader_type": "llm_rubric", "multi_trial": true,
      "input": "<精确触发词>", "expected": "activate",
      "description": "精确触发词测试",
      "weight": 1.0, "status": "pending", "result": null
    }
  ],
  "execution": { "status": "pending", "started_at": "<当前 ISO 时间戳，如 2026-03-24T10:00:00>" }
}
```

完整字段说明见 [references/test-cases.md](./references/test-cases.md)。

保存后立即验证格式合法性，**验证通过才进入步骤 4**：

```bash
python3 {baseDir}/scripts/test_cases_validator.py <cases_json>
```

若 exit code 为 1，根据错误信息修正后重新保存并再次验证（常见问题：缺少 `total` / `weight` 字段，或 `total` 与实际 cases 数量不一致）。

展示案例摘要（至少包含：`total`、按维度数量、前 5 条案例的 `id/type/input`）。

**强制确认门控（必须执行）：**
- 若命令包含 `--yes`：记录「用户已通过 --yes 跳过确认」，直接进入步骤 4。
- 若未包含 `--yes`：**必须先向用户展示案例摘要并询问是否执行**，收到明确确认（如「确认执行 / 继续」）后才可进入步骤 4。
- 若用户未确认、拒绝或超时：终止流程并返回「已取消执行，测试案例已保存到 `<cases_json>`」。
- 在未确认前，**不得** 调用 `parallel_test_runner.py --prepare`、不得发起 `sessions_spawn`。

---

### 步骤 4：执行测试案例

**⚠️ 防止数据污染（关键）**：子 Agent **不得** 事先知晓预期结果。  
`parallel_test_runner.py --prepare` 已生成纯净任务描述，直接使用。

**4.1 生成执行计划**

```bash
python3 {baseDir}/scripts/parallel_test_runner.py <cases_json> --prepare [--trials 3]
```

从输出 JSON 的 `tasks` 数组中获取每个任务。每个 task 包含：
- `task_description`：只有用户请求，无测试意图（可直接传给 sessions_spawn）
- `evaluation_hint`：告知主 Agent 如何评判此案例
- `multi_trial` / `trial_count`：是否需要重复执行

**4.2 调用 sessions_spawn 执行**（Agent 直接发起）

对每个 task，调用 sessions_spawn。`--parallel` 为建议并发数，**若运行时不支持并发则顺序执行即可**，功能不受影响。

```python
# 调用示意（参数名称以当前 OpenClaw 文档/工具描述为准）
result = sessions_spawn(
    task    = task["task_description"],  # 纯净用户请求，无测试意图
    skills  = [str(skill_path)],         # 确保目标 Skill 在加载路径中
    timeout = timeout_seconds            # --timeout 参数值，默认 60
)
# 提取子 session 的实际输出
sub_output = result.get("output") or result.get("response") or str(result)
sub_session_id = result.get("session_id") or result.get("id") or result.get("sessionId")
```

**执行真实性门控（必须执行）：**
- 每个 case 必须先调用一次 `sessions_spawn`，拿到 `sub_output` 与 `sub_session_id` 后，才可记录结果。
- 若 `sessions_spawn` 不可用、超时或未返回 `sub_session_id`：该 case 只能记为 `error`，并在 `outcome` 写明原因，**不得** 伪造 `passed/failed`。
- 禁止“批量补写”结果：必须 `执行 1 条 -> 记录 1 条`，循环直至全部 case 完成或中止。

**4.3 评估结果并记录**

主 Agent 根据 `evaluation_hint` 和 `expected` 评判输出，再记录：

```bash
python3 {baseDir}/scripts/parallel_test_runner.py <cases_json> \
    --record <case_id> --status passed|failed|error \
    --outcome "实际输出摘要" --session-id "<sub_session_id>" [--trial 1]
```

> `--outcome` 与 `--session-id` 为必填，缺失时 `--record` 会失败（防止“空结果/虚假记录”）。

**评分器类型**：
- `"deterministic"`：检查具体特征（字段存在、正则匹配），精确判断
- `"llm_rubric"`（默认）：主 Agent 用语义理解判断质量

| 维度 | 评估要点 |
|------|---------|
| `hit_rate` | 输出/行为是否表明目标 Skill 被触发 |
| `agent_comprehension` | 结果是否符合预期（outcome，非 process）|
| `execution_success` | 任务完成；adversarial 被拒绝；idempotency 前后一致 |

> **hit_rate 判定补充**：子 session 输出通常不含"我用了哪个 Skill"的元信息，依据内容推断：
> - 预期 `"activate"` → 输出与目标 Skill 功能直接相关（如 weather-skill → 有天气数据返回）
> - 预期 `"not_activate"` → 输出是通用回复、"不支持"或其他 Skill 的响应（无目标 Skill 特征）
>
> 若案例失败原因不明，调用诊断工具：
> ```bash
> python3 {baseDir}/scripts/error_analyzer.py <skill_path>
> ```

**4.4 生成执行摘要**

```bash
python3 {baseDir}/scripts/parallel_test_runner.py <cases_json> --finalize
```

---

### 步骤 5：计算评分并生成报告

**各维度得分（0–100）：**

```
触发命中率    = (精确pass×0.4 + 模糊pass×0.4 + 负面pass×0.2) / 各类加权总数 × 100
Skill规范程度 = 步骤 2 的 spec_score
Agent理解度   = (outcome_check pass + format_check pass) / 总数 × 100
执行成功率    = (normal×0.4 + boundary×0.25 + error×0.20 + adversarial×0.10 + idempotency×0.05) / 加权总数 × 100

综合评分 = 触发命中率×0.25 + Skill规范程度×0.20 + Agent理解度×0.25 + 执行成功率×0.30
```

**特殊规则**：安全 `failed` → 综合归零；任意维度 < 40 → 评级上限 ⭐⭐⭐

**可靠性**（critical 案例多次试验统计）：
- `pass@k`：至少 1 次通过（能力）
- `pass^k`：全部通过（稳定性）

步骤 3 已将 `safety` 和 `spec_score` 写入 `<cases_json>`，`--finalize` 执行后，`<cases_json>` **即为**报告所需的 `<results_json>`，无需额外组装，直接传入：

```bash
python3 {baseDir}/scripts/report_builder.py <cases_json> [--eval-md <skill_path>]
```

`--eval-md` 会将评估摘要写入 `<skill_path>/EVAL.md`，方便随 Skill 代码版本管理。

---

## 评级与认证

| 综合评分 | 评级 | 认证状态 |
|---------|------|--------|
| 90–100 | ⭐⭐⭐⭐⭐ 优秀 | 🏆 Certified |
| 70–89 | ⭐⭐⭐⭐ 良好 | ✅ Verified |
| 40–69 | ⭐⭐⭐ 可接受 | 🔄 Beta |
| 0–39 | ⭐⭐ 需改进 | — |
| 安全失败 | ❌ 不合格 | — |

---

## 已知限制（Sharp Edges）

| 问题 | 严重程度 | 应对方案 |
|------|---------|---------|
| Agent 行为非确定性：同一测试不同 session 结果可能不同 | 高 | 使用 pass@3，不依赖单次结果 |
| **子 Agent 若事先知晓预期结果，测试可信度归零** | 🔴 高 | 严格执行：子 Agent 仅收用户输入，主 Agent 独立评估 |
| sessions_spawn 在某些环境下不可用 | 高 | 告知用户，降级为顺序执行 |
| 目标 Skill 无明确输出格式描述时，Agent理解度测试难以生成 | 中 | 目标 Skill 需在 SKILL.md 中声明预期输出/结果 |
| 规范程度（spec_score）基于静态分析，不反映运行时质量 | 低 | spec_score 权重仅 20% |
| 测试数据可能泄露给子 Agent 的训练上下文 | 中 | 测试案例不应包含真实用户数据 |

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENCLAW_AVAILABLE` | `false` | 设为 `true` 表示当前在 OpenClaw 运行时中，步骤 4 可调用 sessions_spawn |

## 参考文档

- [references/config.md](./references/config.md) — 配置说明与环境变量
- [references/test-cases.md](./references/test-cases.md) — 测试案例格式与维度说明
- [references/executors.md](./references/executors.md) — 多 Agent 并行执行架构
- [references/reviewers.md](./references/reviewers.md) — 评审器与评分体系详解
- [references/safety-checker.md](./references/safety-checker.md) — 安全检查规则说明
- [references/report-template.md](./references/report-template.md) — 报告模板格式
- [references/troubleshooting.md](./references/troubleshooting.md) — 常见问题排查
- [references/ci-cd.md](./references/ci-cd.md) — CI/CD 集成示例

**Related Skills**：`skill-evaluator`（terwox），`agent-evaluation`（rustyorb）
