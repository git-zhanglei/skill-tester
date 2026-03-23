# Skill Certifier Usage Examples

## Basic Usage

### Test a skill

```bash
# Test skill in current directory
测试skill ./my-skill/

# Test with custom parallel degree
测试skill ./my-skill/ --parallel 8

# Test with API keys
测试skill ./my-skill/ --env API_KEY=xxx,SECRET=yyy

# Output to specific file
测试skill ./my-skill/ --output ./reports/my-skill-report.md
```

## Advanced Usage

### CI/CD Integration

```yaml
# .github/workflows/skill-test.yml
name: Skill Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test skill
        run: |
          测试skill ./ --format json --output report.json
      - name: Check results
        run: |
          score=$(cat report.json | jq '.summary.overall_score')
          if [ "$score" -lt 60 ]; then
            echo "Skill quality check failed: $score"
            exit 1
          fi
```

### Batch Testing

```bash
# Test all skills in directory
for skill in ./skills/*/; do
    echo "Testing $skill..."
    测试skill "$skill" --output "./reports/$(basename $skill).md"
done

# Generate summary report
cat ./reports/*.md > ./reports/summary.md
```

### Custom Configuration

```yaml
# ~/.skill-certifier/config.yaml
parallel_degree: 8
timeout_per_test: 120

weights:
  hit_rate: 30
  success_rate: 25
  branch_coverage: 20
  tool_accuracy: 15
  error_handling: 10

thresholds:
  excellent: 85
  good: 70
```

## Example Output

### Summary

```
🔍 Testing skill: my-skill
   Parallel degree: 4
   Timeout: 60s

Phase 1: Safety Pre-screen...
   ✅ Passed (2 warnings)

Phase 2: Deep Analysis...
   Generated 45 test cases

Phase 3: Multi-dimensional Testing...
   Completed 45/45 tests
   Success rate: 88.9%

Phase 4: Qualitative Evaluation...
   Structure: ✅ Good
   Usefulness: ✅ Excellent
   Domain: ⚠️ Acceptable

Phase 5: Report Generation...
   Report saved to: report.md

==================================================
SUMMARY
==================================================
Overall Score: 87.5/100
Recommendation: ⭐⭐⭐⭐⭐ Excellent
```

### Report Excerpt

```markdown
## 3. Quantitative Metrics

### 3.1 Trigger Hit Rate (Weight: 25%)

**Score:** 23.5/25

| Test Type | Total | Passed | Rate |
|-----------|-------|--------|------|
| Exact Match | 10 | 10 | 100.0% |
| Fuzzy Match | 15 | 13 | 86.7% |
| Negative Test | 5 | 5 | 100.0% |

**Findings:**
- Excellent exact match performance
- Some fuzzy variations not recognized

### 3.2 Task Success Rate (Weight: 30%)

**Score:** 25.5/30

| Test Type | Total | Passed | Rate |
|-----------|-------|--------|------|
| Normal Path | 8 | 8 | 100.0% |
| Exception Handling | 4 | 3 | 75.0% |
| Boundary Cases | 3 | 2 | 66.7% |

**Findings:**
- Normal paths work perfectly
- Exception handling needs improvement
```

## Troubleshooting

### Test hangs

```bash
# Increase timeout
测试skill ./my-skill/ --timeout 120

# Reduce parallel degree
测试skill ./my-skill/ --parallel 2
```

### Low coverage

```bash
# Add custom test cases
# Edit ~/.skill-certifier/custom-tests.yaml

# Re-run with verbose output
测试skill ./my-skill/ --verbose
```

### Security warnings

```bash
# Review security issues
测试skill ./my-skill/ --skip-safety

# Then manually review safety report
```
