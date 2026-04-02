# 执行架构

## 概述

skill-tester 使用 `parallel_test_runner.py`（TestCoordinator）配合 OpenClaw Agent 执行测试案例。**实际测试执行（sessions_spawn）由 Agent 发起**，本脚本只负责数据管理：执行计划生成、结果记录、统计汇总。

## 架构

```
TestCoordinator (parallel_test_runner.py)
├── prepare()          # 生成执行计划（纯净任务描述）
├── record()           # 记录单条案例结果（含 token 数据）
├── finalize()         # 汇总统计 + 早期终止检测
└── JSON 持久化        # 每次 record 自动保存
```

## 执行流程

### 1. 生成执行计划

```bash
python3 parallel_test_runner.py <cases_json> --prepare [--trials 3] [--dimension <dim>]
```

- 自动跳过非 `pending` 状态的案例（支持断点续跑）
- `--dimension` 切片：只返回指定维度的 pending 案例
- 输出纯净 `task_description`：只有用户请求，无测试意图
- 每个 task 包含 `evaluation_hint`，告知主 Agent 如何评判

### 2. Agent 执行

对每个 task，Agent 调用 `sessions_spawn`，等待子 Agent completion event 返回。

**执行真实性门控**：必须拿到子 Agent 的完整输出和 session_id 后才可记录。

**收到 completion event 后，Agent 必须：**

1. **提取原始输出**：从 `<<<BEGIN_UNTRUSTED_CHILD_RESULT>>>` 到 `<<<END_UNTRUSTED_CHILD_RESULT>>>` 之间的完整文本
2. **保存原始输出到临时文件**：`write /tmp/agent_output_{case_id}.txt`，内容为上述原文，不做任何修改、总结或缩写
3. **独立评估**：主 Agent 根据 `evaluation_hint` 和 `expected` 判断 passed/failed
4. **记录结果**：调用 `--record`，`--outcome` 写一句话评估摘要，`--agent-output-file` 指向临时文件

### 3. 记录结果（含 Token 采集 + 原始输出存证）

每条案例记录需要两类内容：

| 参数 | 内容 | 存储位置 |
|------|------|---------|
| `--outcome` | 主 Agent 的**一句话评估摘要** | test-cases JSON 的 `result.outcome` |
| `--agent-output` / `--agent-output-file` | 子 Agent 返回给用户的**完整原始输出** | `results/{batch_id}/{case_id}.json` |

#### ⚠️ `--agent-output` 必须是原始输出（强制）

`--agent-output` 的内容**必须是子 Agent 返回的完整原文**——即用户实际会看到的消息内容。

- ✅ **正确**：子 Agent completion event 中 `<<<BEGIN_UNTRUSTED_CHILD_RESULT>>>` 到 `<<<END_UNTRUSTED_CHILD_RESULT>>>` 之间的全部文本，原样保存，不做任何修改
- ❌ **错误**：主 Agent 自己写的摘要、总结、缩写、提炼

**为什么？** 这是测试存证，用于人工回溯评估。如果保存的是摘要而不是原文，就失去了存证价值——无法判断子 Agent 的实际表现。

#### 推荐做法：写入临时文件后传路径

子 Agent 的输出通常较长且含特殊字符，直接通过命令行 `--agent-output "..."` 传参容易出问题。推荐：

```bash
# 1. 主 Agent 将子 Agent 原始输出写入临时文件
write /tmp/agent_output_{case_id}.txt  ← 子 Agent 完整原文

# 2. 通过 --agent-output-file 传入（脚本读取后自动删除临时文件）
python3 parallel_test_runner.py <cases_json> \
    --record <case_id> --status passed \
    --outcome "一句话评估摘要" \
    --agent-output-file /tmp/agent_output_{case_id}.txt \
    --session-id "<id>" \
    --tokens-in <N> --tokens-out <N>
```

#### 完整命令参考

```bash
python3 parallel_test_runner.py <cases_json> \
    --record <case_id> --status passed|failed|error \
    --outcome "主 Agent 的一句话评估摘要" \
    --agent-output-file /tmp/agent_output.txt \
    --session-id "<id>" \
    --tokens-in <N> --tokens-out <N> [--trial 1]
```

