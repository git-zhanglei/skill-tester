# 评审器与评分体系

## 综合评分公式

```
综合评分 = 触发命中率×25% + Skill规范程度×20% + Agent理解度×25% + 执行成功率×30%
```

**特殊规则（优先于公式）：**
1. 安全检查失败 → 综合评分强制归零，测试终止
2. 任意单维度分数 < 40 → 最终评级上限为 ⭐⭐⭐（可接受）

**评级对照：**

| 评级 | 分数范围 | 说明 |
|------|---------|------|
| ⭐⭐⭐⭐⭐ 优秀 | 90–100 | 推荐发布 🏆 Certified |
| ⭐⭐⭐⭐ 良好 | 70–89  | 可发布，建议优化 ✅ Verified |
| ⭐⭐⭐ 可接受 | 40–69 | 需改进后发布 🔄 Beta |
| ⭐⭐ 需改进 | 0–39 | 不建议发布 |
| ❌ 不合格 | N/A | 安全检查失败，禁止发布 |

---

## 维度 1：触发命中率评审器（权重 25%）

**评审逻辑：**

```python
def calculate_hit_rate_score(test_results: list) -> float:
    exact_tests    = [r for r in test_results if r['type'] == 'exact_match']
    fuzzy_tests    = [r for r in test_results if r['type'] == 'fuzzy_match']
    negative_tests = [r for r in test_results if r['type'] == 'negative_test']
    
    # 各子类型通过率
    exact_rate    = passed(exact_tests)    / len(exact_tests)    if exact_tests    else 0
    fuzzy_rate    = passed(fuzzy_tests)    / len(fuzzy_tests)    if fuzzy_tests    else 0
    negative_rate = passed(negative_tests) / len(negative_tests) if negative_tests else 0
    
    # 加权合并（精确:模糊:负面 = 4:4:2）
    hit_rate = (exact_rate * 0.4 + fuzzy_rate * 0.4 + negative_rate * 0.2) * 100
    return hit_rate
```

**分析要点：**
- 精确匹配失败 → 触发词描述有问题，需修改 SKILL.md
- 模糊匹配失败率高 → Skill 用途描述不够清晰，用户难以联想触发
- 负面测试失败（错误激活）→ 触发词过于宽泛，可能干扰其他 Skill

---

## 维度 2：Skill规范程度评审器（权重 20%）

静态分析 SKILL.md，无需执行 Agent。

```python
def calculate_spec_score(skill_path: str) -> dict:
    skill_md = read_file(f"{skill_path}/SKILL.md")
    frontmatter, body = parse_frontmatter(skill_md)
    lines = skill_md.split('\n')
    
    score = 100
    findings = []
    
    # Frontmatter name（15%）
    if not frontmatter.get('name'):
        score -= 15
        findings.append("❌ frontmatter 缺少 'name' 字段")
    
    # Frontmatter description（15%）
    if not frontmatter.get('description') or len(frontmatter.get('description','')) < 10:
        score -= 15
        findings.append("❌ frontmatter 缺少有效的 'description' 字段")
    
    # 长度限制（15%）
    if len(lines) > 500:
        score -= 15
        findings.append(f"❌ SKILL.md 有 {len(lines)} 行，超过 500 行限制")
    elif len(lines) > 400:
        score -= 5
        findings.append(f"⚠️ SKILL.md 有 {len(lines)} 行，接近 500 行限制")
    
    # 渐进式披露（20%）
    has_references = os.path.exists(f"{skill_path}/references/")
    if len(lines) > 200 and not has_references:
        score -= 20
        findings.append("❌ SKILL.md 较长但无 references/ 目录，建议使用渐进式披露")
    elif len(lines) > 300 and has_references:
        ref_files = os.listdir(f"{skill_path}/references/")
        if len(ref_files) < 2:
            score -= 10
            findings.append("⚠️ SKILL.md 较长，references/ 中文档不足")
    
    # 结构清晰度（20%）
    has_h1 = any(line.startswith('# ') for line in lines)
    has_quick_start = any('快速开始' in line or 'Quick Start' in line for line in lines)
    if not has_h1:
        score -= 10
        findings.append("❌ 缺少 H1 标题")
    if not has_quick_start:
        score -= 10
        findings.append("⚠️ 建议添加快速开始章节")
    
    # 代码示例（15%）
    code_blocks = body.count('```')
    if code_blocks < 2:
        score -= 15
        findings.append("❌ 缺少代码/命令示例（至少需要 1 个代码块）")
    
    return {
        'score': max(0, score),
        'findings': findings,
        'recommendations': generate_recommendations(findings)
    }
