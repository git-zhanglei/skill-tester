# CI/CD 集成

将 skill-tester 集成到持续集成流程，在每次提交时自动检测 Skill 质量下降。

## 质量门禁脚本 ci_gate.py

`ci_gate.py` 读取 `report_builder.py` 生成的 JSON 报告，根据阈值判断是否通过质量门禁：

```bash
# 使用默认阈值（综合 ≥ 40，各维度 ≥ 40）
python3 scripts/ci_gate.py report.json

# 自定义阈值
python3 scripts/ci_gate.py report.json --min-overall 70 --min-dimension 60
```

- exit 0 = 通过
- exit 1 = 未通过（输出哪些维度不达标）

## 报告获取方式

Agent 执行测试后，结果 JSON 保存在当前工作目录。使用 `--output-json` 标志生成机器可读的 JSON 报告：

```
测试skill <skill_path> --yes --output-json
```

`report_builder.py` 也可直接调用：

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
          python3 scripts/safety_checker.py ./ | python3 -c "
          import sys, json
          d = json.load(sys.stdin)
          if d['status'] == 'failed':
              print('❌ 安全检查失败')
              sys.exit(1)
          print('✅ 安全检查通过')
          "

      - name: 规范程度检查
        run: python3 scripts/spec_checker.py ./ --json

      - name: 生成报告
        run: |
          python3 scripts/report_builder.py results.json --output report.md --json

      - name: 质量门禁
        run: python3 scripts/ci_gate.py report.json --min-overall 40 --min-dimension 40

      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: skill-tester-report
          path: |
            test-report-*.md
            report.json
```

## GitLab CI 示例

```yaml
skill-certify:
  stage: test
  script:
    - python3 scripts/safety_checker.py ./
    - python3 scripts/spec_checker.py ./ --json
    - python3 scripts/report_builder.py results.json --output report.md --json
    - python3 scripts/ci_gate.py report.json --min-overall 40
  artifacts:
    paths:
      - test-report-*.md
      - report.json
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
