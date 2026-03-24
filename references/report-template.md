# Skill 认证报告: {{skill_name}}

**生成时间:** {{generated_at}}
**Skill路径:** {{skill_path}}
**综合评分:** {{overall_score}}/100
**评级:** {{rating}}
**认证状态:** {{badge}}

---

## 1. 执行摘要

{{summary}}

### 关键指标

| 指标 | 分数 | 权重 | 状态 |
|------|------|------|------|
| 触发命中率 | {{hit_rate}}% | 25% | {{hit_status}} |
| Skill规范程度 | {{spec_compliance}}% | 20% | {{spec_status}} |
| Agent理解度 | {{agent_comprehension}}% | 25% | {{comprehension_status}} |
| 执行成功率 | {{execution_success}}% | 30% | {{execution_status}} |
| **综合评分** | **{{overall_score}}/100** | — | {{overall_status}} |

---

## 2. 安全检查

**状态:** {{safety_status}}

{{#if safety_issues}}
### ❌ 严重问题

{{#each safety_issues}}
- **{{this.file}}:{{this.line}}** — {{this.description}}
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
✅ 未发现安全问题
{{/unless}}
{{/unless}}

---

## 3. 触发命中率（{{hit_rate}}% / 权重 25%）

| 测试类型 | 总数 | 通过 | 通过率 |
|---------|------|------|--------|
| 精确匹配 | {{hit_exact_total}} | {{hit_exact_passed}} | {{hit_exact_rate}}% |
| 模糊变体 | {{hit_fuzzy_total}} | {{hit_fuzzy_passed}} | {{hit_fuzzy_rate}}% |
| 负面测试 | {{hit_negative_total}} | {{hit_negative_passed}} | {{hit_negative_rate}}% |

**分析：**
{{hit_rate_analysis}}

---

## 4. Skill规范程度（{{spec_compliance}}% / 权重 20%）

| 检查项 | 状态 | 详情 |
|-------|------|------|
| Frontmatter name | {{spec_name_status}} | {{spec_name_detail}} |
| Frontmatter description | {{spec_desc_status}} | {{spec_desc_detail}} |
| 长度合规（≤500行） | {{spec_length_status}} | {{spec_length_detail}} |
| 渐进式披露 | {{spec_disclosure_status}} | {{spec_disclosure_detail}} |
| 结构清晰度 | {{spec_structure_status}} | {{spec_structure_detail}} |
| 代码示例 | {{spec_examples_status}} | {{spec_examples_detail}} |

**发现：**
{{spec_findings}}

---

## 5. Agent理解度（{{agent_comprehension}}% / 权重 25%）

| 测试类型 | 总数 | 通过 | 通过率 |
|---------|------|------|--------|
| 步骤遵循 | {{comp_step_total}} | {{comp_step_passed}} | {{comp_step_rate}}% |
| 工具调用准确度 | {{comp_tool_total}} | {{comp_tool_passed}} | {{comp_tool_rate}}% |
| 输出格式符合度 | {{comp_format_total}} | {{comp_format_passed}} | {{comp_format_rate}}% |
| 错误处理行为 | {{comp_error_total}} | {{comp_error_passed}} | {{comp_error_rate}}% |

**分析：**
{{comprehension_analysis}}

---

## 6. 执行成功率（{{execution_success}}% / 权重 30%）

| 测试类型 | 总数 | 通过 | 通过率 |
|---------|------|------|--------|
| 正常路径 | {{exec_normal_total}} | {{exec_normal_passed}} | {{exec_normal_rate}}% |
| 边界条件 | {{exec_boundary_total}} | {{exec_boundary_passed}} | {{exec_boundary_rate}}% |
| 异常处理 | {{exec_error_total}} | {{exec_error_passed}} | {{exec_error_rate}}% |

**分析：**
{{execution_analysis}}

{{#if multi_model_results}}
---

## 7. 多模型对比

| 模型 | 触发命中率 | Agent理解度 | 执行成功率 | 综合 |
|------|-----------|-----------|-----------|------|
{{#each multi_model_results}}
| {{this.model}} | {{this.hit_rate}}% | {{this.comprehension}}% | {{this.execution}}% | {{this.overall}}% |
{{/each}}

**建议使用模型：** {{recommended_model}}
{{/if}}

---

## 8. 优化建议

{{#each recommendations}}
### {{this.priority}} — {{this.dimension}}

**问题：** {{this.issue}}
**建议：** {{this.suggestion}}

{{/each}}

---

## 9. 失败测试详情

{{#if failed_cases}}
{{#each failed_cases}}
**[{{this.id}}]** {{this.description}}
- 输入：`{{this.input}}`
- 预期：`{{this.expected}}`
- 实际：`{{this.actual}}`
- 原因：{{this.failure_reason}}

{{/each}}
{{else}}
✅ 所有测试案例均通过
{{/if}}

---

*skill-tester v3 — 生成于 {{generated_at}}*
