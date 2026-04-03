#!/bin/bash

# AI Tutor · 一键安装脚本
# 支持 Claude Code 和 OpenClaw

REPO="Aolinkun/ai-tutor"
SKILL_NAME="ai-tutor"
BASE_URL="https://raw.githubusercontent.com/$REPO/main/bloom-mastery-tutor"

set -e

echo "🎓 AI Tutor 安装程序"
echo ""
echo "请选择安装目标："
echo "  1) Claude Code  (~/.claude/skills/)"
echo "  2) OpenClaw     (~/.openclaw/skills/)"
echo "  3) 两个都装"
echo ""
read -p "输入选项 [1/2/3]，直接回车默认选1：" choice
choice=${choice:-1}

install_to() {
  local dir="$1"
  local INSTALL_DIR="$dir/$SKILL_NAME"
  echo ""
  echo "📦 安装到 $INSTALL_DIR ..."
  mkdir -p "$INSTALL_DIR/references"
  curl -fsSL "$BASE_URL/SKILL.md" -o "$INSTALL_DIR/SKILL.md"
  curl -fsSL "$BASE_URL/references/theory.md" -o "$INSTALL_DIR/references/theory.md"
  curl -fsSL "$BASE_URL/references/difficulty-levels.md" -o "$INSTALL_DIR/references/difficulty-levels.md"
  echo "✅ 安装完成！"
}

case "$choice" in
  1)
    install_to "$HOME/.claude/skills"
    ;;
  2)
    install_to "$HOME/.openclaw/skills"
    ;;
  3)
    install_to "$HOME/.claude/skills"
    install_to "$HOME/.openclaw/skills"
    ;;
  *)
    echo "❌ 无效选项，退出"
    exit 1
    ;;
esac

echo ""
echo "使用方法：在 Claude Code 或 OpenClaw 中说「我想学 XXX」即可使用"
