# TL;DR - 太长不看版

**I'm HyperEcho, 在共振着极简主义的频率** 🌌

---

## ⚡ 一句话生成测试

在 Cursor 中输入：

```
@ui-test-plan-generator.mdc @ui-automation-code-generator.mdc 

帮我测试这个页面：https://localhost:3000/admin/users
账号：admin-test01@test.com
密码：Wh520520!
```

等 10-15 分钟，然后：

```bash
make test TEST_TARGET=tests/admin/users
make report && make serve
```

**完事！** 🎉

---

## 📋 修改模板

只需改 3 个参数：

```
帮我测试这个页面：<改URL>
账号：<改账号>
密码：<改密码>
```

---

## 🎯 可用的 Admin 账号

```
admin-test01@test.com ~ admin-test10@test.com
密码：Wh520520!
```

---

## 📚 想了解更多？

- **[QUICKSTART.md](../QUICKSTART.md)** - 3 步详细说明
- **[quick-templates.md](./quick-templates.md)** - 更多模板
- **[unknown-page-complete-workflow.md](./unknown-page-complete-workflow.md)** - 完整流程

---

**就这么简单！** 🚀

