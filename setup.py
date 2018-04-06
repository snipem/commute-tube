from distutils.core import setup

setup(
    name='commutetube',
    version='0.1dev',
    packages=['commute_tube',],
    license='GPL 3.0',
    long_description=open('README.md').read(),
    entry_points = {
        "console_scripts": [
            "commutetube=commute_tube.__main__:main"
        ]
    },
    install_requires = [
        "youtube_dl",
        "humanfriendly"
    ]

)