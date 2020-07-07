
export ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY = format lint test asd
sources = journeys migrate.py

format:
	isort --recursive $(sources)
	black -v $(sources)

lint:
	flake8 $(sources)
	pylint --errors-only $(sources)

test:
	pytest