# 测试案例：格式与维度说明

## 概述

skill-tester 的测试案例覆盖 4 个维度，保存为 JSON 文件，支持复用与断点续测。最大案例数默认 30（上限）。

### 骨架模式生成

```bash
python3 scripts/smart_test_generator.py <skill_path> --skeleton
```

生成覆盖四维度的骨架案例（含 `dimension`、`type`、`hints`，但 `input` 和 `expected` 为空）。Agent 需读取目标 SKILL.md 后，基于自身理解为每个骨架填充 `input` 和 `expected`（参考 `hints` 但不受其限制），可增删案例。

## 4 个测试维度

### 维度 1：触发命中率（hit_rate）　→ 默认 phase_a

验证 Skill 的触发词是否能正确激活/不激活。

| 测试类型 | 说明 | 预期结果 | 占比 |
|---------|------|--------|------|
| `exact_match` | 使用 SKILL.md 中声明的精确触发词 | `activate` | 40% |
| `fuzzy_match` | 触发词的同义词/衍生表达（口语化、礼貌前后缀） | `activate` | 40% |
| `negative_test` | 非同义、完全无关的输入（用于验证不误触发） | `not_activate` | 20% |

**示例：**
```json
{
  "id": "hit_exact_0",
  "dimension": "hit_rate",
  "type": "exact_match",
  "input": "测试skill ~/skills/weather/",
  "expected": "activate",
  "description": "使用精确触发词"
}
```

```json
{
  "id": "hit_fuzzy_1",
  "dimension": "hit_rate",
  "type": "fuzzy_match",
  "input": "帮我检测一下这个skill的质量",
  "expected": "activate",
  "description": "语义相近的模糊表述"
}
```

```json
{
  "id": "hit_negative_0",
  "dimension": "hit_rate",
  "type": "negative_test",
  "input": "帮我写一首诗",
  "expected": "not_activate",
  "description": "完全无关的输入，不应触发"
}
```

---

### 维度 2：Skill规范程度（spec_compliance）

静态分析 SKILL.md 是否符合 OpenClaw 规范，由 `spec_checker.py` 自动执行（不需要 Agent 运行）。

共 **14 项检查**，分 6 类：

| 类别 | 检查项（示例） |
|------|------------|
| structure | SKILL.md 存在、frontmatter 完整、name 与目录名一致、无冗余文件、Guardrails 按需建议 |
| trigger | description 长度≥20字符、description 含触发上下文短语 |
| documentation | Token 开销（>400行=FAIL）、Workflow 按需建议、references 均已链接 |
| scripts | Python 语法正确、仅使用标准库或本地模块 |
| security | 环境变量均已文档化 |
| agent_specific | 具备机器可读输出信号（--json / exit code） |

评分公式：`pass=2分 / warn=1分 / fail=0分`，归一到 0-100。

```bash
# 运行规范检查
python3 scripts/spec_checker.py <skill_path> --json
```

**注意：** 规范程度得分直接来自 `summary.spec_score`，不生成动态测试案例；Guardrails/Workflow 仅在判定「该 Skill 需要」时，缺失才给出建议。

---

### 维度 3：Agent理解度（agent_comprehension）　→ 默认 phase_c

验证 Agent 对目标 Skill 的理解——**聚焦最终结果（outcome），不评估执行过程**。

| 测试类型 | 说明 | 评估方式 |
|---------|------|--------|
| `outcome_check` | 实际产物是否符合 Skill 声明的预期结果 | 主 Agent 对比输出与 expected |
| `format_check`  | 输出格式是否符合 Skill 声明的格式规范（若有）| 确定性检查或语义判断 |

> **为什么不检查步骤？** 步骤监测会使测试与实现强耦合，只要结果正确，步骤可以不同。
> 这与 skillgrade/mgechev 的"结果导向评分"原则一致。

**示例：**
```json
{
  "id": "comp_outcome_0",
  "dimension": "agent_comprehension",
  "type": "outcome_check",
  "grader_type": "llm_rubric",
  "input": "测试skill ~/skills/weather/",
  "expected": "生成包含综合评分和各维度得分的认证报告",
  "description": "验证最终产物（报告）是否符合 Skill 声明的结果"
}
```

