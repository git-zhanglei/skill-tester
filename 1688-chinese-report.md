# Skill 测试报告: 1688-shopkeeper

**生成时间:** 2026-03-17 20:18:03
**总体评分:** 57.5/100
**评级建议:** ⭐⭐⭐ 可接受 - 需要改进

## 1. 执行摘要

该 skill 基本可用，但需要修复一些问题才能达到生产标准。

### 关键指标

| 指标 | 得分 | 状态 |
|------|------|------|
| 总体评分 | 57.5/100 | ⚠️ |
| 安全检测 | 未通过 | ❌ |
| 触发命中率 | 90.0% | ✅ |
| 任务成功率 | 83.3% | ✅ |


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

**得分:** 22.5/25

| 测试类型 | 总数 | 通过 | 通过率 |
|----------|------|------|--------|
| 总体 | 20 | 18 | 90.0% |

### 3.2 任务成功率 (权重: 30%)

**得分:** 25.0/30

| 测试类型 | 总数 | 通过 | 通过率 |
|----------|------|------|--------|
| 总体 | 6 | 5 | 83.3% |


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
| 1 | Exact trigger: 配置 | 触发命中率 | 精确匹配 | `配置` | activate | ✅ | 0.40s |
| 2 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.30s |
| 3 | Exact trigger: 用户话题 | 触发命中率 | 精确匹配 | `用户话题` | activate | ✅ | 0.42s |
| 4 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.17s |
| 5 | Exact trigger: 首页 | 触发命中率 | 精确匹配 | `首页` | activate | ❌ | 0.27s |
| 6 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.53s |
| 7 | Exact trigger: 其他 | 触发命中率 | 精确匹配 | `其他` | activate | ✅ | 0.43s |
| 8 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.41s |
| 9 | Exact trigger: 返回 | 触发命中率 | 精确匹配 | `返回` | activate | ✅ | 0.19s |
| 10 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.26s |
| 11 | Exact trigger: 商品或店铺存在多个候 | 触发命中率 | 精确匹配 | `商品或店铺存在多个候选` | activate | ✅ | 0.32s |
| 12 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.45s |
| 13 | Exact trigger: 执行前置 | 触发命中率 | 精确匹配 | `执行前置` | activate | ✅ | 0.51s |
| 14 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.46s |
| 15 | Exact trigger: 仅当写入目标不唯一 | 触发命中率 | 精确匹配 | `仅当写入目标不唯一` | activate | ❌ | 0.22s |
| 16 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.19s |
| 17 | Exact trigger: 素材审核 | 触发命中率 | 精确匹配 | `素材审核` | activate | ✅ | 0.51s |
| 18 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.49s |
| 19 | Exact trigger: 字段 | 触发命中率 | 精确匹配 | `字段` | activate | ✅ | 0.30s |
| 20 | Negative test: should not | 触发命中率 | 负面测试 | `completely unrelated` | not_acti | ✅ | 0.47s |
| 21 | Standard usage scenario | 任务成功率 | 正常场景 | `Test 1688-shopkeeper` | success | ❌ | 0.48s |
| 22 | Invalid input handling | 任务成功率 | 异常处理 | `Test 1688-shopkeeper` | error_ha | ✅ | 0.57s |
| 23 | Empty input boundary | 任务成功率 | 边界测试 | `Test 1688-shopkeeper` | handled | ✅ | 0.48s |
| 24 | 安全测试: 命令注入防护 | 任务成功率 | 命令注入防护 | `search --query "; rm` | error_ha | ✅ | 0.35s |
| 25 | 安全测试: 路径遍历防护 | 任务成功率 | 路径遍历防护 | `search --query "../.` | error_ha | ✅ | 0.54s |
| 26 | 安全测试: SQL注入防护 | 任务成功率 | SQL注入防护 | `search --query "' OR` | error_ha | ✅ | 0.41s |

**图例:** ✅ 通过 | ❌ 失败

### 5.2 失败测试详情

**Exact trigger: 首页
- 测试维度: 触发命中率
- 测试类型: 精确匹配
- 测试输入: `首页`
- 期望结果: activate
- 实际状态: 失败
- 执行耗时: 0.267s
- 错误信息: `Failed to handle: 首页`

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

**Exact trigger: 仅当写入目标不唯一
- 测试维度: 触发命中率
- 测试类型: 精确匹配
- 测试输入: `仅当写入目标不唯一`
- 期望结果: activate
- 实际状态: 失败
- 执行耗时: 0.219s
- 错误信息: `Failed to handle: 仅当写入目标不唯一`

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

**Standard usage scenario
- 测试维度: 任务成功率
- 测试类型: 正常场景
- 测试输入: `Test 1688-shopkeeper with standard input`
- 期望结果: success
- 实际状态: 失败
- 执行耗时: 0.481s
- 错误信息: `Failed to handle: Test 1688-shopkeeper with standard input`

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

1. **测试失败: Exact trigger: 首页**
   - 影响: 状态为 failed
   - 建议: 修复实现以处理: 首页

2. **测试失败: Exact trigger: 仅当写入目标不唯一**
   - 影响: 状态为 failed
   - 建议: 修复实现以处理: 仅当写入目标不唯一

3. **测试失败: Standard usage scenario**
   - 影响: 状态为 failed
   - 建议: 修复实现以处理: Test 1688-shopkeeper with standard input


## 7. 结论

该 skill **1688-shopkeeper** 基本可用，评分为 57.5/100。需要修复一些问题才能达到生产标准。


---

*报告由 Skill Certifier v1.0.0 生成*