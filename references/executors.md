# 测试执行器

## 概述

测试执行器在隔离环境中运行测试用例并收集结果。

## 架构

```
TestExecutor
├── ThreadPoolExecutor (并行代理)
│   ├── 代理 1: 测试用例 A
│   ├── 代理 2: 测试用例 B
│   ├── 代理 3: 测试用例 C
│   └── 代理 4: 测试用例 D
└── 结果收集器
```

## 执行流程

1. **准备环境**
   - 创建临时目录
   - 复制 skill 到沙箱
   - 安装依赖
   - 注入 API key

2. **生成子代理**
   - 使用 `sessions_spawn` 进行隔离
   - 每个代理运行一个测试用例
   - 超时保护

3. **收集结果**
   - 成功/失败状态
   - 输出捕获
   - 持续时间测量
   - 错误详情

4. **清理**
   - 终止子代理
   - 删除临时文件
   - 释放资源

## 子代理实现

```python
# 子代理执行伪代码
def execute_test_case(test_case, skill_path, env_vars):
    # 生成隔离会话
    session = sessions_spawn(
        task=f"""
        你正在隔离环境中测试一个 skill。
        
        Skill 位置: {skill_path}
        测试输入: {test_case['input']}
        预期: {test_case['expected']}
        
        步骤:
        1. 从 {skill_path}/SKILL.md 加载 skill
        2. 处理测试输入，就像用户说的那样
        3. 记录发生了什么:
           - skill 是否激活?
           - 它采取了什么操作?
           - 是否成功完成?
           - 有任何错误?
        
        输出 JSON:
        {{
            "activated": true/false,
            "actions": [...],
            "success": true/false,
            "error": "错误信息或 null",
            "output": "完整输出"
        }}
        """,
        timeout=test_case.get('timeout', 60)
    )
    
    return session.result
```

## 并行执行

### 好处
- 更快的测试完成
- 更好的资源利用
- 测试间隔离

### 考虑因素
- 资源限制（CPU、内存）
- API 速率限制
- 共享状态冲突

### 配置

```python
# 根据机器能力调整
parallel_degree = 4  # 默认
parallel_degree = 8  # 高端机器
parallel_degree = 2  # 低端机器
```

## 超时处理

```python
# 每个测试超时
timeout = 60  # 秒

# 优雅超时处理
try:
    result = future.result(timeout=timeout)
except TimeoutExpired:
    return {
        'status': 'timeout',
        'error': f'{timeout}秒后超时',
        'duration': timeout
    }
```

## 错误分类

| 错误类型 | 描述 | 操作 |
|------------|-------------|--------|
| 超时 | 测试耗时太长 | 标记优化 |
| 异常 | 未处理的错误 | Bug 报告 |
| 断言 | 预期 != 实际 | 测试失败 |
| 资源 | 内存/磁盘不足 | 降低并行度 |
| 网络 | API 调用失败 | 重试或跳过 |

## 结果格式

```json
{
  "test_case": {
    "dimension": "hit_rate",
    "type": "exact_match",
    "input": "测试skill"
  },
  "status": "passed|failed|timeout|error",
  "output": "捕获的输出",
  "error": null,
  "duration": 5.2,
  "returncode": 0
}
```

## 性能优化

1. **重用沙箱** 用于相同 skill
2. **缓存依赖** 在测试间
3. **延迟加载** skill 资源
4. **批量相似测试** 减少开销

## 调试失败的测试

```bash
# 详细输出运行
测试skill ./my-skill --verbose

# 运行单个测试用例
测试skill ./my-skill --test-case "精确触发"

# 保留沙箱用于检查
测试skill ./my-skill --no-cleanup
```