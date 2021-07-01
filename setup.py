from setuptools import setup, find_packages
from os import path

import pytexcount

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md')) as f:
    long_description = f.read()

setup(
    name='pytexcount',
    version=pytexcount.__version__,

    # Description
    description=pytexcount.__doc__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='website',

    project_urls={
        'Bug Reports': 'https://github.com/pierre-24/pytexcount/issues',
        'Source': 'https://github.com/pierre-24/pytexcount',
    },

    url='https://github.com/pierre-24/pytexcount',
    author=pytexcount.__author__,

    # Classifiers
    classifiers=[
        'Environment :: Scientific',
        'Operating System :: OS Independent',

        # Specify the Python versions:
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],

    packages=find_packages(),
    python_requires='>=3.7',
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'pytexcount = pytexcount.script:main'
        ]
    },
)