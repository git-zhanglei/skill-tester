---
name: skill-certifier
description: "OpenClaw skill测试和认证框架V2。新流程：1)内置skill test验证 2)生成测试案例集 3)用户确认 4)并行执行 5)生成报告。触发词：'测试skill', 'skill测试', '评估skill'"
---

# Skill Certifier V2

OpenClaw skill 测试和认证框架，采用全新的测试流程。

## 新流程概述

```
┌─────────────────────────────────────────────────────────────┐
│                    Skill Certifier V2                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  阶段 0: 内置 Skill Test 验证                               │
│  ├─ 安全检查（恶意代码、凭证泄露）                          │
│  ├─ 结构评审（SKILL.md 格式）                               │
│  ├─ 实用性评审（清晰度、可操作性）                          │
│  └─ 输出：初次扫描结论                                      │
│                                                             │
│  阶段 1: 生成测试案例集                                     │
│  ├─ 深度分析 SKILL.md                                       │
│  ├─ 提取触发词、工具依赖                                    │
│  ├─ 生成多维度测试案例                                      │
│  └─ 输出：保存到本地 JSON 文件                              │
│                                                             │
│  阶段 2: 用户确认                                           │
│  ├─ 展示测试案例集概览                                      │
│  ├─ 显示测试用例详情                                        │
│  └─ 等待用户确认开始执行                                    │
│                                                             │
│  阶段 3: 并行执行测试                                       │
│  ├─ 创建子 agent                                            │
│  ├─ 并行执行每条测试案例                                    │
│  ├─ 实时标记完成状态                                        │
│  └─ 更新测试案例集                                          │
│                                                             │
│  阶段 4: 生成最终报告                                       │
│  ├─ 基于完成的测试案例集                                    │
│  ├─ 计算各维度评分                                          │
│  └─ 输出：Markdown 报告                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

**1分钟上手：**

```bash
# 基础测试（交互式）
测试skill ~/skills/my-skill/

# 自动测试（CI/CD推荐）
测试skill ~/skills/my-skill/ --yes --output-json

# 完整认证（生成所有报告）
测试skill ~/skills/my-skill/ --yes --output-json --visual
```

**完整测试流程：**
```
测试skill ~/skills/my-skill/
```

**使用已有的测试案例集：**
```
测试skill ~/skills/my-skill/ --test-cases ./test-cases-my-skill-20240319.json
```

**调整并行度：**
```
测试skill ~/skills/my-skill/ --parallel 8
```

**自动确认（不询问）：**
```
测试skill ~/skills/my-skill/ --yes
```

## 详细流程

### 阶段 0: 内置 Skill Test 验证

使用嵌入的 Skill Test 逻辑进行初步验证：

- **安全检查**：恶意代码模式、凭证泄露、个人数据暴露
- **结构评审**：SKILL.md 格式、长度、渐进式披露
- **实用性评审**：清晰度、触发词、可操作性
- **领域评审**：工具引用、API 指导、错误处理
- **兼容性检查**：OpenClaw版本要求、依赖skill可用性

**输出：**
- 安全状态：通过/警告/失败
- 可用性：优秀/良好/可接受/需改进
- 兼容性：兼容版本范围、依赖状态
- 初次扫描结论
- 优化建议

### 阶段 1: 生成测试案例集

基于初次扫描结果，生成针对不同维度的测试案例：

| 维度 | 测试类型 | 说明 | 覆盖目标 |
|------|----------|------|----------|
| 命中率 | 精确匹配、模糊匹配、负面测试 | 验证触发词准确性 | ≥90% |
| 成功率 | 正常场景、带参数 | 验证任务完成能力 | ≥80% |
| 边界 | 空输入、超长输入、特殊字符 | 验证边界处理 | 100% |
| 异常 | 无效路径、错误输入、权限不足 | 验证异常处理 | ≥70% |
| 性能 | 响应时间、资源占用 | 验证执行效率 | 基准对比 |

**覆盖率计算：**
```
覆盖率 = 已测试的功能点 / SKILL.md中声明的功能点 × 100%
```

**输出：**
- 保存为 JSON 文件：`test-cases-{skill-name}-{timestamp}.json`
- 包含测试用例详情、状态、元数据
- 覆盖率分析报告

### 阶段 2: 用户确认

展示测试案例集信息后，询问用户：

```
❓ 是否开始执行测试？
   [Y] 是 - 开始执行测试
   [N] 否 - 退出，稍后可以使用 --test-cases 参数重新执行
   [S] 显示完整测试案例集