```json
{
  "id": "comp_format_0",
  "dimension": "agent_comprehension",
  "type": "format_check",
  "grader_type": "deterministic",
  "input": "测试skill ~/skills/weather/ --output-json",
  "expected": "输出中包含 overall_score、hit_rate、execution_success 字段",
  "description": "验证 JSON 输出格式符合声明规范"
}
```

---

### 维度 4：执行成功率（execution_success）　→ 按类型分 phase

真实执行多种场景，验证 Skill 能否成功完成任务。

| 测试类型 | 说明 | 权重 | 通过目标 | 默认 Phase |
|---------|------|------|--------|-----------|
| `normal_path` | 标准输入，Skill 应完整执行 | 40% | ≥ 90% | phase_c |
| `boundary_case` | 边界输入（空路径、超长输入等） | 25% | ≥ 70% | phase_a |
| `error_handling` | 异常输入（无效路径、权限不足等） | 20% | ≥ 60% | 视具体场景 |
| `adversarial` | 歧义/越权/空输入，预期拒绝并说明 | 10% | ≥ 60% | phase_a |
| `idempotency_check` | 执行两次相同操作，验证结果一致 | 5% | ≥ 80% | phase_c |

> `idempotency_check` 补充：对实时数据类 Skill（天气/股价等），改为验证**输出格式**一致而非数据值一致。

**示例：**
```json
{
  "id": "exec_normal_0",
  "dimension": "execution_success",
  "type": "normal_path",
  "input": "测试skill ~/skills/weather/ --yes",
  "expected": {
    "status": "completed",
    "report_generated": true
  },
  "description": "标准执行路径"
}
```

```json
{
  "id": "exec_boundary_0",
  "dimension": "execution_success",
  "type": "boundary_case",
  "input": "测试skill ./nonexistent-skill/",
  "expected": {
    "status": "error",
    "error_handled": true,
    "error_message_contains": "不存在"
  },
  "description": "目标 Skill 路径不存在时的处理"
}
```

---

## 测试案例集 JSON 格式（完整）

```json
{
  "version": "3.0",
  "skill_name": "my-skill",
  "skill_path": "~/skills/my-skill/",
  "generated_at": "2026-03-23T10:00:00",
  "total": 30,
  "dependencies": {
    "items": [
      {
        "id": "ak",
        "name": "API_KEY",
        "type": "env_var",
        "description": "API Access Key",
        "configure_hint": "export API_KEY=xxx",
        "verify_command": "echo $API_KEY",
        "verify_expect": "xxx",
        "status": "unverified"
      }
    ],
    "all_verified": false
  },
  "phases": {
    "current": "phase_a",
    "phase_a": {"status": "pending", "description": "无依赖测试"},
    "phase_b": {"status": "blocked", "description": "依赖配置门控", "blocked_by": "phase_a"},
    "phase_c": {"status": "blocked", "description": "有依赖测试", "blocked_by": "phase_b"}
  },
  "cases": [
    {
      "id": "hit_exact_0",
      "dimension": "hit_rate",
      "type": "exact_match",
      "input": "测试skill ~/skills/my-skill/",
      "expected": "activate",
      "description": "精确触发词测试",
      "model": "auto",
      "weight": 1.0,
      "status": "pending",
      "phase": "phase_a",
      "dependency_requires": [],
      "result": null,
      "completed_at": null
    },
    {
      "id": "exec_normal_0",
      "dimension": "execution_success",
      "type": "normal_path",
      "input": "使用 my-skill 执行标准操作",
      "expected": "任务完成且输出符合预期",
      "description": "标准输入执行路径",
      "weight": 1.1,
      "status": "pending",
      "phase": "phase_c",
      "dependency_requires": ["ak"],
      "result": null,
      "completed_at": null
    }
  ],
  "notes": "result 对象在完成后包含 tokens_in 和 tokens_out 字段，记录该案例的 token 消耗",
  "execution": {
    "status": "pending"
  }
}
```

## 测试案例状态流转

```
pending → running → completed (passed / failed / timeout / error)
```

| 状态 | 说明 |
|------|------|
| `pending` | 等待执行 |
| `running` | 正在执行中 |
| `completed` | 执行完成（查看 result.status 获取结果） |

`result.status` 取值：
- `passed`：测试通过
- `failed`：测试失败（预期与实际不符）
- `timeout`：执行超时
- `error`：执行出现异常

