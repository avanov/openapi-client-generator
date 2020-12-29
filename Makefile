# https://www.gnu.org/software/make/manual/html_node/Special-Variables.html
# https://ftp.gnu.org/old-gnu/Manuals/make-3.80/html_node/make_17.html
PROJECT_MKFILE_PATH       := $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))
PROJECT_MKFILE_DIR        := $(shell cd $(shell dirname $(PROJECT_MKFILE_PATH)); pwd)

PROJECT_NAME              := openapi_client_generator
PROJECT_ROOT              := $(PROJECT_MKFILE_DIR)

BUILD_DIR                 := $(PROJECT_ROOT)/build
DIST_DIR                  := $(PROJECT_ROOT)/dist
TEST_DIR                  := $(PROJECT_ROOT)/tests

CLI                       := openapi-client-generator


typecheck:
	mypy --config-file setup.cfg --package $(PROJECT_NAME)
	mypy --config-file setup.cfg $(TEST_DIR)/example_client/example_client


test: typecheck
	pytest -s  --cov=openapi_client_generator $(TEST_DIR)


generate-example-client:
	$(CLI) gen -f -s "$(TEST_DIR)/example-client-spec.json" -o "$(TEST_DIR)/example_client" -n example-client


publish: generate-example-client test
	rm -rf $(BUILD_DIR) $(DIST_DIR)
	python $(PROJECT_ROOT)/setup.py sdist bdist_wheel
	twine upload $(DIST_DIR)/*