请输入选择 [Y/N/S]:
```

**选项说明：**
- **Y**: 确认并开始执行测试
- **N**: 取消测试，保存测试案例集供后续使用
- **S**: 显示完整的测试案例集详情

**自动确认模式：**
添加 `--yes` 或 `-y` 参数可跳过确认：
```
测试skill ~/skills/my-skill/ --yes
```

### 阶段 3: 并行执行测试

使用 ThreadPoolExecutor 并行执行：
- 创建子 agent（通过 sessions_spawn）
- 并行执行每条测试案例
- 实时更新测试案例状态
- 标记完成状态（pending → running → completed）
- 保存结果到测试案例集文件

**执行隔离机制：**
每个子 agent 在独立会话中运行，避免相互干扰：
- 独立的文件系统命名空间
- 独立的环境变量
- 独立的会话历史

**有状态 skill 的注意事项：**
如果 skill 涉及全局状态（如修改配置文件、数据库操作），建议：
1. 使用 `--parallel 1` 串行执行
2. 或确保 skill 内部有并发安全机制

### 阶段 4: 生成最终报告

基于完成的测试案例集生成报告：
- 安全评分
- 触发命中率
- 任务成功率
- 综合评分（0-100）
- 评级（⭐⭐⭐⭐⭐）
- 详细结果（按维度分组）
- 失败详情
- 优化建议

**输出：**
- Markdown 报告：`test-report-{skill-name}-{timestamp}.md`
- JSON 报告：`test-report-{skill-name}-{timestamp}.json`（便于CI/CD集成）

**JSON报告格式：**
```json
{
  "version": "2.0",
  "skill_name": "my-skill",
  "generated_at": "2024-03-19T10:35:00",
  "summary": {
    "safety_score": 100,
    "hit_rate": 95.0,
    "success_rate": 87.5,
    "overall_score": 92.5,
    "rating": "⭐⭐⭐⭐⭐",
    "grade": "excellent",
    "passed": true
  },
  "details": { "by_dimension": { ... } },
  "recommendations": [ ... ]
}
```

## 测试案例集格式

```json
{
  "version": "2.0",
  "generated_at": "2024-03-19T10:30:00",
  "skill_name": "my-skill",
  "total": 10,
  "cases": [
    {
      "id": "hit_exact_0",
      "dimension": "hit_rate",
      "type": "exact_match",
      "input": "测试skill",
      "expected": "activate",
      "description": "精确触发: 测试skill",
      "weight": 1.0,
      "status": "completed",
      "result": {
        "status": "passed",
        "output": "...",
        "duration": 1.5
      },
      "completed_at": "2024-03-19T10:31:00"
    }
  ],
  "execution": {
    "status": "completed",
    "progress": {
      "total": 10,
      "completed": 10,
      "passed": 8,
      "failed": 2
    }
  }
}
```

## 核心指标

### 1. 安全评分
- ✅ 通过：无安全问题
- ⚠️ 警告：有警告但可接受
- ❌ 失败：发现严重安全问题，测试停止

### 2. 触发命中率
测试触发词是否能正确激活 skill：
- 精确匹配测试
- 模糊匹配测试
- 负面测试（不应激活的输入）

### 3. 任务成功率
真实执行测试，验证 skill 是否能正确完成任务：
- 正常场景测试
- 异常处理测试
- 边界情况测试

### 4. 综合评分

**评分算法（加权计算）：**

```
综合评分 = 安全评分 × 25% + 触发命中率 × 25% + 任务成功率 × 50%
```

**各维度计算方式：**

| 维度 | 计算方式 | 权重 | 说明 |
|------|----------|------|------|
| 安全评分 | 通过=100, 警告=70, 失败=0 | 25% | 安全是底线 |
| 触发命中率 | (精确匹配通过数 + 模糊匹配通过数) / 总匹配测试数 × 100 | 25% | 激活准确性 |
| 任务成功率 | 成功测试数 / 总执行测试数 × 100 | 50% | 核心能力 |

**评分等级：**
- ⭐⭐⭐⭐⭐ 优秀 (80-100)
- ⭐⭐⭐⭐ 良好 (60-79)
- ⭐⭐⭐ 可接受 (40-59)
- ⭐⭐ 需要改进 (0-39)
- ⭐ 不合格 (安全失败直接判定)

**特殊规则：**
- 安全评分为0时，综合评分直接为0（一票否决）
- 任何维度低于40分，最高评级不超过⭐⭐⭐

## 配置

**默认配置：**
- 并行度：4
- 每个测试超时：60秒
- 最大测试用例数：20
- 自动保存间隔：每完成5个测试用例

**命令行参数：**
- `--parallel, -p`：并行度
- `--timeout, -t`：超时时间
- `--test-cases, -c`：使用已有的测试案例集
- `--skip-skill-test`：跳过内置 skill test
- `--resume, -r`：从断点继续执行（自动检测未完成的测试案例集）
- `--output-json`：同时输出JSON格式报告
- `--debug, -d`：交互式调试模式（失败时暂停）
- `--custom-tests`：加载自定义测试用例文件
- `--compare`：与历史报告对比
- `--visual`：生成可视化HTML报告
- `--batch`：批量测试多个skill（传入目录）
- `--sandbox`：启用沙箱隔离模式
- `--benchmark`：生成性能基准报告

## 最佳实践

1. **开发阶段**
   - 使用 `--debug` 模式快速定位问题
   - 添加 `custom-tests.yaml` 覆盖特殊场景
   - 定期使用 `--benchmark` 跟踪性能变化

2. **CI/CD集成**
   - 使用 `--yes` 实现自动化
   - 设置最低分数门槛（推荐≥70）
   - 保存JSON报告用于趋势分析

3. **发布前检查**
   - 确保所有测试通过
   - 生成可视化报告供用户查看
   - 对比历史版本确认无退化

4. **维护阶段**
   - 保存测试案例集用于回归测试
   - 定期使用 `--batch` 测试所有skill
   - 关注社区基准库的更新

## 与 V1 的区别

| 特性 | V1 | V2 |
|------|-----|-----|
| 流程 | 5阶段连续执行 | 分阶段，用户确认 |
| 测试案例 | 自动生成直接执行 | 生成后保存，用户确认 |
| 状态跟踪 | 内存中 | 持久化到 JSON |
| 可重复性 | 低 | 高（保存测试集）|
| 透明度 | 中 | 高（可审查测试用例）|
| 错误恢复 | 不支持 | 断点续测 |
| 报告格式 | Markdown | Markdown + JSON + HTML |
| CI/CD | 困难 | 原生支持 |
| 调试 | 无 | 交互式调试 |
| 批量测试 | 不支持 | 支持 |
| 沙箱 | 无 | 支持 |

## 示例：完整认证流程

**场景**：认证一个天气查询skill

```bash
# Step 1: 生成测试案例集（阶段0-1）
测试skill ~/skills/weather/
# → 生成 test-cases-weather-20240319.json

