from setuptools import setup
try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README.md').read()

setup(
    name='commute-tube',
    packages=['commute_tube'],
    version='1.0',
    description='Copy online media to your USB pen by night and watch it on your daily commute',
    long_description=long_description,
    author='Matthias Kuech',
    author_email='halde@matthias-kuech.de',
    url='https://github.com/snipem/commute-tube',
    download_url='https://github.com/snipem/commute-tube/archive/1.0.tar.gz',
    keywords=['commute', 'download', 'youtube-dl'],
    license='GPL2',
    test_suite='nose.collector',
    tests_require=['nose'],
    entry_points={
        'console_scripts': ['commutecli=commute_tube.commutecli:main']
        }
    )
