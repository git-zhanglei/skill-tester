# skill-tester — 配置说明

## 默认配置

```yaml
# 执行设置
timeout_per_test: 60            # 每个测试案例超时（秒）
max_test_cases: 30              # 最大测试案例总数（上限）
auto_save_interval: 5           # 每完成 N 个自动保存一次

# 安全检查
skip_safety_check: false        # 跳过安全检查（不推荐）
fail_on_critical: true          # 严重问题时终止测试

# 多模型设置
multi_model: false              # 是否启用多模型分发
models: []                      # 指定模型列表（空=自动检测）
model_distribution: "balanced"  # 分发策略：balanced / round-robin / dimension-based

# 报告设置
output_format: markdown         # markdown 或 json 或 both
output_file: ""                 # 空=自动命名为 test-report-{skill}-{timestamp}
include_passed_tests: true      # 报告中包含通过的测试
include_model_comparison: true  # 多模型时包含对比报告

# 评分权重（总和应为 100）
weights:
  hit_rate: 25
  spec_compliance: 20
  agent_comprehension: 25
  execution_success: 30

# 评分阈值
thresholds:
  excellent: 90
  good: 70
  acceptable: 40
```

## 配置优先级

1. 命令行参数（最高）
2. 环境变量
3. 配置文件（`<workspace>/.skill-tester/config.yaml`）
4. 默认值（最低）

## 环境变量

```bash
# 执行
SKILL_TESTER_TIMEOUT=60
SKILL_TESTER_MAX_CASES=30

# 多模型
SKILL_TESTER_MULTI_MODEL=false
SKILL_TESTER_MODELS="model-a,model-b"

# 报告
SKILL_TESTER_FORMAT=markdown
SKILL_TESTER_OUTPUT=""

# 安全
SKILL_TESTER_SKIP_SAFETY=false
```

## 自定义配置文件

```yaml
# <workspace>/.skill-tester/config.yaml
timeout_per_test: 120
multi_model: true

weights:
  hit_rate: 25
  spec_compliance: 20
  agent_comprehension: 25
  execution_success: 30

thresholds:
  excellent: 90
  good: 70
```

## 评分权重说明

权重决定各维度在综合评分中的贡献比例，**四个权重之和必须为 100**。

| 维度 | 默认权重 | 调整建议 |
|------|----------|--------|
| `hit_rate` | 25 | 触发词不重要的工具类 Skill 可降低 |
| `spec_compliance` | 20 | 规范要求严格时可提高 |
| `agent_comprehension` | 25 | 复杂指令 Skill 可提高 |
| `execution_success` | 30 | 核心能力，建议不低于 25 |

## 模型分发策略

| 策略 | 说明 | 适用场景 |
|------|------|--------|
| `balanced` | 均匀分配测试案例到各模型 | 通用（默认） |
| `round-robin` | 轮询分配，每个案例依次换模型 | 对比各模型一致性 |
| `dimension-based` | 按测试维度分组分配不同模型 | 专项能力对比 |