```

---

## 维度 3：Agent理解度评审器（权重 25%）

在执行阶段，分析 Agent 执行日志来评估理解准确性。

```python
def calculate_comprehension_score(test_results: list, skill_md: str) -> float:
    expected_steps   = extract_declared_steps(skill_md)
    expected_tools   = extract_declared_tools(skill_md)
    
    step_scores   = []
    tool_scores   = []
    format_scores = []
    error_scores  = []
    
    for result in test_results:
        if result['dimension'] != 'agent_comprehension':
            continue
        
        if result['type'] == 'step_following':
            observed = result['result'].get('steps_observed', [])
            coverage = len(set(observed) & set(expected_steps)) / len(expected_steps)
            step_scores.append(coverage)
        
        elif result['type'] == 'tool_selection':
            called = result['result'].get('tools_called', [])
            precision = len(set(called) & set(expected_tools)) / max(len(called), 1)
            tool_scores.append(precision)
        
        elif result['type'] == 'output_format':
            format_scores.append(1.0 if result['result']['status'] == 'passed' else 0.0)
        
        elif result['type'] == 'error_behavior':
            error_scores.append(1.0 if result['result']['status'] == 'passed' else 0.0)
    
    # 4 类型加权平均（步骤:工具:格式:错误 = 3:3:2:2）
    weights = [0.3, 0.3, 0.2, 0.2]
    scores  = [avg(step_scores), avg(tool_scores), avg(format_scores), avg(error_scores)]
    return sum(w * s for w, s in zip(weights, scores)) * 100
```

**分析要点：**
- 步骤遵循度低 → Skill 流程描述不够清晰，Agent 难以理解执行顺序
- 工具调用不准确 → Skill 中工具说明含糊，或声明了不存在的工具
- 输出格式不符 → Skill 中输出格式描述不具体

---

## 维度 4：执行成功率评审器（权重 30%）

统计各场景类型的通过率。

```python
def calculate_execution_score(test_results: list) -> float:
    normal_tests   = [r for r in test_results if r['type'] == 'normal_path'     and r['dimension'] == 'execution_success']
    boundary_tests = [r for r in test_results if r['type'] == 'boundary_case'   and r['dimension'] == 'execution_success']
    error_tests    = [r for r in test_results if r['type'] == 'error_handling'  and r['dimension'] == 'execution_success']
    
    normal_rate   = pass_rate(normal_tests)   if normal_tests   else 1.0
    boundary_rate = pass_rate(boundary_tests) if boundary_tests else 1.0
    error_rate    = pass_rate(error_tests)    if error_tests    else 1.0
    
    # 正常路径权重最高（正常:边界:异常 = 5:3:2）
    execution_score = (normal_rate * 0.5 + boundary_rate * 0.3 + error_rate * 0.2) * 100
    return execution_score
```

**分析要点：**
- 正常路径失败率高 → Skill 核心功能有问题，优先修复
- 边界条件失败率高 → Skill 输入验证不足
- 异常处理失败 → Skill 缺乏错误处理指导

---

## 综合报告生成

```python
def generate_report(safety_result, hit_rate_score, spec_score, 
                    comprehension_score, execution_score, config) -> dict:
    # 安全门控
    if safety_result['status'] == 'failed':
        return {
            'overall_score': 0,
            'rating': '❌ 不合格',
            'safety': safety_result,
            'note': '安全检查失败，测试已终止'
        }
    
    weights = config['weights']
    overall = (
        hit_rate_score      * weights['hit_rate']          / 100 +
        spec_score          * weights['spec_compliance']   / 100 +
        comprehension_score * weights['agent_comprehension']/ 100 +
        execution_score     * weights['execution_success'] / 100
    )
    
    # 特殊规则：单维度 < 40 则评级上限为 ⭐⭐⭐
    min_score = min(hit_rate_score, spec_score, comprehension_score, execution_score)
    rating = get_rating(overall)
    if min_score < 40 and rating in ['⭐⭐⭐⭐⭐', '⭐⭐⭐⭐']:
        rating = '⭐⭐⭐（单维度不达标限制）'
    
    return {
        'overall_score': round(overall, 1),
        'rating': rating,
        'dimensions': {
            'hit_rate':             {'score': hit_rate_score,      'weight': weights['hit_rate']},
            'spec_compliance':      {'score': spec_score,          'weight': weights['spec_compliance']},
            'agent_comprehension':  {'score': comprehension_score, 'weight': weights['agent_comprehension']},
            'execution_success':    {'score': execution_score,     'weight': weights['execution_success']}
        },
        'safety': safety_result,
        'recommendations': generate_recommendations(...)
    }
```

## 优化建议生成规则

| 维度 | 分数区间 | 优先级 | 建议 |
|------|---------|--------|------|
| 触发命中率 | < 70 | P0 | 检查触发词是否清晰，增加描述多样性 |
| 触发命中率（负面失败）| — | P1 | 触发词过宽，细化描述排除误触发场景 |
| Skill规范程度 | < 60 | P1 | 检查 frontmatter、SKILL.md 长度、references/ |
| Agent理解度 | < 70 | P0 | 简化步骤描述，增加示例和边界说明 |
| 执行成功率（正常路径）| < 80 | P0 | 核心功能有缺陷，优先修复 |
| 执行成功率（边界）| < 60 | P2 | 增加输入验证和边界说明 |
