# Skill Evaluation Report: 1688-shopkeeper

**Generated:** 2026-03-17 20:03:59
**Overall Score:** 47.5/100
**Recommendation:** ⭐⭐⭐ Acceptable - Improvements needed

## 1. Executive Summary

This skill has acceptable quality but requires attention before production use. Several areas need improvement, particularly in test coverage and error handling.

### Key Metrics

| Metric | Score | Status |
|--------|-------|--------|
| Overall | 47.5/100 | ⚠️ |
| Safety | ✅ Pass | PASSED |
| Trigger Hit Rate | 90.0% | ✅ |
| Task Success Rate | 50.0% | ⚠️ |

## 2. Safety Pre-screen

### ⚠️ Warnings

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
- [.git/logs/refs/heads/v1.0.1] Long number (potential ID): 1773634401
- [.git/logs/refs/remotes/origin/HEAD] Email address: zhanglei@zhangleideMacBook-Pro.local
- [.git/logs/refs/remotes/origin/HEAD] Long number (potential ID): 0000000000000000000000000000000000000000
- [.git/logs/refs/remotes/origin/HEAD] Long number (potential ID): 1773634401

### Checked Files

- README.md
- SKILL.md
- references/capabilities/search.md
- references/capabilities/publish.md
- references/capabilities/configure.md
- references/capabilities/shops.md
- references/faq/platform-selection.md
- references/faq/new-store.md
- references/faq/base.md
- references/faq/product-selection.md
- references/faq/content-compliance.md
- references/faq/after-sales.md
- references/faq/listing-template.md
- references/faq/fulfillment.md
- references/common/data-contracts.md
- references/common/error-handling.md
- cli.py
- scripts/_output.py
- scripts/_errors.py
- scripts/_http.py
- ... and 17 more files

## 3. Quantitative Metrics

### 3.1 Trigger Hit Rate (Weight: 25%)

**Score:** 22.5/25

| Test Type | Total | Passed | Rate |
|-----------|-------|--------|------|
| Overall | 20 | 18 | 90.0% |

### 3.2 Task Success Rate (Weight: 30%)

**Score:** 15.0/30

| Test Type | Total | Passed | Rate |
|-----------|-------|--------|------|
| Overall | 6 | 3 | 50.0% |


## 4. Qualitative Assessment

### 4.1 Structure Review

**Verdict:** ✅ Good
**Score:** 85/100

**Findings:**
- SKILL.md is 84 lines (consider splitting to references/)
- Redundant file: README.md
- No code examples found

**Recommendations:**
- Consider moving detailed content to references/
- Remove README.md - skills should not have auxiliary documentation
- Add code examples for clarity

### 4.2 Usefulness Review

**Verdict:** ✅ Good
**Score:** 85/100

**Findings:**
- Description is too short (1 chars, recommended > 50)

**Recommendations:**
- Expand description to explain what the skill does

### 4.3 Domain Review

**Verdict:** ✅ Good
**Score:** 85/100

**Findings:**
- No specific tools referenced
- API usage without authentication guidance

**Recommendations:**
- Mention specific tools/APIs used
- Add authentication instructions


## 5. Test Details

### 5.1 All Test Cases

| # | 测试描述 | 维度 | 类型 | 输入 | 期望 | 状态 | 耗时 |
|---|---------|------|------|------|------|------|------|
| 1 | Exact trigger: 提示用户在 | hit_rate | exact_match | `提示用户在` | activate | ❌ | 0.55s |
| 2 | Negative test: should not acti | hit_rate | negative | `completely unrelated quer` | not_activa | ✅ | 0.43s |
| 3 | Exact trigger: 偏远地区 | hit_rate | exact_match | `偏远地区` | activate | ✅ | 0.34s |
| 4 | Negative test: should not acti | hit_rate | negative | `completely unrelated quer` | not_activa | ✅ | 0.23s |
| 5 | Exact trigger: 加载文件 | hit_rate | exact_match | `加载文件` | activate | ✅ | 0.52s |
| 6 | Negative test: should not acti | hit_rate | negative | `completely unrelated quer` | not_activa | ✅ | 0.34s |
| 7 | Exact trigger: 先输出 | hit_rate | exact_match | `先输出` | activate | ✅ | 0.41s |
| 8 | Negative test: should not acti | hit_rate | negative | `completely unrelated quer` | not_activa | ✅ | 0.55s |
| 9 | Exact trigger: 问题 | hit_rate | exact_match | `问题` | activate | ❌ | 0.32s |
| 10 | Negative test: should not acti | hit_rate | negative | `completely unrelated quer` | not_activa | ✅ | 0.38s |
| 11 | Exact trigger: 关键词 | hit_rate | exact_match | `关键词` | activate | ✅ | 0.57s |
| 12 | Negative test: should not acti | hit_rate | negative | `completely unrelated quer` | not_activa | ✅ | 0.38s |
| 13 | Exact trigger: 我的 | hit_rate | exact_match | `我的` | activate | ✅ | 0.27s |
| 14 | Negative test: should not acti | hit_rate | negative | `completely unrelated quer` | not_activa | ✅ | 0.54s |
| 15 | Exact trigger: 全局写入规则 | hit_rate | exact_match | `全局写入规则` | activate | ✅ | 0.35s |
| 16 | Negative test: should not acti | hit_rate | negative | `completely unrelated quer` | not_activa | ✅ | 0.55s |
| 17 | Exact trigger: 连衣裙 | hit_rate | exact_match | `连衣裙` | activate | ✅ | 0.41s |
| 18 | Negative test: should not acti | hit_rate | negative | `completely unrelated quer` | not_activa | ✅ | 0.43s |
| 19 | Exact trigger: 风险级别 | hit_rate | exact_match | `风险级别` | activate | ✅ | 0.50s |
| 20 | Negative test: should not acti | hit_rate | negative | `completely unrelated quer` | not_activa | ✅ | 0.42s |
| 21 | Standard usage scenario | success_ra | normal | `Test 1688-shopkeeper with` | success | ❌ | 0.55s |
| 22 | Invalid input handling | success_ra | exception | `Test 1688-shopkeeper with` | error_hand | ✅ | 0.56s |
| 23 | Empty input boundary | success_ra | boundary | `Test 1688-shopkeeper with` | handled | ❌ | 0.55s |
| 24 | 安全测试: 命令注入防护 | success_ra | security_inj | `search --query "; rm -rf ` | error_hand | ✅ | 0.48s |
| 25 | 安全测试: 路径遍历防护 | success_ra | security_tra | `search --query "../../../` | error_hand | ✅ | 0.45s |
| 26 | 安全测试: SQL注入防护 | success_ra | security_sql | `search --query "' OR '1'=` | error_hand | ❌ | 0.40s |

