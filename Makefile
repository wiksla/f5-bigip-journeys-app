
export ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY = format lint test
sources = journeys test journey.py

format:
	isort --recursive $(sources)
	black -v $(sources)

lint:
	flake8 $(sources)
	pylint --errors-only $(sources)

test: FORCE
	PYTHONPATH=$$PYTHONPATH:${ROOT_DIR} pytest -s

FORCE:
