# Skill 测试报告: 1688-shopkeeper

**生成时间:** 2026-03-17 21:01:01
**总体评分:** 53.8/100
**评级建议:** ⭐⭐⭐ 可接受 - 需要改进

## 1. 执行摘要

该 skill 基本可用，但需要修复一些问题才能达到生产标准。

### 关键指标

| 指标 | 得分 | 状态 |
|------|------|------|
| 总体评分 | 53.8/100 | ⚠️ |
| 安全检测 | 未通过 | ❌ |
| 触发命中率 | 95.0% | ✅ |
| 任务成功率 | 66.7% | ⚠️ |


## 2. 安全预检

❌ **未通过** - 发现安全问题

### ⚠️ 警告 (14个)

- [references/capabilities/search.md] Long number (potential ID): 991122553819
- [references/capabilities/search.md] Long number (potential ID): 991122553819
- [references/capabilities/publish.md] Long number (potential ID): 991122553819
- [references/capabilities/publish.md] Long number (potential ID): 894138137003
- [scripts/_http.py] HTTP POST (potential exfiltration): requests\.post\s*\(
- [.git/logs/HEAD] Email address: zhanglei@zhangleideMacBook-Pro.local
- [.git/logs/HEAD] Long number (potential ID): 0000000000000000000000000000000000000000
- [.git/logs/HEAD] Long number (potential ID): 1773634401
- [.git/logs/refs/heads/v1.0.1] Email address: zhanglei@zhangleideMacBook-Pro.local
- [.git/logs/refs/heads/v1.0.1] Long number (potential ID): 0000000000000000000000000000000000000000
- ... 还有 4 个警告


## 3. 量化指标

### 3.1 触发命中率 (权重: 25%)

**得分:** 23.8/25

| 测试类型 | 总数 | 通过 | 通过率 |
|----------|------|------|--------|
| 总体 | 20 | 19 | 95.0% |

### 3.2 任务成功率 (权重: 30%)

**得分:** 20.0/30

| 测试类型 | 总数 | 通过 | 通过率 |
|----------|------|------|--------|
| 总体 | 6 | 4 | 66.7% |


## 4. 质量评估

### 4.1 结构评审

** verdict:** ✅ Good
**得分:** 85/100

**发现问题:**
- SKILL.md is 84 lines (consider splitting to references/)
- Redundant file: README.md
- No code examples found

**改进建议:**
- Consider moving detailed content to references/
- Remove README.md - skills should not have auxiliary documentation
- Add code examples for clarity

### 4.2 实用性评审

** verdict:** ✅ Good
**得分:** 85/100

**发现问题:**
- Description is too short (1 chars, recommended > 50)

**改进建议:**
- Expand description to explain what the skill does

### 4.3 领域评审

** verdict:** ✅ Good
**得分:** 85/100

**发现问题:**
- No specific tools referenced
- API usage without authentication guidance

**改进建议:**
- Mention specific tools/APIs used
- Add authentication instructions


## 5. 测试详情

### 5.1 所有测试用例

| 序号 | 测试描述 | 维度 | 类型 | 输入 | 期望 | 状态 | 耗时 |
|------|----------|------|------|------|------|------|------|
| 1 | Exact trigger: 先完整阅读 | 触发命中率 | 精确匹配 | `先完整阅读` | activate | ✅ | 0.53s |
| 2 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.15s |
| 3 | Exact trigger: 安全声明 | 触发命中率 | 精确匹配 | `安全声明` | activate | ✅ | 0.52s |
| 4 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.36s |
| 5 | Exact trigger: 根据用户意图 | 触发命中率 | 精确匹配 | `根据用户意图` | activate | ✅ | 0.37s |
| 6 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.33s |
| 7 | Exact trigger: 加价倍率 | 触发命中率 | 精确匹配 | `加价倍率` | activate | ✅ | 0.24s |
| 8 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.42s |
| 9 | Exact trigger: 仅当写入目标不唯一 | 触发命中率 | 精确匹配 | `仅当写入目标不唯一` | activate | ✅ | 0.38s |
| 10 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ❌ | 0.21s |
| 11 | Exact trigger: 行为 | 触发命中率 | 精确匹配 | `行为` | activate | ✅ | 0.29s |
| 12 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.49s |
| 13 | Exact trigger: 加载文件 | 触发命中率 | 精确匹配 | `加载文件` | activate | ✅ | 0.27s |
| 14 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.55s |
| 15 | Exact trigger: 运费险 | 触发命中率 | 精确匹配 | `运费险` | activate | ✅ | 0.34s |
| 16 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.23s |
| 17 | Exact trigger: 进入页面获取 | 触发命中率 | 精确匹配 | `进入页面获取` | activate | ✅ | 0.50s |
| 18 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.45s |
| 19 | Exact trigger: 无需每次先执行 | 触发命中率 | 精确匹配 | `无需每次先执行` | activate | ✅ | 0.50s |
| 20 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.28s |
| 21 | Standard usage scenario | 任务成功率 | 正常场景 | `Test 1688-shopkeeper` | success | ✅ | 0.29s |
| 22 | Invalid input handling | 任务成功率 | 异常处理 | `Test 1688-shopkeeper` | error_ha | ❌ | 0.21s |
| 23 | Empty input boundary | 任务成功率 | 边界测试 | `Test 1688-shopkeeper` | handled | ❌ | 0.18s |
| 24 | 安全测试: 命令注入防护 | 任务成功率 | 命令注入防护 | `search --query "; rm` | error_ha | ✅ | 0.32s |
| 25 | 安全测试: 路径遍历防护 | 任务成功率 | 路径遍历防护 | `search --query "../.` | error_ha | ✅ | 0.35s |
| 26 | 安全测试: SQL注入防护 | 任务成功率 | SQL注入防护 | `search --query "' OR` | error_ha | ✅ | 0.31s |

**图例:** ✅ 通过 | ❌ 失败

### 5.2 失败测试详情

**Negative test: should not activate
- 测试维度: 触发命中率
- 测试类型: 负面测试
- 测试输入: `completely unrelated query about 仅当写入目标不唯一`
- 期望结果: not_activate
- 实际状态: 失败
- 执行耗时: 0.212s
- 错误信息: `Failed to handle: completely unrelated query about 仅当写入目标不唯一`

**错误分析:**
- 错误类型: 未知错误
- 严重程度: 中
- 处理建议: 查看详细错误信息

**修复步骤:**
  1. 检查错误日志
  2. 查看 SKILL.md 文档
  3. 在测试环境复现问题
  4. 联系 skill 维护者
- 参考文档: references/common/error-handling.md

**Invalid input handling
- 测试维度: 任务成功率
- 测试类型: 异常处理
- 测试输入: `Test 1688-shopkeeper with invalid path`
- 期望结果: error_handled
- 实际状态: 失败
- 执行耗时: 0.206s
- 错误信息: `Failed to handle: Test 1688-shopkeeper with invalid path`

**错误分析:**
- 错误类型: 未知错误
- 严重程度: 中
- 处理建议: 查看详细错误信息

**修复步骤:**
  1. 检查错误日志
  2. 查看 SKILL.md 文档
  3. 在测试环境复现问题
  4. 联系 skill 维护者
- 参考文档: references/common/error-handling.md

**Empty input boundary
- 测试维度: 任务成功率
- 测试类型: 边界测试
- 测试输入: `Test 1688-shopkeeper with empty input`
- 期望结果: handled
- 实际状态: 失败
- 执行耗时: 0.177s
- 错误信息: `Failed to handle: Test 1688-shopkeeper with empty input`

**错误分析:**
- 错误类型: 未知错误
- 严重程度: 中
- 处理建议: 查看详细错误信息

**修复步骤:**
  1. 检查错误日志
  2. 查看 SKILL.md 文档
  3. 在测试环境复现问题
  4. 联系 skill 维护者
- 参考文档: references/common/error-handling.md


## 6. 优化建议

### 高优先级

1. **测试失败: Negative test: should not activate**
   - 影响: 状态为 failed
   - 建议: 修复实现以处理: completely unrelated query about 仅当写入目标不唯一

2. **测试失败: Invalid input handling**
   - 影响: 状态为 failed
   - 建议: 修复实现以处理: Test 1688-shopkeeper with invalid path

3. **测试失败: Empty input boundary**
   - 影响: 状态为 failed
   - 建议: 修复实现以处理: Test 1688-shopkeeper with empty input


## 7. 结论

该 skill **1688-shopkeeper** 基本可用，评分为 53.8/100。需要修复一些问题才能达到生产标准。


---

*报告由 Skill Certifier v1.0.0 生成*