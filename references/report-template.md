# Skill 评估报告: {{skill_name}}

**生成时间:** {{timestamp}}  
**总分:** {{overall_score}}/100  
**建议:** {{recommendation}}

---

## 1. 执行摘要

{{summary}}

### 关键指标

| 指标 | 分数 | 状态 |
|--------|-------|--------|
| 总分 | {{overall_score}}/100 | {{overall_status}} |
| 安全 | {{safety_score}} | {{safety_status}} |
| 触发命中率 | {{hit_rate}}% | {{hit_status}} |
| 任务成功率 | {{success_rate}}% | {{success_status}} |
| 分支覆盖率 | {{coverage}}% | {{coverage_status}} |

---

## 2. 安全预检

{{#if safety_issues}}
### ❌ 严重问题

{{#each safety_issues}}
- {{this}}
{{/each}}

{{/if}}

{{#if safety_warnings}}
### ⚠️ 警告

{{#each safety_warnings}}
- {{this}}
{{/each}}

{{/if}}

{{#unless safety_issues}}
{{#unless safety_warnings}}
✅ 未发现安全问题。
{{/unless}}
{{/unless}}

### 检查的文件

{{#each checked_files}}
- {{this}}
{{/each}}

---

## 3. 定量指标

### 3.1 触发命中率（权重: 25%）

**分数:** {{hit_rate_score}}/25

| 测试类型 | 总数 | 通过 | 比率 |
|-----------|-------|--------|------|
| 精确匹配 | {{hit_exact_total}} | {{hit_exact_passed}} | {{hit_exact_rate}}% |
| 模糊匹配 | {{hit_fuzzy_total}} | {{hit_fuzzy_passed}} | {{hit_fuzzy_rate}}% |
| 负面测试 | {{hit_neg_total}} | {{hit_neg_passed}} | {{hit_neg_rate}}% |

**发现:**
{{hit_findings}}

### 3.2 任务成功率（权重: 30%）

**分数:** {{success_score}}/30

| 测试类型 | 总数 | 通过 | 比率 |
|-----------|-------|--------|------|
| 正常路径 | {{success_normal_total}} | {{success_normal_passed}} | {{success_normal_rate}}% |
| 异常处理 | {{success_except_total}} | {{success_except_passed}} | {{success_except_rate}}% |
| 边界情况 | {{success_bound_total}} | {{success_bound_passed}} | {{success_bound_rate}}% |

**发现:**
{{success_findings}}

### 3.3 分支覆盖率（权重: 20%）

**分数:** {{coverage_score}}/20

| 覆盖类型 | 百分比 |
|---------------|------------|
| 条件覆盖 | {{cond_coverage}}% |
| 路径覆盖 | {{path_coverage}}% |

**未覆盖分支:**
{{#each uncovered_branches}}
- {{this}}
{{/each}}

### 3.4 工具调用准确度（权重: 15%）

**分数:** {{tool_score}}/15

| 指标 | 分数 |
|--------|-------|
| 工具选择准确度 | {{tool_select_rate}}% |
| 参数完整性 | {{tool_param_rate}}% |

### 3.5 错误处理（权重: 10%）

**分数:** {{error_score}}/10

| 指标 | 分数 |
|--------|-------|
| 异常覆盖 | {{except_coverage}}% |
| 错误信息质量 | {{error_msg_score}}/10 |

---

## 4. 定性评估

### 4.1 结构评审

**结论:** {{structure_verdict}}

{{structure_findings}}

### 4.2 实用性评审

**结论:** {{usefulness_verdict}}

{{usefulness_findings}}

### 4.3 领域评审

**结论:** {{domain_verdict}}

{{domain_findings}}

---

## 5. 测试详情

### 失败的测试

{{#each failed_tests}}
#### {{test_name}}

- **维度:** {{dimension}}
- **输入:** {{input}}
- **预期:** {{expected}}
- **实际:** {{actual}}
- **错误:** {{error}}

{{/each}}

### 通过的测试

{{#each passed_tests}}
- {{test_name}} ({{dimension}}) - {{duration}}秒
{{/each}}

---

## 6. 优化建议

### 高优先级

{{#each high_priority_suggestions}}
1. **{{title}}**
   - 影响: {{impact}}
   - 建议: {{recommendation}}
{{/each}}

### 中优先级

{{#each medium_priority_suggestions}}
1. **{{title}}**
   - 影响: {{impact}}
   - 建议: {{recommendation}}
{{/each}}

### 低优先级

{{#each low_priority_suggestions}}
1. **{{title}}**
   - 影响: {{impact}}
   - 建议: {{recommendation}}
{{/each}}

---

## 7. 结论

{{conclusion}}

---

*报告由 Skill Certifier v1.0.0 生成*