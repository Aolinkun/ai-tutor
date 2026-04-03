#!/bin/bash

# AI Tutor · 一键安装脚本
# 支持 Claude Code 和 OpenClaw

REPO="Aolinkun/ai-tutor"
SKILL_NAME="ai-tutor"
BASE_URL="https://raw.githubusercontent.com/$REPO/main/bloom-mastery-tutor"

echo "🎓 AI Tutor 安装程序"
echo ""
echo "请选择安装目标："
echo "  1) Claude Code  (~/.claude/skills/)  [默认]"
echo "  2) OpenClaw     (~/.openclaw/skills/)"
echo "  3) 两个都装"
echo ""

read -p "输入选项 [1/2/3]，直接回车默认选1：" choice < /dev/tty
choice=${choice:-1}

install_to() {
  local INSTALL_DIR="$1/$SKILL_NAME"
  echo ""
  echo "📦 安装到 $INSTALL_DIR ..."
  mkdir -p "$INSTALL_DIR/references"

  curl -fsSL "$BASE_URL/SKILL.md" -o "$INSTALL_DIR/SKILL.md" || { echo "❌ 下载 SKILL.md 失败"; exit 1; }
  curl -fsSL "$BASE_URL/references/theory.md" -o "$INSTALL_DIR/references/theory.md" || { echo "❌ 下载 theory.md 失败"; exit 1; }
  curl -fsSL "$BASE_URL/references/difficulty-levels.md" -o "$INSTALL_DIR/references/difficulty-levels.md" || { echo "❌ 下载 difficulty-levels.md 失败"; exit 1; }

  echo "✅ 安装完成！路径：$INSTALL_DIR"
}

case "$choice" in
  1) install_to "$HOME/.claude/skills" ;;
  2) install_to "$HOME/.openclaw/skills" ;;
  3)
    install_to "$HOME/.claude/skills"
    install_to "$HOME/.openclaw/skills"
    ;;
  *)
    echo "❌ 无效选项，请输入 1、2 或 3"
    exit 1
    ;;
esac

echo ""
echo "在 Claude Code 或 OpenClaw 中说「我想学 XXX」即可使用"
echo ""
echo "验证版本："
echo "  grep '^# Version' ~/.claude/skills/ai-tutor/SKILL.md"
