import re
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

def get_version():
    with open("leakpy/__init__.py", "rt") as file:
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
        'prompt_toolkit'
    ],
    python_requires='>=3.6',  
    project_urls={
        'Bug Tracker': 'https://github.com/Chocapikk/LeakPy/issues',
        'Documentation': 'https://github.com/Chocapikk/LeakPy/wiki',
        'Source Code': 'https://github.com/Chocapikk/LeakPy',
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
