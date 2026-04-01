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

### 2. Agent 串行执行

对每个 task，Agent 调用 `sessions_spawn`：

```python
result = sessions_spawn(
    task    = task["task_description"],
    timeout = 120  # 默认超时 120 秒
)
sub_output = result.get("output") or str(result)
sub_session_id = result.get("session_id") or result.get("id") or ""
```

**执行真实性门控**：必须拿到 `sub_output` 和 `sub_session_id` 后才可记录。

### 3. 记录结果（含 Token 采集）

```bash
python3 parallel_test_runner.py <cases_json> \
    --record <case_id> --status passed|failed|error \
    --outcome "输出摘要" --session-id "<id>" \
    --tokens-in <N> --tokens-out <N> [--trial 1]

# 或从文件读取 outcome（适合长输出）
python3 parallel_test_runner.py cases.json --record hit_exact_0 --status passed \
    --outcome-file /tmp/outcome.txt --session-id "session-123"
```

- `--tokens-in` / `--tokens-out`：从子 Agent completion event 的 stats 中提取
- Token 数据保存到每条 case 的 result 中，finalize 时汇总统计
- `--trial`：multi_trial 案例专用（从 1 开始），所有 trial 完成后自动聚合

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