- `--outcome`：主 Agent 对结果的评估摘要（如 "成功返回20个商品列表"）
- `--agent-output-file`：子 Agent 完整原始输出的临时文件路径（读取后自动删除）
- `--agent-output`：直接传入原始输出文本（仅适用于短输出）
- `--tokens-in` / `--tokens-out`：从子 Agent completion event 的 stats 中提取
- `--trial`：multi_trial 案例专用（从 1 开始），所有 trial 完成后自动聚合

#### 存证文件结构

原始输出保存在 `results/` 目录下，按测试批次分子目录：

```
.skill-tester/results/
  {skill_name}-{YYYYMMDD_HHMMSS}/     ← 批次目录（自动创建）
    hit_exact_0.json                    ← 单次试验
    exec_normal_0_trial1.json           ← multi-trial 第1次
    exec_normal_0_trial2.json           ← multi-trial 第2次
    ...
```

每个文件内容：
```json
{
  "case_id": "hit_exact_0",
  "session_id": "子 Agent 会话 ID",
  "tokens_in": 74000,
  "tokens_out": 3300,
  "agent_output": "子 Agent 返回的完整原始输出...",
  "recorded_at": "2026-04-02T12:01:23.456789"
}
```

### 4. 早期终止

`finalize()` 会检测早期终止条件：

- 最近连续 `EARLY_EXIT_THRESHOLD`（默认 3）个案例都是 failed/error
- 且 outcome 中包含相似根因关键词（如"未触发"、"超时"、"Skill未被激活"）
- 满足时 summary 中增加 `early_exit_recommended: true` 和 `early_exit_reason`

**Agent 在执行过程中也应检测**：如果连续 3 个案例因同一原因失败，停止执行，报告根因，建议修复后重试。

### 5. 断点续跑

`--prepare` 自动跳过已完成的案例。Agent 重入时：

1. 直接 `--prepare` 获取剩余 pending 任务
2. 继续执行和记录
3. 全部完成后 `--finalize`

无需手动管理状态——状态持久化在 cases JSON 文件中。

### 6. 汇总

```bash
python3 parallel_test_runner.py <cases_json> --finalize
```

输出 summary 包含：
- 常规统计：total / completed / passed / failed / pending / pass_rate
- Token 统计：total_tokens_in / total_tokens_out / avg_tokens_per_case
- 早期终止建议（如适用）

## 错误处理

| 错误类型 | 处理方式 |
|---------|--------|
| 超时 | 记为 `error`，outcome 写明"超时" |
| sessions_spawn 不可用 | 记为 `error`，不伪造结果 |
| 断言失败 | 记为 `failed`，记录预期 vs 实际 |

## 性能建议

| 场景 | 推荐配置 |
|------|--------|
| 快速验证 | `--timeout 60` |
| 标准测试 | `--timeout 120`（默认） |
| 有状态 Skill | 串行执行（按顺序逐个测试） |

## 分阶段执行（依赖 Skill）

对有外部依赖的 Skill，测试流程分三个阶段执行：Phase A（无依赖测试）→ Phase B（依赖配置门控）→ Phase C（有依赖测试）。

### 查看阶段状态

```bash
python3 parallel_test_runner.py <cases_json> --phase-status
```

### 按阶段获取任务

```bash
python3 parallel_test_runner.py <cases_json> --prepare --phase phase_a
python3 parallel_test_runner.py <cases_json> --prepare --phase phase_c
```

### 推进阶段

```bash
python3 parallel_test_runner.py <cases_json> --advance-phase
```

### 验证依赖

```bash
python3 parallel_test_runner.py <cases_json> --verify-dep ak
python3 parallel_test_runner.py <cases_json> --verify-all-deps
```

### 典型流程

```bash
# Phase A
python3 ptr.py cases.json --prepare --phase phase_a
# ... Agent 执行 + record ...
python3 ptr.py cases.json --advance-phase

# Phase B
python3 ptr.py cases.json --verify-all-deps
# ... 用户配置依赖 ...
python3 ptr.py cases.json --verify-dep ak
python3 ptr.py cases.json --advance-phase

# Phase C
python3 ptr.py cases.json --prepare --phase phase_c
# ... Agent 执行 + record ...
python3 ptr.py cases.json --advance-phase
python3 ptr.py cases.json --finalize
```
