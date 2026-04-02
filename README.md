# 🎓 AI Tutor · 苏格拉底学习导师

基于 Benjamin Bloom 的 **Two Sigma 掌握学习法**，让 Claude 变成你的专属一对一导师。

> 研究表明：一对一辅导 + 掌握学习法，可让学生超越 98% 的同龄人。  
> 现在用 AI，人人都能用上这种学习方式。

## ⚡ 一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/Aolinkun/ai-tutor/main/install.sh | bash
```

## 🚀 使用方法

安装后，在 Claude Code 中说：

```
我想学维特根斯坦的逻辑哲学论
我想学傅里叶变换
我想学 Rust 的所有权系统
```

Claude 会自动启动苏格拉底式导师模式，主动提问、实时调整难度，并在当前目录创建学习文件记录进度。

## 🧠 这个技能做什么？

- **AI 主动提问**，而不是被动回答你——这才是高效学习的正确机制
- **根据你的回答实时调整难度**，正确率 ≥ 80% 才推进下一阶段
- **学习记录存成文件**，在 Claude Code 中跨对话持久保存进度
- 支持任何学科：哲学、编程、数学、历史……

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
