.PHONY: dist

coverage:
	py.test commute_tube --cov-report xml:cov.xml --cov-report html --cov commute_tube

deps:
	python3 -m pip install twine --user

dist:
	rm dist/*.tar.gz || true
	python3 setup.py sdist
	python3 -m twine upload dist/*