# -*- coding: utf-8 -*-
from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='commute-tube',
    version='1.6',
    packages=['commute_tube',],
    url='https://github.com/snipem/commute-tube',
    license='GPL 3.0',
    long_description=long_description, 
    long_description_content_type='text/markdown',
    author='Matthias Küch',
    author_email='halde@matthias-kuech.de',
    classifiers=[ 
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ],
    keywords='youtube-dl wrapper commute config datahoarding', 
    package_data={
        'sample': ['config.example.json'],
    },
    entry_points = {
        "console_scripts": [
            "commute-tube=commute_tube.__main__:main"
        ]
    },
    install_requires = [
        "youtube_dl",
        "humanfriendly"
    ],
    setup_requires = [
        "pytest-runner"
    ],
    tests_requires = [
        "pytest"
    ],
    project_urls={  # Optional
        'Bug Reports': 'https://github.com/snipem/commute-tube/issues',
        'Source': 'https://github.com/snipem/commute-tube/'
    }
)