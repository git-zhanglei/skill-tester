# Skill Evaluation Report: 1688-shopkeeper

**Generated:** 2026-03-17 19:06:01
**Overall Score:** 65.0/100
**Recommendation:** ⭐⭐⭐⭐ Good - Minor improvements recommended

## 1. Executive Summary

This skill shows good overall quality with solid functionality. While it performs well in most areas, there are opportunities for improvement that should be addressed for optimal reliability.

### Key Metrics

| Metric | Score | Status |
|--------|-------|--------|
| Overall | 65.0/100 | ✅ |
| Safety | ✅ Pass | PASSED |
| Trigger Hit Rate | 100.0% | ✅ |
| Task Success Rate | 100.0% | ✅ |

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

**Score:** 25.0/25

| Test Type | Total | Passed | Rate |
|-----------|-------|--------|------|
| Overall | 20 | 20 | 100.0% |

### 3.2 Task Success Rate (Weight: 30%)

**Score:** 30.0/30

| Test Type | Total | Passed | Rate |
|-----------|-------|--------|------|
| Overall | 3 | 3 | 100.0% |


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

### Summary Statistics

- Total Tests: 23
- Passed: 23
- Failed: 0
- Errors: 0
- Success Rate: 100.0%


## 6. Optimization Suggestions

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

The skill **1688-shopkeeper** shows good quality with a score of 65.0/100. It is functional and usable, but there are areas for improvement. Addressing the medium and high priority suggestions will enhance its reliability.


---

*Report generated by Skill Certifier v1.0.0*