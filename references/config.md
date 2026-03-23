# Skill Certifier 配置

## 默认配置

```yaml
# 执行设置
parallel_degree: 4              # 并行测试代理数量
timeout_per_test: 60            # 每个测试用例超时时间（秒）
max_test_cases_per_dimension: 20
sandbox_auto_cleanup: true

# 安全设置
skip_safety_check: false        # 跳过阶段 1 安全预检
fail_on_critical: true          # 发现严重问题时停止测试

# 定性设置
skip_qualitative: false         # 跳过阶段 4 定性评估

# 报告设置
report_format: markdown         # markdown 或 json
output_file: report.md          # 默认输出文件名
include_passed_tests: true      # 报告中包含通过的测试
include_test_output: false      # 包含完整测试输出（详细模式）

# 评分权重
weights:
  hit_rate: 25
  success_rate: 30
  branch_coverage: 20
  tool_accuracy: 15
  error_handling: 10

# 阈值
thresholds:
  excellent: 80
  good: 60
  acceptable: 40
```

## 配置来源（优先级顺序）

1. 命令行参数（最高优先级）
2. 环境变量
3. 配置文件（`~/.skill-certifier/config.yaml`）
4. 默认值（最低优先级）

## 环境变量

```bash
# 执行
SKILL_CERTIFIER_PARALLEL=4
SKILL_CERTIFIER_TIMEOUT=60

# 安全
SKILL_CERTIFIER_SKIP_SAFETY=false
SKILL_CERTIFIER_FAIL_ON_CRITICAL=true

# 报告
SKILL_CERTIFIER_FORMAT=markdown
SKILL_CERTIFIER_OUTPUT=report.md
```

## 配置文件示例

```yaml
# ~/.skill-certifier/config.yaml
parallel_degree: 8
timeout_per_test: 120

weights:
  hit_rate: 30
  success_rate: 25

thresholds:
  excellent: 85
  good: 70
```