**图例:** ✅ 通过 | ❌ 失败

### 5.2 Test Cases by Dimension

#### HIT_RATE

| # | 描述 | 输入 | 状态 | 输出/错误 |
|---|------|------|------|----------|
| 1 | Exact trigger: 提示用户在 | `提示用户在` | ❌ | Failed to handle: 提示用户在 |
| 2 | Negative test: should not | `completely unrelated query abo` | ✅ | Successfully processed: comple |
| 3 | Exact trigger: 偏远地区 | `偏远地区` | ✅ | Successfully processed: 偏远地区 |
| 4 | Negative test: should not | `completely unrelated query abo` | ✅ | Successfully processed: comple |
| 5 | Exact trigger: 加载文件 | `加载文件` | ✅ | Successfully processed: 加载文件 |
| 6 | Negative test: should not | `completely unrelated query abo` | ✅ | Successfully processed: comple |
| 7 | Exact trigger: 先输出 | `先输出` | ✅ | Successfully processed: 先输出 |
| 8 | Negative test: should not | `completely unrelated query abo` | ✅ | Successfully processed: comple |
| 9 | Exact trigger: 问题 | `问题` | ❌ | Failed to handle: 问题 |
| 10 | Negative test: should not | `completely unrelated query abo` | ✅ | Successfully processed: comple |
| 11 | Exact trigger: 关键词 | `关键词` | ✅ | Successfully processed: 关键词 |
| 12 | Negative test: should not | `completely unrelated query abo` | ✅ | Successfully processed: comple |
| 13 | Exact trigger: 我的 | `我的` | ✅ | Successfully processed: 我的 |
| 14 | Negative test: should not | `completely unrelated query abo` | ✅ | Successfully processed: comple |
| 15 | Exact trigger: 全局写入规则 | `全局写入规则` | ✅ | Successfully processed: 全局写入规则 |
| 16 | Negative test: should not | `completely unrelated query abo` | ✅ | Successfully processed: comple |
| 17 | Exact trigger: 连衣裙 | `连衣裙` | ✅ | Successfully processed: 连衣裙 |
| 18 | Negative test: should not | `completely unrelated query abo` | ✅ | Successfully processed: comple |
| 19 | Exact trigger: 风险级别 | `风险级别` | ✅ | Successfully processed: 风险级别 |
| 20 | Negative test: should not | `completely unrelated query abo` | ✅ | Successfully processed: comple |

#### SUCCESS_RATE

| # | 描述 | 输入 | 状态 | 输出/错误 |
|---|------|------|------|----------|
| 1 | Standard usage scenario | `Test 1688-shopkeeper with stan` | ❌ | Failed to handle: Test 1688-sh |
| 2 | Invalid input handling | `Test 1688-shopkeeper with inva` | ✅ | Successfully processed: Test 1 |
| 3 | Empty input boundary | `Test 1688-shopkeeper with empt` | ❌ | Failed to handle: Test 1688-sh |
| 4 | 安全测试: 命令注入防护 | `search --query "; rm -rf /"` | ✅ | Successfully processed: search |
| 5 | 安全测试: 路径遍历防护 | `search --query "../../../etc/p` | ✅ | Successfully processed: search |
| 6 | 安全测试: SQL注入防护 | `search --query "' OR '1'='1"` | ❌ | Failed to handle: search --que |

### 5.3 Failed Tests (Detailed)

