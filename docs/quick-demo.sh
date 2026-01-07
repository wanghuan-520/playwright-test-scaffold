#!/bin/bash

# ============================================================
# Spec-Kit 快速演示脚本
# 功能：演示如何使用 Spec-Kit 框架测试一个页面
# ============================================================

set -e

echo "🎯 Spec-Kit 实战演示"
echo "目标页面: https://localhost:3000/admin/users"
echo ""

# 检查环境
echo "📋 步骤 1: 检查环境"
echo "----------------------------------------"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

if ! command -v pytest &> /dev/null; then
    echo "❌ pytest 未安装，请运行: pip install -r requirements.txt"
    exit 1
fi

echo "✅ Python3: $(python3 --version)"
echo "✅ pytest: $(pytest --version | head -n 1)"
echo ""

# 选择演示模式
echo "📋 步骤 2: 选择演示模式"
echo "----------------------------------------"
echo "A) 运行现有测试（验证环境）"
echo "B) 创建新测试（完整演示）"
echo "C) 查看文档（学习流程）"
echo ""
read -p "请选择 (A/B/C): " choice

case $choice in
    [Aa]* )
        echo ""
        echo "🚀 模式 A: 运行现有测试"
        echo "----------------------------------------"
        
        echo "📂 查看测试规约..."
        cat specs/011-admin_users/spec.md
        echo ""
        
        echo "📂 查看测试文件..."
        ls -la tests/admin/users/
        echo ""
        
        read -p "是否运行测试？(y/n) " run_test
        if [[ $run_test =~ ^[Yy]$ ]]; then
            echo "🧪 运行测试..."
            make test TEST_TARGET=tests/admin/users
            
            echo "📊 生成报告..."
            make report
            
            echo "🌐 启动报告服务器..."
            echo "浏览器打开: http://127.0.0.1:59717"
            make serve
        fi
        ;;
        
    [Bb]* )
        echo ""
        echo "🚀 模式 B: 创建新测试"
        echo "----------------------------------------"
        echo ""
        echo "我将演示如何为 admin/users 页面创建一个新的测试场景："
        echo "功能：导出用户列表为 CSV"
        echo ""
        
        read -p "是否继续？(y/n) " continue_demo
        if [[ $continue_demo =~ ^[Yy]$ ]]; then
            echo ""
            echo "📝 步骤 1: 在 Cursor 中输入:"
            echo "  /speckit.specify"
            echo ""
            echo "📝 步骤 2: 描述功能:"
            echo "  我要测试用户管理页面的导出功能："
            echo "  - 用户可以导出用户列表为 CSV"
            echo "  - 支持筛选条件（按角色、状态）"
            echo "  - 导出文件包含：用户名、邮箱、角色、创建时间"
            echo "  这是 P2 功能，需要登录。"
            echo ""
            echo "📝 步骤 3: 生成计划和任务:"
            echo "  /speckit.plan"
            echo "  /speckit.tasks"
            echo ""
            echo "📝 步骤 4: 自动实现:"
            echo "  /speckit.implement"
            echo ""
            echo "📝 步骤 5: 运行测试:"
            echo "  make test TEST_TARGET=tests/admin/users_export"
            echo ""
            echo "✅ 演示完成！请在 Cursor 中尝试上述命令。"
        fi
        ;;
        
    [Cc]* )
        echo ""
        echo "📚 模式 C: 查看文档"
        echo "----------------------------------------"
        echo ""
        echo "📖 实战落地手册:"
        echo "  docs/spec-kit-hands-on-guide.md"
        echo ""
        echo "📖 快速入门:"
        echo "  docs/spec-kit-quickstart.md"
        echo ""
        echo "📖 框架详解:"
        echo "  docs/spec-kit-guide.md"
        echo ""
        echo "📖 宪法深度解读:"
        echo "  docs/constitution-deep-dive.md"
        echo ""
        
        read -p "是否打开实战手册？(y/n) " open_doc
        if [[ $open_doc =~ ^[Yy]$ ]]; then
            cat docs/spec-kit-hands-on-guide.md
        fi
        ;;
        
    * )
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "✅ 演示完成！"
echo ""
echo "📚 更多资源:"
echo "  - 实战手册: docs/spec-kit-hands-on-guide.md"
echo "  - 快速入门: docs/spec-kit-quickstart.md"
echo "  - 框架详解: docs/spec-kit-guide.md"
echo ""

