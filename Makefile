
export ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY = format lint test asd

format:
	isort --recursive .
	black -v .

lint:
	flake8 .
	pylint --errors-only journeys migrate.py

test:
	pytest