#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 清理混乱的 Allure 报告文件夹
# ═══════════════════════════════════════════════════════════════

set -e

echo "🧹 开始清理测试报告文件夹..."
echo ""

# 当前目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# ═══════════════════════════════════════════════════════════════
# 1. 备份重要报告（可选）
# ═══════════════════════════════════════════════════════════════

BACKUP_DIR="test-reports-backup-$(date +%Y%m%d_%H%M%S)"

echo "📦 是否需要备份现有报告？(y/n)"
read -r NEED_BACKUP

if [ "$NEED_BACKUP" = "y" ] || [ "$NEED_BACKUP" = "Y" ]; then
    mkdir -p "$BACKUP_DIR"
    
    if [ -d "allure-report-admin-profile" ]; then
        echo "  备份: allure-report-admin-profile"
        cp -r allure-report-admin-profile "$BACKUP_DIR/"
    fi
    
    if [ -d "allure-report-new" ]; then
        echo "  备份: allure-report-new"
        cp -r allure-report-new "$BACKUP_DIR/"
    fi
    
    if [ -d "allure-results-fix" ]; then
        echo "  备份: allure-results-fix"
        cp -r allure-results-fix "$BACKUP_DIR/"
    fi
    
    echo "  ✅ 备份完成: $BACKUP_DIR"
    echo ""
fi

# ═══════════════════════════════════════════════════════════════
# 2. 清理临时文件夹
# ═══════════════════════════════════════════════════════════════

echo "🗑️  清理临时报告文件夹..."

if [ -d "allure-report-admin-profile" ]; then
    echo "  删除: allure-report-admin-profile"
    rm -rf allure-report-admin-profile
fi

if [ -d "allure-report-new" ]; then
    echo "  删除: allure-report-new"
    rm -rf allure-report-new
fi

if [ -d "allure-results-fix" ]; then
    echo "  删除: allure-results-fix"
    rm -rf allure-results-fix
fi

# 清理任何其他 allure-report-* 文件夹
for dir in allure-report-*; do
    if [ -d "$dir" ]; then
        echo "  删除: $dir"
        rm -rf "$dir"
    fi
done

# 清理任何其他 allure-results-* 文件夹
for dir in allure-results-*; do
    if [ -d "$dir" ]; then
        echo "  删除: $dir"
        rm -rf "$dir"
    fi
done

echo ""
echo "✅ 清理完成！"
echo ""

# ═══════════════════════════════════════════════════════════════
# 3. 显示最终结构
# ═══════════════════════════════════════════════════════════════

echo "📁 当前测试报告结构："
echo ""
echo "  allure-results/    ← 原始测试结果（pytest 输出）"
echo "  allure-report/     ← 最新测试报告（Allure 生成）"
echo "  screenshots/       ← 测试截图"
echo "  reports/           ← pytest 日志"
echo ""

# ═══════════════════════════════════════════════════════════════
# 4. 提示如何使用
# ═══════════════════════════════════════════════════════════════

echo "📝 标准工作流："
echo ""
echo "  1. 运行测试："
echo "     make test TEST_TARGET=tests/admin/profile"
echo "     → 输出到: allure-results/"
echo ""
echo "  2. 生成报告："
echo "     make report"
echo "     → 输出到: allure-report/"
echo ""
echo "  3. 查看报告："
echo "     make serve"
echo "     → 浏览器打开: http://127.0.0.1:59717"
echo ""
echo "  4. 清理所有报告："
echo "     make clean"
echo ""

if [ -d "$BACKUP_DIR" ]; then
    echo "💾 备份保存在: $BACKUP_DIR"
    echo "   如不需要可手动删除: rm -rf $BACKUP_DIR"
    echo ""
fi

echo "🎉 优化完成！测试报告结构已统一。"

