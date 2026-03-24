# CI/CD 集成

将 skill-tester 集成到持续集成流程，在每次提交时自动检测 Skill 质量下降。

## 报告获取方式

Agent 执行测试后，结果 JSON 保存在当前工作目录。使用 `--output-json` 标志生成机器可读的 JSON 报告：

```
测试skill <skill_path> --yes --output-json
```

`report_builder.py` 可直接用 `python3` 调用生成报告文件：

```bash
python3 scripts/report_builder.py results.json --output report.md --json
```

## GitHub Actions 示例

```yaml
name: Skill Quality Gate

on:
  pull_request:
    paths:
      - 'SKILL.md'
      - 'scripts/**'
      - 'references/**'

jobs:
  certify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: 安全检查
        run: |
          cd scripts
          python3 safety_checker.py ../
          STATUS=$(python3 safety_checker.py ../ | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d['status']!='failed' else 1)")

      - name: 规范程度检查
        run: |
          cd scripts
          python3 smart_test_generator.py ../

      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: skill-tester-report
          path: test-report-*.md
```

## GitLab CI 示例

```yaml
skill-certify:
  stage: test
  script:
    - cd scripts && python3 safety_checker.py ../
    - cd scripts && python3 smart_test_generator.py ../
  artifacts:
    paths:
      - test-report-*.md
    when: always
  rules:
    - changes:
        - SKILL.md
        - scripts/**
```

## 质量门控阈值建议

| 阶段 | 最低要求 | 推荐目标 |
|------|---------|---------|
| 安全检查 | 通过（无 failed） | 通过（无 warning） |
| 触发命中率 | ≥ 60% | ≥ 85% |
| Skill 规范 | ≥ 60% | ≥ 80% |
| Agent 理解度 | ≥ 60% | ≥ 80% |
| 执行成功率 | ≥ 60% | ≥ 85% |
| 综合评分 | ≥ 40 | ≥ 70 |

## 解析 JSON 报告的 Shell 示例

`report_builder.py` 生成的 JSON 报告中，综合评分位于 `summary.overall_score`：

```bash
SCORE=$(python3 -c "
import json, sys
with open('test-report-*.json') as f:
    d = json.load(f)
print(d['summary']['overall_score'])
")

if (( $(echo "$SCORE < 40" | bc -l) )); then
  echo "❌ 综合评分 $SCORE 低于最低要求，流水线失败"
  exit 1
fi
echo "✅ 综合评分 $SCORE，通过质量门控"
```
