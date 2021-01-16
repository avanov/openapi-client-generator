# https://www.gnu.org/software/make/manual/html_node/Special-Variables.html
# https://ftp.gnu.org/old-gnu/Manuals/make-3.80/html_node/make_17.html
PROJECT_MKFILE_PATH       := $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))
PROJECT_MKFILE_DIR        := $(shell cd $(shell dirname $(PROJECT_MKFILE_PATH)); pwd)

PROJECT_NAME              := openapi_client_generator
PROJECT_ROOT              := $(PROJECT_MKFILE_DIR)

BUILD_DIR                 := $(PROJECT_ROOT)/build
DIST_DIR                  := $(PROJECT_ROOT)/dist
TEST_DIR                  := $(PROJECT_ROOT)/tests
SPECS_DIR                 := $(PROJECT_ROOT)/specification/examples/v3.0

CLI                       := openapi-client-generator


typecheck:
	mypy --config-file setup.cfg --package $(PROJECT_NAME)
	mypy --config-file setup.cfg $(TEST_DIR)/petstore-full/petstore_full
	mypy --config-file setup.cfg $(TEST_DIR)/test_generated_client.py


test: typecheck
	pytest -s  --cov=openapi_client_generator $(TEST_DIR)


example-clients:
	$(CLI) gen -f -s "$(TEST_DIR)/petstore-full.json" -o "$(TEST_DIR)/petstore-full" -n petstore-full
	pip install -e $(TEST_DIR)/petstore-full
	$(CLI) gen -f -s "$(SPECS_DIR)/api-with-examples.json" -o "$(TEST_DIR)/api-with-examples" -n api-with-examples
	pip install -e $(TEST_DIR)/api-with-examples
	$(CLI) gen -f -s "$(SPECS_DIR)/callback-example.json" -o "$(TEST_DIR)/callback-example" -n callback-example
	pip install -e $(TEST_DIR)/callback-example
	$(CLI) gen -f -s "$(SPECS_DIR)/link-example.json" -o "$(TEST_DIR)/link-example" -n link-example
	pip install -e $(TEST_DIR)/link-example
	$(CLI) gen -f -s "$(SPECS_DIR)/petstore.json" -o "$(TEST_DIR)/petstore" -n petstore
	pip install -e $(TEST_DIR)/petstore
	$(CLI) gen -f -s "$(SPECS_DIR)/petstore-expanded.json" -o "$(TEST_DIR)/petstore-expanded" -n petstore-expanded
	pip install -e $(TEST_DIR)/petstore-expanded
	$(CLI) gen -f -s "$(SPECS_DIR)/uspto.json" -o "$(TEST_DIR)/uspto" -n uspto
	pip install -e $(TEST_DIR)/uspto



publish: example-clients test clean | do-publish
	@echo "Done publishing."


do-publish:
	python $(PROJECT_ROOT)/setup.py sdist bdist_wheel
	twine upload $(DIST_DIR)/*


test-all: | example-clients test
	@echo "Done."


clean:
	rm -rf $(BUILD_DIR) $(DIST_DIR)
