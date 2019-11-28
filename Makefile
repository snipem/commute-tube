coverage:
	py.test commute_tube --cov-report xml:cov.xml --cov-report html --cov commute_tube

dist:
	rm dist/*.tar.gz
	python setup.py sdist
	python -m twine upload dist/*