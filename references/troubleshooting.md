# 故障排除

## 常见问题

### 安全检查误报

**现象：** 安全检查将文档中的 `curl` 示例误判为危险模式。

**原因：** `SafetyChecker` 对 `curl` 使用正则全文匹配，不区分代码块与执行代码。

**处理：**
1. 检查报告中 `warnings` 列出的具体文件和行号
2. 对无害示例，可在安全注释中说明（不影响评分，仅为说明）
3. 若确属误报，可向本 Skill 提 Issue

---

### 测试案例生成质量差

**现象：** Agent 生成的测试案例过于单一，未覆盖触发词变体。

**原因：** 目标 Skill 的 `description` 过于简短，缺少示例触发词。

**建议：**
1. 在目标 SKILL.md 的 `description` 中至少列出 3 种触发词
2. 增加 `## 触发示例` 章节，明确列出预期触发语句
3. 重新运行测试，Agent 会据此生成更丰富的测试案例

---

### sessions_spawn 超时

**现象：** 测试案例执行时频繁报 `timeout`。

**调整方式：**
```
测试skill <skill_path> --timeout 120
```

**进一步排查：**
- 检查目标 Skill 依赖的外部 API 是否可用
- 对于 I/O 密集型 Skill，适当降低并行度：`--parallel 2`

---

### 报告文件找不到

**现象：** 报告生成后找不到文件。

**说明：** `report_builder.py` 将报告输出到当前工作目录，文件名格式为：
```
test-report-<skill_name>-<timestamp>.md
```

**解决：** 在执行命令时指定输出路径：
```bash
python3 {baseDir}/scripts/report_builder.py results.json --output /path/to/report.md
```

---

### Agent 理解度分数为 0

**现象：** `agent_comprehension` 维度分数为 0，即使功能正常。

**原因：** 目标 SKILL.md 没有明确描述执行步骤，导致"步骤遵循"测试无法生成。

**建议：** 在目标 SKILL.md 中添加 `## 执行步骤` 章节，用有序列表描述步骤。

---

## 与 Skill 开发团队联系

若以上方案无法解决问题，请在 ClawHub 上提交 Issue，并附上：
1. 完整报告 JSON（`--output-json`）
2. 目标 Skill 的 `SKILL.md`（敏感信息脱敏）
3. 使用的命令和参数
