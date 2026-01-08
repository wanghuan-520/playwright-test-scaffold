.PHONY: test test-p0 report serve clean
.PHONY: test-mutate test-unit test-cov
.PHONY: clean-cache clean-all
.PHONY: lint format check install-hooks
.PHONY: spec-new spec-plan spec-bootstrap spec-implement spec-refresh-po

# ============================================================
# 配置变量
# ============================================================

PYTEST_ARGS ?=
TEST_TARGET ?= tests
SUITE_KEY ?=
PYTHON ?= python3

# ============================================================
# 代码质量 & 开发工具
# ============================================================

install-hooks:  ## 安装 pre-commit hooks
	pip install pre-commit
	pre-commit install
	@echo "✅ Pre-commit hooks 已安装！"

lint:  ## 运行代码检查 (ruff)
	ruff check . --output-format=grouped

format:  ## 格式化代码 (ruff)
	ruff format .
	ruff check . --fix

check:  ## 运行所有检查 (lint + type check)
	@echo "🔍 Running ruff..."
	ruff check .
	@echo "🔍 Running mypy..."
	mypy --ignore-missing-imports core/ utils/ || true
	@echo "✅ 检查完成！"

# ============================================================
# 单元测试
# ============================================================

test-unit:  ## 运行框架单元测试
	PRECHECK_SERVICES=0 pytest tests/framework/ -v --tb=short

test-cov:  ## 运行单元测试并生成覆盖率报告
	PRECHECK_SERVICES=0 pytest tests/framework/ -v --cov=core --cov=utils --cov-report=term-missing --cov-report=html:reports/coverage
	@echo "📊 覆盖率报告: reports/coverage/index.html"

# ============================================================
# E2E 测试
# ============================================================

test:
	@start_s=$$(date +%s); \
	pytest -q $(TEST_TARGET) $(PYTEST_ARGS) --alluredir=allure-results; \
	rc=$$?; \
	$(PYTHON) -m utils.allure_cache sync --suite-key "$(SUITE_KEY)" --guess-from "$(TEST_TARGET)" --src allure-results; \
	end_s=$$(date +%s); \
	dur_s=$$((end_s - start_s)); \
	h=$$((dur_s / 3600)); m=$$(((dur_s % 3600) / 60)); s=$$((dur_s % 60)); \
	if [ $$h -gt 0 ]; then printf "Duration: %d:%02d:%02d\\n" $$h $$m $$s; else printf "Duration: %d:%02d\\n" $$m $$s; fi; \
	exit $$rc

test-p0:
	@start_s=$$(date +%s); \
	pytest -q $(TEST_TARGET) -m "P0" $(PYTEST_ARGS) --alluredir=allure-results; \
	rc=$$?; \
	$(PYTHON) -m utils.allure_cache sync --suite-key "$(SUITE_KEY)" --guess-from "$(TEST_TARGET)__P0" --src allure-results; \
	end_s=$$(date +%s); \
	dur_s=$$((end_s - start_s)); \
	h=$$((dur_s / 3600)); m=$$(((dur_s % 3600) / 60)); s=$$((dur_s % 60)); \
	if [ $$h -gt 0 ]; then printf "Duration: %d:%02d:%02d\\n" $$h $$m $$s; else printf "Duration: %d:%02d\\n" $$m $$s; fi; \
	exit $$rc

test-mutate:
	@start_s=$$(date +%s); \
	pytest -q $(TEST_TARGET) -m "mutate" $(PYTEST_ARGS) --alluredir=allure-results; \
	rc=$$?; \
	$(PYTHON) -m utils.allure_cache sync --suite-key "$(SUITE_KEY)" --guess-from "$(TEST_TARGET)__mutate" --src allure-results; \
	end_s=$$(date +%s); \
	dur_s=$$((end_s - start_s)); \
	h=$$((dur_s / 3600)); m=$$(((dur_s % 3600) / 60)); s=$$((dur_s % 60)); \
	if [ $$h -gt 0 ]; then printf "Duration: %d:%02d:%02d\\n" $$h $$m $$s; else printf "Duration: %d:%02d\\n" $$m $$s; fi; \
	exit $$rc

report:
	$(PYTHON) -m utils.allure_cache report --out allure-report

serve:
	$(PYTHON) -m utils.allure_cache report --out allure-report
	python3 -m http.server 59717 --bind 127.0.0.1 --directory "allure-report"

clean:
	@echo "🧹 清理测试报告..."
	rm -rf allure-results allure-report screenshots reports .pytest_cache
	@echo "✅ 清理完成！"

clean-cache:
	@echo "🧹 清理 Allure 缓存..."
	rm -rf .allure-cache
	@echo "✅ 缓存已清理！"

clean-all:
	@echo "🧹 清理所有 Allure 相关文件夹（包括临时文件夹）..."
	rm -rf allure-results* allure-report* screenshots reports .pytest_cache .allure-cache
	@echo "✅ 全部清理完成！"



# ============================================================
# Spec-Driven workflow（可选：spec-kit 风格落地到本仓库）
# - specs/ 是“规格层”（spec/plan/tasks）
# - docs/test-plans/ 是“可解析契约”（用于生成器输入）
# ============================================================

SLUG ?=
URL ?=
PAGE_TYPE ?= FORM
AUTH ?=
MODE ?= plan

spec-new:
	@python3 scripts/speckit.py new --slug "$(SLUG)" --url "$(URL)" --page-type "$(PAGE_TYPE)" $(if $(AUTH),--auth-required "$(AUTH)",)

spec-plan:
	@python3 scripts/speckit.py sync-plan --slug "$(SLUG)"

spec-bootstrap:
	@python3 scripts/speckit.py bootstrap

spec-implement:
	@python3 scripts/speckit.py implement --slug "$(SLUG)" --mode "$(MODE)"

spec-refresh-po:
	@python3 -m generators.refresh_page_objects --plans-dir docs/test-plans --slug "$(SLUG)"
