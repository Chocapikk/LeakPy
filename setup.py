import re
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

def get_version():
    with open("leakpy/__init__.py", "rt", encoding="utf-8") as file:
        version = re.search(r'__version__ = \"(.*?)\"', file.read()).group(1)
    return version

setuptools.setup(
    name='leakpy',
    version=get_version(),
    author="Valentin Lobstein",
    author_email="balgogan@protonmail.com",
    description="LeakIX API Client",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Chocapikk/LeakPy",
    packages=setuptools.find_packages(),
    install_requires=[
        'requests',
        'rich',
        'prompt_toolkit',
        'keyring>=23.0.0',
        'l9format>=1.3.2'
    ],
    python_requires='>=3.9',  
    project_urls={
        'Bug Tracker': 'https://github.com/Chocapikk/LeakPy/issues',
        'Documentation': 'https://leakpy.readthedocs.io/',
        'Source Code': 'https://github.com/Chocapikk/LeakPy',
    },
    extras_require={
        'docs': [
            'sphinx>=5.0.0',
            'sphinx-rtd-theme>=1.0.0',
            'myst-parser>=0.18.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'leakpy=leakpy.cli:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",  
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: Internet :: Log Analysis", 
    ],
)