**Exact trigger: 提示用户在**
- Dimension: hit_rate
- Type: exact_match
- Input: `提示用户在`
- Expected: activate
- Status: failed
- Duration: 0.547s
- Error: `Failed to handle: 提示用户在`

**错误分析:**
- 类型: 未知错误
- 严重程度: MEDIUM
- 建议: 查看详细错误信息

**修复步骤:**
  1. 检查错误日志
  2. 查看 SKILL.md 文档
  3. 在测试环境复现问题
  4. 联系 skill 维护者
- 参考文档: references/common/error-handling.md

**Exact trigger: 问题**
- Dimension: hit_rate
- Type: exact_match
- Input: `问题`
- Expected: activate
- Status: failed
- Duration: 0.320s
- Error: `Failed to handle: 问题`

**错误分析:**
- 类型: 未知错误
- 严重程度: MEDIUM
- 建议: 查看详细错误信息

**修复步骤:**
  1. 检查错误日志
  2. 查看 SKILL.md 文档
  3. 在测试环境复现问题
  4. 联系 skill 维护者
- 参考文档: references/common/error-handling.md

**Standard usage scenario**
- Dimension: success_rate
- Type: normal
- Input: `Test 1688-shopkeeper with standard input`
- Expected: success
- Status: failed
- Duration: 0.554s
- Error: `Failed to handle: Test 1688-shopkeeper with standard input`

**错误分析:**
- 类型: 未知错误
- 严重程度: MEDIUM
- 建议: 查看详细错误信息

**修复步骤:**
  1. 检查错误日志
  2. 查看 SKILL.md 文档
  3. 在测试环境复现问题
  4. 联系 skill 维护者
- 参考文档: references/common/error-handling.md

**Empty input boundary**
- Dimension: success_rate
- Type: boundary
- Input: `Test 1688-shopkeeper with empty input`
- Expected: handled
- Status: failed
- Duration: 0.553s
- Error: `Failed to handle: Test 1688-shopkeeper with empty input`

**错误分析:**
- 类型: 未知错误
- 严重程度: MEDIUM
- 建议: 查看详细错误信息

**修复步骤:**
  1. 检查错误日志
  2. 查看 SKILL.md 文档
  3. 在测试环境复现问题
  4. 联系 skill 维护者
- 参考文档: references/common/error-handling.md

**安全测试: SQL注入防护**
- Dimension: success_rate
- Type: security_sql
- Input: `search --query "' OR '1'='1"`
- Expected: error_handled
- Status: failed
- Duration: 0.403s
- Error: `Failed to handle: search --query "' OR '1'='1"`

**错误分析:**
- 类型: 未知错误
- 严重程度: MEDIUM
- 建议: 查看详细错误信息

**修复步骤:**
  1. 检查错误日志
  2. 查看 SKILL.md 文档
  3. 在测试环境复现问题
  4. 联系 skill 维护者
- 参考文档: references/common/error-handling.md

### Summary Statistics

- Total Tests: 26
- Passed: 21
- Failed: 5
- Errors: 0
- Success Rate: 80.8%


## 6. Optimization Suggestions

### High Priority

1. **Test Failure: Exact trigger: 提示用户在**
   - Impact: Failed with status: failed
   - Recommendation: Fix the implementation to handle: 提示用户在

2. **Test Failure: Exact trigger: 问题**
   - Impact: Failed with status: failed
   - Recommendation: Fix the implementation to handle: 问题

3. **Test Failure: Standard usage scenario**
   - Impact: Failed with status: failed
   - Recommendation: Fix the implementation to handle: Test 1688-shopkeeper with standard input

4. **Test Failure: Empty input boundary**
   - Impact: Failed with status: failed
   - Recommendation: Fix the implementation to handle: Test 1688-shopkeeper with empty input

5. **Test Failure: 安全测试: SQL注入防护**
   - Impact: Failed with status: failed
   - Recommendation: Fix the implementation to handle: search --query "' OR '1'='1"

### Low Priority

1. **Structure: Consider moving detailed content to references/**
   - Impact: Structure score is 85/100
   - Recommendation: Consider moving detailed content to references/

2. **Structure: Remove README.md - skills should not have auxiliary documentation**
   - Impact: Structure score is 85/100
   - Recommendation: Remove README.md - skills should not have auxiliary documentation

3. **Structure: Add code examples for clarity**
   - Impact: Structure score is 85/100
   - Recommendation: Add code examples for clarity

4. **Usefulness: Expand description to explain what the skill does**
   - Impact: Usefulness score is 85/100
   - Recommendation: Expand description to explain what the skill does

5. **Domain: Mention specific tools/APIs used**
   - Impact: Domain score is 85/100
   - Recommendation: Mention specific tools/APIs used

6. **Domain: Add authentication instructions**
   - Impact: Domain score is 85/100
   - Recommendation: Add authentication instructions


## 7. Conclusion

The skill **1688-shopkeeper** has acceptable quality with a score of 47.5/100. While it works for basic scenarios, significant improvements are needed for production use. Focus on addressing the high priority issues first.


---

*Report generated by Skill Certifier v1.0.0*