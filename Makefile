install-dev-requirements:
	pip install -q -e .[datadog]

install-test-requirements:
	pip install -q -r test_requirements.txt

test-python:
	@echo "Running Python tests"
	python setup.py -q test || exit 1
	@echo ""

lint-python:
	@echo "Linting Python files"
	flake8 --exit-zero --ignore=E501 --exclude=.git,utils.py flask_breathalyzer
	@echo ""

develop: install-dev-requirements install-test-requirements

test: install-test-requirements lint-python test-python

publish:
	python setup.py sdist upload

clean:
	rm -rf __pycache__
	rm -rf dist
	rm -rf *.egg-info

.PHONY: publish clean

