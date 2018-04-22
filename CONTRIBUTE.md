# Contribute

## Upload to PIP

[Manual on how to upload to PIP](https://packaging.python.org/tutorials/distributing-packages/#working-in-development-mode)

This will only work for me as the maintainer:

    rm dist/*.tar.gz
    python setup.py sdist
    python -m twine upload dist/*

Twine uses the global config file in `$HOME/.pypirc`

### Setup py

[Example setup.py](https://github.com/pypa/sampleproject/blob/master/setup.py)

### AutoPep

autopep8 --max-line-length 999 -i commute_tube/commute_tube.py