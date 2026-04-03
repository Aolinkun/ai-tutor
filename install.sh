#!/bin/bash

# AI Tutor · 一键安装脚本

REPO="Aolinkun/ai-tutor"
SKILL_NAME="ai-tutor"
INSTALL_DIR="$HOME/.claude/skills/$SKILL_NAME"
BASE_URL="https://raw.githubusercontent.com/$REPO/main/bloom-mastery-tutor"

echo "🎓 正在安装 AI Tutor..."

mkdir -p "$INSTALL_DIR/references"

curl -fsSL "$BASE_URL/SKILL.md" -o "$INSTALL_DIR/SKILL.md" || { echo "❌ 下载失败，请稍后重试"; exit 1; }
curl -fsSL "$BASE_URL/references/theory.md" -o "$INSTALL_DIR/references/theory.md" || { echo "❌ 下载失败，请稍后重试"; exit 1; }
curl -fsSL "$BASE_URL/references/difficulty-levels.md" -o "$INSTALL_DIR/references/difficulty-levels.md" || { echo "❌ 下载失败，请稍后重试"; exit 1; }

echo ""
echo "✅ 安装完成！路径：$INSTALL_DIR"
echo "在 Claude Code 中说「我想学 XXX」即可使用"
echo ""
grep "^# Version" "$INSTALL_DIR/SKILL.md"
