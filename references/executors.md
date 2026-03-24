# 多 Agent 并行执行器

## 概述

skill-tester 使用多 Agent 并行执行策略，每个测试案例在独立隔离会话中运行，支持多模型分发。

## 架构

```
ParallelTestRunner
├── ModelDetector          # 检测 OpenClaw 已配置的模型
├── TaskDistributor        # 测试案例分发器
│   ├── balanced           # 均匀分配
│   ├── round-robin        # 轮询分配
│   └── dimension-based    # 按维度分配
├── ThreadPoolExecutor     # 线程池（并行度可配置）
│   ├── Agent-1 → Session-A (model-x)
│   ├── Agent-2 → Session-B (model-y)
│   ├── Agent-3 → Session-C (model-x)
│   └── Agent-4 → Session-D (model-z)
└── ResultCollector        # 结果收集与持久化
```

## 阶段 2：测试案例生成（Agent 泛化）

测试案例不是硬编码的，而是调度 Agent 对 SKILL.md 进行深度解析后泛化生成的。

```python
# 测试案例生成伪代码
def generate_test_cases(skill_path: str) -> List[TestCase]:
    skill_content = read_skill_md(skill_path)
    
    # 调度 Agent 泛化生成
    generator_session = sessions_spawn(
        task=f"""
        你是一个 OpenClaw Skill 测试专家。请分析以下 SKILL.md，生成覆盖 4 个测试维度的测试案例。
        
        SKILL.md 内容：
        {skill_content}
        
        请生成以下维度的测试案例（JSON 格式）：
        
        1. 触发命中率（hit_rate）：
           - 精确触发词（exact_match）：直接使用 SKILL.md 中声明的触发词
           - 模糊变体（fuzzy_match）：触发词同义词/衍生词（如口语化、礼貌前后缀），至少 3 个
           - 负面测试（negative_test）：非同义、无关输入，不应触发 Skill，至少 2 个
        
        2. Agent理解度（agent_comprehension）：
           - 结果检验（outcome_check）：验证最终产物是否满足 Skill 声明目标
           - 格式检验（format_check）：验证输出结构/字段是否符合 Skill 规范
        
        3. 执行成功率（execution_success）：
           - 正常路径（normal_path）：标准输入
           - 边界条件（boundary_case）：空输入、路径不存在、极端参数
           - 异常处理（error_handling）：权限不足、格式错误等
        
        注意：Skill规范程度（spec_compliance）由静态评审器处理，无需生成动态测试案例。
        
        以 JSON 数组格式输出测试案例，每个案例包含：id, dimension, type, input, expected, description
        """,
        timeout=120
    )
    
    return parse_test_cases(generator_session.result)
```

## 阶段 3：并行执行

### 执行流程

1. **检测可用模型** — 查询 OpenClaw 配置，获取已配置的模型列表
2. **分发任务** — 按选定策略将测试案例分配给不同 Agent/模型
3. **并行执行** — 使用线程池创建独立会话执行每个测试案例
4. **收集结果** — 实时更新测试案例状态，定期持久化到 JSON 文件

### 单个测试案例执行

```python
# 子 Agent 执行伪代码
def execute_test_case(test_case: dict, skill_path: str, model: str = "auto") -> dict:
    session_config = {}
    if model != "auto":
        session_config["model"] = model
    
    session = sessions_spawn(
        task=f"""
        你正在为 Skill 测试执行一个独立的测试案例。请严格按照以下信息执行。
        
        目标 Skill 路径：{skill_path}
        测试维度：{test_case['dimension']}
        测试类型：{test_case['type']}
        测试输入：{test_case['input']}
        预期结果：{test_case['expected']}
        测试描述：{test_case['description']}
        
        执行步骤：
        1. 加载并理解 {skill_path}/SKILL.md
        2. 模拟用户输入：{test_case['input']}
        3. 观察 Skill 的激活状态和执行行为
        4. 对照预期结果评估是否通过
        
        以 JSON 格式输出结果：
        {{
            "status": "passed/failed/error",
            "activated": true/false,
            "steps_observed": [...],
            "tools_called": [...],
            "output_summary": "...",
            "actual_vs_expected": "...",
            "failure_reason": null
        }}
        """,
        timeout=test_case.get('timeout', 60),
        **session_config
    )
    
    return {
        "status": parse_status(session.result),
        "output": session.result,
        "duration": session.duration,
        "model_used": model
    }
```

### 多模型分发策略

#### balanced（默认）

均匀分配测试案例到各模型：
```
案例 1-5   → model-a
案例 6-10  → model-b
案例 11-15 → model-c
案例 16-20 → model-a（循环）
```

#### round-robin

每个案例轮询换模型，用于对比模型一致性：
```
案例 1 → model-a
案例 2 → model-b
案例 3 → model-c
案例 4 → model-a
...
```

#### dimension-based

按测试维度分配到不同模型，适合专项能力对比：
```
hit_rate          → model-a（擅长指令理解）
agent_comprehension → model-b（擅长推理）
execution_success → model-c（通用模型）
```

## 执行隔离机制

每个子 Agent 在完全独立的会话中运行：
- 独立的会话上下文（无共享历史）
- 独立的文件系统命名空间（沙箱）
- 独立的环境变量
- 超时保护（防止单个测试阻塞整体）

## 进度追踪与持久化

每完成 5 个测试案例自动保存到 JSON 文件，防止执行中断丢失结果：

```python
# 进度更新示例
def update_progress(test_cases_file: str, case_id: str, result: dict):
    data = load_json(test_cases_file)
    case = find_case(data['cases'], case_id)
    case['status'] = 'completed'
    case['result'] = result
    case['completed_at'] = datetime.now().isoformat()
    
    data['execution']['progress']['completed'] += 1
    if result['status'] == 'passed':
        data['execution']['progress']['passed'] += 1
    else:
        data['execution']['progress']['failed'] += 1
    
    save_json(test_cases_file, data)
```

## 错误处理

| 错误类型 | 处理方式 |
|---------|--------|
| 超时（timeout） | 标记为 timeout，继续执行其他案例 |
| 会话异常（error） | 记录错误详情，标记为 error |
| 断言失败（failed） | 记录预期 vs 实际，标记为 failed |
| 资源不足 | 降低并行度重试 |

## 结果格式

```json
{
  "id": "exec_normal_0",
  "dimension": "execution_success",
  "type": "normal_path",
  "status": "completed",
  "result": {
    "status": "passed",
    "activated": true,
    "steps_observed": ["安全检查", "测试案例生成", "执行", "报告"],
    "tools_called": ["sessions_spawn", "write_file"],
    "output_summary": "生成了包含 20 个测试案例的认证报告",
    "actual_vs_expected": "符合预期",
    "failure_reason": null
  },
  "model_used": "model-a",
  "duration": 8.3,
  "completed_at": "2026-03-23T10:05:30"
}
```

## 性能调优建议

| 场景 | 推荐配置 |
|------|--------|
| 快速验证 | `--parallel 2 --timeout 30` |
| 标准测试 | `--parallel 4 --timeout 60`（默认） |
| 高并发 | `--parallel 8 --timeout 90` |
| 有状态 Skill（如修改配置文件） | `--parallel 1`（串行） |
| 多模型对比 | `--multi-model --parallel 4` |
