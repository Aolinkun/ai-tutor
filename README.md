# 🎓 Bloom Mastery Tutor · AI 苏格拉底学习导师

基于 Benjamin Bloom 的 **Two Sigma 掌握学习法**，让 Claude 变成你的专属一对一导师。

> 研究表明：一对一辅导 + 掌握学习法，可让学生超越 98% 的同龄人。  
> 现在用 AI，人人都能用上这种学习方式。

## 🧠 这个 Skill 做什么？

- **AI 主动提问**，而不是被动回答你——这才是高效学习的正确机制
- **根据你的回答实时调整难度**，正确率 ≥ 80% 才推进下一阶段
- **学习记录存成文件**，在 Claude Code 中跨对话持久保存
- 支持任何学科：哲学、编程、数学、历史……

## 📦 安装方法

### 方法一：安装 `.skill` 文件（推荐）

1. 下载本仓库的 `bloom-mastery-tutor.skill` 文件
2. 在 Claude Code 中运行：

```bash
claude skills install bloom-mastery-tutor.skill
```

### 方法二：手动复制到 Claude Code 项目

将 `bloom-mastery-tutor/` 文件夹复制到你的项目的 `.claude/skills/` 目录下：

```
your-project/
└── .claude/
    └── skills/
        └── bloom-mastery-tutor/
            ├── SKILL.md
            └── references/
                ├── theory.md
                └── difficulty-levels.md
```

### 方法三：普通对话框（无需安装）

直接复制以下提示词，粘贴到任意 AI 对话框：

```
你是我的苏格拉底式学习导师，请严格按照 Bloom 掌握学习法来帮我学习。

【你的角色】
- 你是主动提问者，不是被动回答者
- 你根据我的回答实时调整难度

【学习流程】
1. 先问我想学什么，以及我目前的了解程度
2. 生成 2-3 个诊断性问题，判断我真实的知识边界
3. 根据回答：正确率 ≥ 80% → 进入更难内容；< 80% → 当前层级巩固
4. 每轮结束告诉我：当前掌握状态 + 下一步计划

【禁止行为】
- 不要给大段知识讲解，除非我答错需要解释
- 不要问「你有什么问题吗？」——你来主导提问
- 不要一次超过 3 个问题

请问我：你想学什么？你现在对它了解多少？
```

## 🚀 使用示例

安装后，在 Claude Code 中直接说：

- `帮我学维特根斯坦的逻辑哲学论`
- `我想搞懂傅里叶变换`
- `帮我学 Rust 的所有权系统`

Claude 会自动启动苏格拉底式导师模式，并在你的项目目录下创建学习文件记录进度。

## 📁 文件结构

```
bloom-mastery-tutor/
├── SKILL.md                        # 主技能文件
└── references/
    ├── theory.md                   # Bloom Two Sigma 理论背景
    └── difficulty-levels.md        # 各学科难度层级参考
```

## 📖 理论背景

Benjamin Bloom（1984）在《The 2 Sigma Problem》中发现：

| 学习方式 | 效果 |
|---------|------|
| 传统课堂（1对30） | 基准 |
| 掌握学习法 | 超越 84% 的学生（+1σ） |
| 一对一辅导 + 掌握学习法 | 超越 **98%** 的学生（+2σ） |

AI 是人类历史上第一次能以极低成本大规模复制这种体验的技术。

## License

MIT
