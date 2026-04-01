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
- 对于 I/O 密集型 Skill，考虑串行执行以降低并发压力

---

### 依赖未补齐导致批量失败

**现象：** 步骤 1.5 提示 `sandbox_incompatible`，跳过步骤 2.5 直接执行，导致大量案例失败。

**原因：** 目标 Skill 依赖环境变量、网络访问或浏览器能力，但测试前未补齐依赖。

**处理（步骤 2.5 依赖补齐）：**
1. 查看 `sandbox_check.setup_checklist`，逐项确认：
   - **环境变量**：设置所需 API Key / Token（如 `export ALI_1688_AK=xxx`）
   - **网络访问**：确认测试环境可访问外部网络，配置代理（如需）
   - **浏览器能力**：确认 OpenClaw browser tool 已配置或使用有头模式
2. 所有依赖就绪后重新运行测试
3. 若准备"测试专用配置"（mock API / 假数据），可在隔离环境中测试

**风险告知：** 依赖未补齐时继续执行，测试结果不可信，务必先完成步骤 2.5。

---

### 提示"无法在沙箱中测试"

**现象：** 流程在步骤 1.5 后提示目标 Skill 依赖环境变量、网络访问或浏览器能力，无法在沙箱中测试。

**原因：** `sandbox_checker.py` 检测到目标 Skill 需要沙箱外能力，执行时可能影响本地工作环境。

**处理：** 参见上方"依赖未补齐导致批量失败"。

---

### 早期终止（连续同因失败）

**现象：** 执行过程中，连续 3 个案例因相同原因失败（如"未触发"、"超时"、"Skill未被激活"）。

**原因：** 根本性问题导致所有案例无法正常执行，继续执行浪费资源。

**处理：**
1. Agent 应停止执行，调用 `--finalize` 生成当前报告
2. 查看 `summary.early_exit_recommended` 和 `early_exit_reason`
3. 根据根因修复后重新运行：
   - **skill_not_activated**：目标 Skill 未在 available_skills 中配置
   - **timeout**：提高 `--timeout` 或优化目标 Skill 性能
   - **spawn_unavailable**：sessions_spawn 不可用，检查 OpenClaw 环境
   - **dependency_missing**：返回步骤 2.5 补齐依赖
4. 修复后，`--prepare` 会自动跳过已完成案例，继续剩余测试

---

### 报告文件找不到

**现象：** 报告生成后找不到文件。

**说明：** `report_builder.py` 将报告输出到当前工作目录，文件名格式为：
```
<workspace>/.skill-tester/reports/test-report-<skill_name>-<timestamp>.md
```

**解决：** 在执行命令时指定输出路径：
```bash
python3 {baseDir}/scripts/report_builder.py results.json --output /path/to/report.md
```

---

### Agent 理解度分数为 0

**现象：** `agent_comprehension` 维度分数为 0，即使功能正常。

**可能原因：**
- 子 Agent 启动异常，输出为空（非 Skill 问题）
- 目标 Skill 的输出格式不明确，Agent 难以理解预期产物

**建议：** 在目标 SKILL.md 中明确描述预期输出格式和结果特征，便于 outcome_check 和 format_check 评估。

---

## 与 Skill 开发团队联系

若以上方案无法解决问题，请在 ClawHub 上提交 Issue，并附上：
1. 完整报告 JSON（`--output-json`）
2. 目标 Skill 的 `SKILL.md`（敏感信息脱敏）
3. 使用的命令和参数