# Step 2: 查看测试案例（可选）
# 输入 S 查看完整测试案例集

# Step 3: 确认并执行（阶段2-3）
# 输入 Y 开始执行

# Step 4: 查看报告（阶段4）
# → test-report-weather-20240319.md
# → test-report-weather-20240319.json
```

**示例报告摘要：**
```
╔══════════════════════════════════════════════════╗
║         Weather Skill 认证报告                    ║
╠══════════════════════════════════════════════════╣
║ 安全评分:    100/100  ✅                          ║
║ 触发命中率:  95.0%    ✅                          ║
║ 任务成功率:  90.0%    ✅                          ║
║ 综合评分:    93.8/100 ⭐⭐⭐⭐⭐                   ║
║ 评级:        优秀 (Certified)                     ║
╠══════════════════════════════════════════════════╣
║ 测试用例:    20个                                 ║
║ 通过:        18个                                 ║
║ 失败:        2个（边界情况）                      ║
╚══════════════════════════════════════════════════╝
```

## 故障排除

**测试案例集生成失败：**
- 检查 SKILL.md 是否存在
- 检查是否有可提取的触发词

**执行时连接失败：**
- 确保在 OpenClaw 环境中运行
- 检查 sessions_spawn 是否可用

**测试用例执行超时：**
- 增加 `--timeout` 参数
- 检查 skill 是否有长时间运行的操作

**执行中断恢复：**
如果阶段3执行中断，使用 `--resume` 参数自动恢复：
```bash
测试skill ~/skills/my-skill/ --resume
```

**自动恢复机制：**
1. 自动扫描当前目录下未完成的测试案例集文件
2. 识别状态为 `pending` 或 `running` 的测试用例
3. 重置 `running` 状态的用例为 `pending`
4. 继续执行剩余测试

**手动指定恢复：**
```bash
测试skill ~/skills/my-skill/ --test-cases ./test-cases-my-skill-20240319.json --resume
```

**交互式调试模式：**
当测试失败时自动暂停，允许人工检查：
```bash
测试skill ~/skills/my-skill/ --debug
```

调试模式下：
- 失败时显示详细上下文
- 提供选项：重试/跳过/查看日志/进入交互式shell
- 支持单步执行

**自定义测试用例：**
创建 `custom-tests.yaml` 添加自己的测试：
```yaml
test_cases:
  - id: custom_001
    dimension: custom
    input: "我的特殊测试输入"
    expected: "期望的输出模式"
    description: "测试特定场景"
