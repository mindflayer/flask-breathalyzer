install-dev-requirements:
	pip install -q -e .

install-test-requirements:
	pip install -q -r requirements.txt
	pip install -q -r test_requirements.txt

test-python:
	@echo "Running Python tests"
	py.test tests/*py
	@echo ""

lint-python:
	@echo "Linting Python files"
	flake8 --exit-zero --ignore=E501 --exclude=.git,compat.py mocket
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

