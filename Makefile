all: help

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  init                        to install python dependencies"
	@echo "  lint                        to lint backend code (flake8)"
	@echo "  test                        to run test suite"
	@echo "  help                        to get this help"

init:
	pip install -e . && pip install -r requirements.txt

lint:
	flake8 pytexcount --max-line-length=120 --ignore=N802

test:
	python -m unittest discover -s pytexcount.tests