```

运行：
```bash
测试skill ~/skills/my-skill/ --custom-tests ./custom-tests.yaml
```

**版本对比：**
对比当前版本与历史认证结果：
```bash
测试skill ~/skills/my-skill/ --compare ./test-report-v1.0.0.json
```

对比报告包含：
- 评分变化趋势
- 新增/修复的问题
- 性能变化分析

**可视化报告：**
生成HTML格式的交互式报告：
```bash
测试skill ~/skills/my-skill/ --visual
```

HTML报告包含：
- 评分仪表盘
- 测试用例通过率图表
- 失败详情折叠面板
- 可导出的PDF版本

## 社区发布标准

**可发布到社区的最低标准：**

| 指标 | 最低要求 | 推荐标准 |
|------|----------|----------|
| 安全评分 | 100（无警告） | 100 |
| 触发命中率 | ≥85% | ≥95% |
| 任务成功率 | ≥75% | ≥90% |
| 综合评分 | ≥70（⭐⭐⭐⭐） | ≥85（⭐⭐⭐⭐⭐） |
| 测试覆盖率 | ≥80% | ≥95% |
| 文档完整性 | 必须包含：快速开始、故障排除 | 完整示例、最佳实践 |

**认证徽章：**
- 🏆 **Certified**: 综合评分 ≥90
- ✅ **Verified**: 综合评分 ≥70
- 🔄 **Beta**: 综合评分 <70 或测试覆盖率 <80

## CI/CD 集成

**GitHub Actions 示例：**

```yaml
name: Skill Certification
on: [push, pull_request]
jobs:
  certify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup OpenClaw
        uses: openclaw/setup-action@v1
      - name: Run Certification
        run: |
          测试skill ./ --yes --output-json
      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: certification-report
          path: test-report-*.json
      - name: Check Standards
        run: |
          SCORE=$(cat test-report-*.json | jq '.summary.overall_score')
          if (( $(echo "$SCORE < 70" | bc -l) )); then
            echo "❌ 未达到社区发布标准（需要≥70分）"
            exit 1
          fi
          echo "✅ 通过认证，评分: $SCORE"
```

**GitLab CI 示例：**

```yaml
certify:
  script:
    - 测试skill ./ --yes --output-json
    - |
      SCORE=$(cat test-report-*.json | jq '.summary.overall_score')
      if (( $(echo "$SCORE < 70" | bc -l) )); then
        echo "未达到社区发布标准"
        exit 1
      fi
  artifacts:
    paths:
      - test-report-*.json
      - test-report-*.md
```

## 批量测试

同时测试多个skill：
```bash
测试skill ~/skills/ --batch
```

批量模式输出：
- 汇总报告：所有skill的评分对比
- 排行榜：按综合评分排序
- 详细报告：每个skill的独立报告

## 沙箱隔离模式

在隔离环境中运行测试，保护真实环境：
```bash
测试skill ~/skills/my-skill/ --sandbox
```

沙箱特性：
- 临时文件系统（测试后自动清理）
- 网络访问限制（可选）
- 资源使用限制（CPU/内存）
- 敏感操作拦截

## 性能基准

生成性能基准报告，与社区平均对比：
```bash
测试skill ~/skills/my-skill/ --benchmark
```

基准报告包含：
- 响应时间分布（P50/P90/P99）
- 资源占用分析
- 与同类skill对比
- 优化建议

**社区基准库：**
定期更新的skill性能数据库，用于横向对比。

---

*Skill Certifier V2 - 更透明、更可控的测试流程*