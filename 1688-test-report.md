# Skill Evaluation Report: 1688-shopkeeper

**Generated:** 2026-03-17 19:55:21
**Overall Score:** 57.5/100
**Recommendation:** ⭐⭐⭐ Acceptable - Improvements needed

## 1. Executive Summary

This skill has acceptable quality but requires attention before production use. Several areas need improvement, particularly in test coverage and error handling.

### Key Metrics

| Metric | Score | Status |
|--------|-------|--------|
| Overall | 57.5/100 | ⚠️ |
| Safety | ✅ Pass | PASSED |
| Trigger Hit Rate | 90.0% | ✅ |
| Task Success Rate | 83.3% | ✅ |

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

**Score:** 25.0/30

| Test Type | Total | Passed | Rate |
|-----------|-------|--------|------|
| Overall | 6 | 5 | 83.3% |


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

### Failed Tests

**Exact trigger: 没装的话点链接下载**
- Dimension: hit_rate
- Input: `没装的话点链接下载`
- Expected: activate
- Status: failed
- Error: `Failed to handle: 没装的话点链接下载`

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

**Exact trigger: 统一入口**
- Dimension: hit_rate
- Input: `统一入口`
- Expected: activate
- Status: failed
- Error: `Failed to handle: 统一入口`

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

**安全测试: 路径遍历防护**
- Dimension: success_rate
- Input: `search --query "../../../etc/passwd"`
- Expected: error_handled
- Status: failed
- Error: `Failed to handle: search --query "../../../etc/passwd"`

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
- Passed: 23
- Failed: 3
- Errors: 0
- Success Rate: 88.5%


## 6. Optimization Suggestions

### High Priority

1. **Test Failure: Exact trigger: 没装的话点链接下载**
   - Impact: Failed with status: failed
   - Recommendation: Fix the implementation to handle: 没装的话点链接下载

2. **Test Failure: Exact trigger: 统一入口**
   - Impact: Failed with status: failed
   - Recommendation: Fix the implementation to handle: 统一入口

3. **Test Failure: 安全测试: 路径遍历防护**
   - Impact: Failed with status: failed
   - Recommendation: Fix the implementation to handle: search --query "../../../etc/passwd"

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

The skill **1688-shopkeeper** has acceptable quality with a score of 57.5/100. While it works for basic scenarios, significant improvements are needed for production use. Focus on addressing the high priority issues first.


---

*Report generated by Skill Certifier v1.0.0*