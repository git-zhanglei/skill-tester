# 测试案例：格式与维度说明

## 概述

skill-tester 的测试案例覆盖 4 个维度。案例由 Agent 泛化生成，保存为 JSON 文件，支持复用与断点续测。

## 4 个测试维度

### 维度 1：触发命中率（hit_rate）

验证 Skill 的触发词是否能正确激活/不激活。

| 测试类型 | 说明 | 预期结果 | 占比 |
|---------|------|--------|------|
| `exact_match` | 使用 SKILL.md 中声明的精确触发词 | `activate` | 40% |
| `fuzzy_match` | 语义相近的不同表述 | `activate` | 40% |
| `negative_test` | 完全无关的输入 | `not_activate` | 20% |

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
| structure | SKILL.md 存在、frontmatter 完整、name 与目录名一致、无冗余文件、有 Guardrails |
| trigger | description 长度≥20字符、description 含触发上下文短语 |
| documentation | Token 开销（>400行=FAIL）、有 Workflow 章节、references 均已链接 |
| scripts | Python 语法正确、仅使用标准库或本地模块 |
| security | 环境变量均已文档化 |
| agent_specific | 具备机器可读输出信号（--json / exit code） |

评分公式：`pass=2分 / warn=1分 / fail=0分`，归一到 0-100。

```bash
# 运行规范检查
python3 scripts/spec_checker.py <skill_path> --json
```

**注意：** 规范程度得分直接来自 `summary.spec_score`，不生成动态测试案例。

---

### 维度 3：Agent理解度（agent_comprehension）

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

### 维度 4：执行成功率（execution_success）

真实执行多种场景，验证 Skill 能否成功完成任务。

| 测试类型 | 说明 | 通过目标 |
|---------|------|--------|
| `normal_path` | 标准输入，Skill 应完整执行 | ≥ 90% |
| `boundary_case` | 边界输入（空路径、超长输入等） | ≥ 70% |
| `error_handling` | 异常输入（无效路径、权限不足等） | ≥ 60% |

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
  "total": 20,
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
      "result": null,
      "completed_at": null
    }
  ],
  "execution": {
    "status": "pending",
    "parallel_degree": 4,
    "multi_model": false,
    "models_used": [],
    "progress": {
      "total": 20,
      "completed": 0,
      "passed": 0,
      "failed": 0,
      "timeout": 0
    }
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

## 自定义测试案例

创建 `custom-tests.yaml` 文件，添加自定义测试：

```yaml
test_cases:
  - id: custom_001
    dimension: execution_success
    type: normal_path
    input: "测试skill ~/skills/my-skill/ --yes --output-json"
    expected:
      status: "completed"
      report_generated: true
    description: "我的特殊场景测试"
    weight: 1.5

  - id: custom_002
    dimension: hit_rate
    type: fuzzy_match
    input: "帮我看看这个skill好不好用"
    expected: "activate"
    description: "口语化触发词测试"
```

运行时加载：

```bash
测试skill ~/skills/my-skill/ --custom-tests ./custom-tests.yaml
```
