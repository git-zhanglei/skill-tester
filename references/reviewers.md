# 定性评审器

## 概述

定性评审器从人类视角评估 skill 质量：结构、实用性和领域正确性。

嵌入自 Skill Test，增强自动评分功能。

## 评审器类型

### 1. 结构评审器

评估 SKILL.md 组织和格式。

**标准:**

| 检查 | 权重 | 描述 |
|-------|--------|-------------|
| Frontmatter | 15% | 名称和描述存在 |
| 长度 | 10% | 少于 500 行 |
| 渐进式披露 | 10% | 使用 references/ 目录 |
| 无冗余文件 | 10% | 无 README/CHANGELOG 等 |
| 正确标题 | 10% | 有 H1，逻辑结构 |
| 代码示例 | 5% | 包含用法示例 |

**评分:**
- 90-100: 结构优秀
- 70-89: 结构良好
- 50-69: 可接受，小问题
- <50: 需要重大改进

**常见问题:**
- 缺少 frontmatter 字段
- SKILL.md 太长（>500 行）
- 无代码示例
- 冗余文档文件

### 2. 实用性评审器

评估清晰度和实用性。

**标准:**

| 检查 | 权重 | 描述 |
|-------|--------|-------------|
| 清晰描述 | 15% | 描述说明用途 |
| 清晰触发词 | 15% | 何时使用很明显 |
| 可执行 | 10% | 指令可执行 |
| 示例 | 10% | 真实用法示例 |
| 前置条件 | 5% | 列出需求 |

**评分:**
- 90-100: 非常有用，清晰指令
- 70-89: 有用，小清晰度问题
- 50-69: 有些用，需要改进
- <50: 不清晰或不可执行

**常见问题:**
- 描述太模糊
- 无清晰触发条件
- 缺少示例
- 无错误处理指导

### 3. 领域评审器

评估技术正确性。

**标准:**

| 检查 | 权重 | 描述 |
|-------|--------|-------------|
| 工具引用 | 5% | 工具提及恰当 |
| API 指导 | 10% | 认证已文档化 |
| 错误处理 | 10% | 处理失败模式 |
| 最佳实践 | 5% | 遵循领域惯例 |

**评分:**
- 90-100: 技术上优秀
- 70-89: 良好，小问题
- 50-69: 可接受，有些担忧
- <50: 发现技术问题

**常见问题:**
- API 使用无认证指导
- 无错误处理
- 过时的工具引用

## 评审器实现

```python
class ReviewerSuite:
    def evaluate(self) -> Dict:
        return {
            'structure': self._structure_reviewer(),
            'usefulness': self._usefulness_reviewer(),
            'domain': self._domain_reviewer()
        }
    
    def _structure_reviewer(self) -> Dict:
        findings = []
        score = 100
        
        # 检查 frontmatter
        if not self.frontmatter.get('name'):
            findings.append("frontmatter 中缺少 'name'")
            score -= 15
        
        # 检查长度
        lines = self.body.split('\n')
        if len(lines) > 500:
            findings.append(f"SKILL.md 有 {len(lines)} 行")
            score -= 10
        
        # ... 更多检查
        
        return {
            'verdict': self._get_verdict(score),
            'score': score,
            'findings': findings,
            'recommendations': self._generate_recommendations(findings)
        }
```

## 与定量结果集成

定性分数与定量指标结合：

```
最终分数 = (定量 × 0.85) + (定性 × 0.15)

其中:
- 定量 = 命中率(25%) + 成功率(30%) + 覆盖率(20%) + 工具准确度(15%) + 错误处理(10%)
- 定性 = 结构(5%) + 实用性(5%) + 领域(5%)
```

## 自定义评审器

你可以添加自定义评审器：

```python
# ~/.skill-certifier/custom_reviewers.py
class SecurityReviewer:
    def evaluate(self, skill_path):
        # 自定义安全检查
        pass

# 在配置中注册
custom_reviewers:
  - security: SecurityReviewer
```

## 评审器输出格式

```json
{
  "structure": {
    "verdict": "✅ 良好",
    "score": 85,
    "findings": [
      "SKILL.md 有 120 行",
      "考虑将详情移到 references/"
    ],
    "recommendations": [
      "将长章节拆分到参考文件"
    ]
  },
  "usefulness": {
    "verdict": "✅ 优秀",
    "score": 92,
    "findings": [],
    "recommendations": []
  },
  "domain": {
    "verdict": "⚠️ 可接受",
    "score": 65,
    "findings": [
      "API 认证未文档化"
    ],
    "recommendations": [
      "添加获取 API key 的章节"
    ]
  }
}
```

## 最佳实践

1. **评审器补充而非替代**定量测试
2. **人工判断**对边界情况仍有价值
3. **迭代**评审器标准基于反馈
4. **文档化**评审器逻辑以透明