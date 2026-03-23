# 测试用例指南

## 概述

测试用例基于 SKILL.md 分析自动生成，但你可以自定义以获得更好的覆盖率。

## 测试用例格式

```json
{
  "dimension": "hit_rate|success_rate|branch_coverage|tool_accuracy",
  "type": "exact_match|fuzzy_match|negative|normal|exception|boundary",
  "input": "测试输入",
  "expected": "预期结果",
  "description": "人类可读的描述",
  "weight": 1.0
}
```

## 维度

### 1. 命中率测试

测试触发词准确度。

**精确匹配:**
```json
{
  "dimension": "hit_rate",
  "type": "exact_match",
  "input": "测试skill",
  "expected": "activate",
  "description": "精确触发词"
}
```

**模糊匹配:**
```json
{
  "dimension": "hit_rate",
  "type": "fuzzy_match",
  "input": "帮我测试一下skill",
  "expected": "activate",
  "description": "带上下文的触发"
}
```

**负面测试:**
```json
{
  "dimension": "hit_rate",
  "type": "negative",
  "input": "今天天气怎么样",
  "expected": "not_activate",
  "description": "不应激活"
}
```

### 2. 成功率测试

测试任务执行成功。

**正常路径:**
```json
{
  "dimension": "success_rate",
  "type": "normal",
  "input": "测试skill ./my-skill/",
  "expected": "success",
  "description": "标准用法"
}
```

**异常处理:**
```json
{
  "dimension": "success_rate",
  "type": "exception",
  "input": "测试skill /nonexistent/path/",
  "expected": "error_handled",
  "description": "处理缺失的 skill"
}
```

**边界情况:**
```json
{
  "dimension": "success_rate",
  "type": "boundary",
  "input": "测试skill ./my-skill/ --parallel 100",
  "expected": "success_or_warning",
  "description": "高并行度"
}
```

### 3. 分支覆盖率测试

测试代码路径覆盖。

```json
{
  "dimension": "branch_coverage",
  "type": "condition",
  "input": "使用 api_key 测试",
  "expected": "api_branch_executed",
  "description": "测试 API key 分支"
}
```

### 4. 工具准确度测试

测试工具选择和参数。

```json
{
  "dimension": "tool_accuracy",
  "type": "tool_selection",
  "input": "测试skill ./my-skill/",
  "expected": "sessions_spawn",
  "description": "选择正确的工具"
}
```

## 自定义测试用例文件

创建 `~/.skill-certifier/custom-tests.yaml`:

```yaml
test_suites:
  my-skill:
    - dimension: hit_rate
      type: exact_match
      input: "我的自定义触发词"
      expected: activate
      description: "我的 skill 的自定义触发词"
    
    - dimension: success_rate
      type: normal
      input: "测试skill ./my-skill/ --custom-flag"
      expected: success
      description: "测试自定义标志"
```

## 测试用例优先级

1. 自动生成的用例（基础覆盖）
2. 文件中的自定义用例（领域特定）
3. 用户提供的用例（临时测试）

## 最佳实践

1. **覆盖边界情况**: 空输入、超长输入、特殊字符
2. **测试负面情况**: 确保 skill 不会错误激活
3. **包含真实示例**: 匹配实际用户使用模式
4. **变化测试权重**: 关键路径应有更高权重
5. **定期更新**: 发现 bug 时添加新用例