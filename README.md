# AI Tutor V5 · 掌握学习教练

基于 Benjamin S. Bloom 掌握学习理论的 AI 学习系统，帮助你形成**可验证、可保持、可迁移**的能力。

[![Tests](https://img.shields.io/badge/tests-44%2F44%20passing-success)]()
[![Version](https://img.shields.io/badge/version-5.0-blue)]()
[![Protocol](https://img.shields.io/badge/protocol-schema%203-blue)]()

---

## 快速开始

### 三个核心场景

```
1️⃣ 学会一个东西    → 我想学会条件概率 / Python 装饰器 / 如何读懂资产负债表
2️⃣ 解决具体问题    → 我的代码总是报错 / 不知道怎么分析这个商业案例
3️⃣ 复习与检测      → 复习上周学的概念 / 检测一下我是否真的掌握了
```

### 5 分钟上手

**场景 1：系统学习**
```
你：我想学会 Python 装饰器
AI：先给一个诊断任务判断起点 → 讲解缺口 → 写代码练习 → 新题检测 → 
    证据反馈 → 24 小时后复习 → 在实际项目中应用 → 掌握
```

**场景 2：解决问题**
```
你：我不理解为什么我的递归函数会栈溢出
AI：定位缺口（递归终止条件）→ 补最少知识 → 回到原问题 → 修复代码 → 验证通过
```

**场景 3：复习**
```
你：复习上次学的条件概率
AI：读取课程状态 → 间隔检测（新题，不同场景）→ 更新保持/迁移证据
```

---

## 核心特性

### ✅ 真正的掌握学习

不是「听懂了」就算，而是：
- **准确性** + **推理** + **迁移** + **独立性** 四维评分
- 24 小时后换题检测**延迟保持**
- 新场景验证**跨情境迁移**

### ✅ 可追溯证据链

```
assessments.jsonl  → 每次评估记录（题目、作答、评分、提示等级）
state.json        → 当前掌握状态（由评估日志派生）
sources.jsonl     → 教学资料来源（法规、论文、财报等）
```

### ✅ 跨会话续学

```bash
# 上次学到一半
python3 scripts/tutor.py courses
# → 显示：概率基础 | 更新于 2026-09-10 | 活动：practice

# 恢复学习（AI 自动读取状态）
→ 从上次的 checkpoint 继续，不重做已完成内容
```

### ✅ 数据安全

- **原子写入**：临时文件 + 替换，防止损坏
- **并发保护**：文件锁 + stale lock 检测
- **版本隔离**：V5 不覆盖 V4 数据
- **软链接防御**：拒绝通过软链接修改外部数据

---

## 安装与配置

### 环境要求

- Python 3.8+（仅标准库，无第三方依赖）
- 支持 Skill 的 AI 环境（Claude Code、Codex 等）

### 作为 Skill 使用

```bash
# 1. 克隆到本地
git clone <repo-url> ai-tutor-v5

# 2. 配置数据根目录（可选，默认 ~/Documents/AI-Tutor-V5-学习记录/）
python3 -B scripts/tutor.py configure-root --data-root "/绝对路径/学习记录"

# 3. 在 AI 对话中调用
$ai-tutor-v5
# 或直接说：我想学会 XXX
```

### 命令行使用

```bash
# 查看数据根目录
python3 -B scripts/tutor.py root

# 列出所有课程
python3 -B scripts/tutor.py courses

# 创建新课程
python3 -B scripts/tutor.py init "课程目录" \
  --title "概率基础" \
  --slug probability \
  --storage progress \
  --authorize-progress

# 验证课程数据
python3 -B scripts/tutor.py validate "课程目录"

# 恢复中断写入
python3 -B scripts/tutor.py sync "课程目录"
```

---

## 工作原理

### 掌握学习循环

```
1. 定义可观察成果 → 什么算达标
2. 判断真实起点   → 有区分度的诊断任务
3. 针对缺口教学   → 只讲当前需要的
4. 主动练习       → 预测、解释、比较、产出
5. 新题检测       → 未泄露答案的等价任务
6. 纠正与复测     → 定位错误 → 换角度纠正 → 新题再测
7. 证据推进       → 独立通过 → 延迟保持 → 跨场景迁移 → 掌握
```

### 状态升级路径

```
introduced      → 刚接触，尚未独立完成
   ↓
assisted        → 在提示/支架下完成
   ↓
provisional     → 当前独立通过（可进入下一单元）
   ↓
retained        → 24 小时后换题仍能独立完成
   ↓
transferred     → 在新场景中独立应用
   ↓
mastered        → 同时具备 retained + transferred 证据
```

### 评分标准（0-2 分）

| 维度 | 0 分 | 1 分 | 2 分 |
|---|---|---|---|
| **accuracy** | 关键错误 | 主方向对，有遗漏 | 关系准确 |
| **reasoning** | 无依据或跳步 | 部分理由成立 | 依据清晰 |
| **transfer** | 未检测 | 相近情境应用 | 新情境独立应用 |
| **independence** | 依赖答案/示范 | 有过程支持 | 无提示完成 |

**通过条件**：总分 ≥6、accuracy=2、无关键错误、符合成功标准

---

## 目录结构

```
ai-tutor-v5/
├── SKILL.md                       # 主入口（53 行）
├── README.md                      # 本文件
├── references/                    # 按需加载的规则文件
│   ├── 工作流_workflows.md        # 四模式工作流（115 行）
│   ├── 评估规则_assessment.md     # 四维评分与证据（55 行）
│   ├── 数据协议_protocol.md       # 状态与日志格式（140 行）
│   ├── 笔记与存储_storage.md      # 三档存储与恢复（87 行）
│   └── 资料与来源_sources.md      # 资料核验规则（80 行）
├── scripts/                       # Python 工具链
│   ├── tutor.py                   # 命令行入口
│   └── tutorlib.py                # 核心逻辑（699 行）
├── assets/templates/              # JSON 与 Markdown 模板
│   ├── state.json
│   ├── assessment.json
│   ├── source.json
│   ├── insight.json
│   └── 学习记录_session.md
└── tests/                         # 测试套件
    ├── test_runtime.py            # 44 个单元测试
    └── 行为场景_eval-cases.json   # 28 个行为场景
```

---

## 三档存储模式

### off（默认）

- 无课程写入
- 适合临时解释和练习

### progress（进度档）

```bash
--storage progress --authorize-progress
```

- 保存状态、评估证据、恢复点
- 简短 session 记录
- 适合系统学习

### full（完整档）

```bash
--storage full --authorize-progress --authorize-full
```

- 在 progress 基础上保存完整学习对话
- 原文与摘要分区
- 适合教学研究或需要完整档案的场景

---

## 实例

### 实例 1：学会条件概率

**第 1 轮：诊断起点**
```
AI：有 100 人，60 人喝咖啡，40 人加班，其中 30 人既喝咖啡又加班。
    随机选一个喝咖啡的人，他加班的概率是多少？

你：30/60 = 0.5

AI：✅ 正确。你已经理解了条件概率的核心：在「已知喝咖啡」这个条件下，
    样本空间缩小到 60 人，其中 30 人加班。
    
    下一题（无提示）：某疾病患病率 1%，检测准确率 95%。
    检测阳性的人，真正患病的概率是多少？
```

**第 2 轮：发现误解**
```
你：95%

AI：❌ 这里混淆了 P(阳性|患病) 和 P(患病|阳性)。
    
    让我们用反例：假设 10000 人...
    [纠正后]
    
    新题：某公司...（结构相同，数字不同的场景）
```

**第 3 轮：独立通过**
```
你：[正确推理过程]

AI：✅ 独立通过。当前单元达标（provisional）。
    24 小时后我们换个新题检测保持。
    
    [保存评估日志]
```

**24 小时后：保持检测**
```
AI：[完全不同的医疗场景，但底层结构相同]

你：[独立完成]

AI：✅ 延迟保持验证（retained）。
    下次我们在决策树场景中应用条件概率，检测迁移。
```

### 实例 2：解决递归问题

```
你：我的递归函数总是报错 "RecursionError: maximum recursion depth exceeded"

AI：[定位缺口] 你的递归有终止条件吗？可以给我看看代码吗？

你：
def factorial(n):
    return n * factorial(n-1)

AI：找到问题了。你的递归缺少终止条件，会无限递归直到栈溢出。
    
    递归需要两个要素：
    1. 终止条件（base case）
    2. 递归调用（recursive case）
    
    修复版本：
    def factorial(n):
        if n <= 1:        # 终止条件
            return 1
        return n * factorial(n-1)
    
    练习：现在写一个递归函数计算斐波那契数列 fib(n)

你：
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

AI：✅ 正确！终止条件和递归逻辑都对。问题解决了吗？

你：解决了，谢谢

AI：[记录：solve 模式，补充了「递归终止条件」知识，验证了应用]
```

---

## 与其他版本对比

| 特性 | V5（本版本） | 单文件 V4 | 其他学习助手 |
|---|---|---|---|
| 掌握学习机制 | ✅ 完整 | ✅ 简化 | ⚠️ 少数有 |
| 延迟保持检测 | ✅ 24h+ | ✅ | ❌ 几乎没有 |
| 跨场景迁移 | ✅ | ✅ | ❌ |
| 本地数据存储 | ✅ JSONL | ❌ | ⚠️ 部分有 |
| 跨会话续学 | ✅ | ❌ | ⚠️ 依赖平台 |
| 并发写入保护 | ✅ | N/A | ❌ |
| 完整测试 | ✅ 44 tests | ❌ | ❌ |
| 依赖项 | Python 标准库 | 无 | 不定 |

**选择建议**：
- 需要**长期系统学习** → V5
- 需要**临时快速学习** → 单文件 V4（`AI_TUTOR.md`）
- 需要**极简对话** → 考虑其他轻量级方案

---

## 开发

### 运行测试

```bash
python3 -B scripts/validate-package.py
# → Ran 44 tests in 2.3s
# → OK
```

### 测试覆盖

- ✅ 四维评分计算
- ✅ 状态升级逻辑（introduced → mastered）
- ✅ 保持与迁移验证（24h 间隔、新场景）
- ✅ 并发写入冲突处理
- ✅ 损坏数据检测与恢复
- ✅ 软链接安全防御
- ✅ 时区与时间戳验证
- ✅ JSON 格式与字段完整性

### 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 运行测试确保通过
4. 提交更改 (`git commit -m 'Add amazing feature'`)
5. 推送到分支 (`git push origin feature/amazing-feature`)
6. 创建 Pull Request

---

## 设计理念

### 为什么是掌握学习？

> **Two Sigma Problem**: One-to-one tutoring produces learning outcomes two standard deviations better than conventional classroom instruction.  
> — Benjamin S. Bloom (1984)

AI 可以提供接近一对一辅导的个别化支持：
- ✅ 实时诊断起点
- ✅ 针对缺口教学
- ✅ 等待真实作答
- ✅ 纠正后立即复测
- ✅ 按证据调整难度

### 为什么需要延迟保持和迁移？

认知科学研究表明：
- **即时表现 ≠ 长期记忆**（遗忘曲线）
- **原场景成功 ≠ 可迁移能力**（情境依赖）

只有同时验证：
1. 延迟后仍能独立完成（retained）
2. 新场景中能独立应用（transferred）

才能说真正「掌握」。

### 为什么需要本地存储？

对话历史 ≠ 学习档案：
- 对话会被清理、总结、遗忘
- 证据链需要**完整、可追溯、不可篡改**
- 状态派生需要**从原始日志重建，不靠主观判断**

---

## FAQ

### Q: 必须用命令行工具吗？

A: 不是。工具只负责数据完整性验证，AI 也可以直接写 JSON/JSONL。但工具提供：
- 原子写入保护
- 并发锁
- 自动计算 mastery 状态
- 损坏恢复

建议在有文件权限的环境使用工具。

### Q: 可以不保存数据吗？

A: 可以。默认 `storage_mode=off`，所有教学在对话中完成。适合临时学习和快速解释。

### Q: V4 数据能迁移到 V5 吗？

A: 不能。V5 与 V4 协议不兼容，且 V5 不会读取或改写 V4 数据。建议新课程使用 V5，旧课程保持原样。

### Q: 支持哪些 AI 平台？

A: 理论上支持所有能执行 Skill、读取文件、运行 Python 的环境。已测试：
- ✅ Claude Code
- ✅ Codex
- ⚠️ 其他平台需自行测试

### Q: 如何备份数据？

A: 数据根目录是独立的，直接复制或打包：
```bash
tar -czf backup-$(date +%Y%m%d).tar.gz ~/Documents/AI-Tutor-V5-学习记录/
```

---

## 许可证

MIT License

---

## 致谢

- Benjamin S. Bloom - 掌握学习理论（1968, 1984）
- 所有参与测试和反馈的用户

---

**版本**：5.0  
**协议**：Schema 3  
**最后更新**：2026-09-12
