.PHONY: test test-p0 report serve clean
.PHONY: test-mutate
.PHONY: clean-cache

# ============================================================
# 手动工作流（最短入口）
# - 不依赖历史“一键脚本入口”
# ============================================================

PYTEST_ARGS ?=
TEST_TARGET ?= tests
SUITE_KEY ?=
PYTHON ?= python3

test:
	pytest -q $(TEST_TARGET) $(PYTEST_ARGS) --alluredir=allure-results
	$(PYTHON) -m utils.allure_cache sync --suite-key "$(SUITE_KEY)" --guess-from "$(TEST_TARGET)" --src allure-results

test-p0:
	pytest -q $(TEST_TARGET) -m "P0" $(PYTEST_ARGS) --alluredir=allure-results
	$(PYTHON) -m utils.allure_cache sync --suite-key "$(SUITE_KEY)" --guess-from "$(TEST_TARGET)__P0" --src allure-results

test-mutate:
	pytest -q $(TEST_TARGET) -m "mutate" $(PYTEST_ARGS) --alluredir=allure-results
	$(PYTHON) -m utils.allure_cache sync --suite-key "$(SUITE_KEY)" --guess-from "$(TEST_TARGET)__mutate" --src allure-results

report:
	$(PYTHON) -m utils.allure_cache report --out allure-report

serve:
	$(PYTHON) -m utils.allure_cache report --out allure-report
	python3 -m http.server 59717 --bind 127.0.0.1 --directory "allure-report"

clean:
	rm -rf allure-results allure-report screenshots reports .pytest_cache

clean-cache:
	rm -rf .allure-cache


