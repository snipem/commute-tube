.PHONY: dist

coverage:
	py.test commute_tube --cov-report xml:cov.xml --cov-report html --cov commute_tube

deps:
	pip install -r requirements.txt

dist:
	rm dist/*.tar.gz || true
	python3 setup.py sdist
	python3 -m twine upload dist/*

test_deps:
	pip install -r test_requirements.txt
	pip install -e .
