PROJECT=openapi_client_generator

test: typecheck
	pytest -s  --cov=openapi_client_generator tests/

typecheck:
	mypy --config-file setup.cfg --package $(PROJECT)
