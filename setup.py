import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='leakpy',
    version='1.6.5',
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
    entry_points={
        'console_scripts': [
            'leakpy=leakpy.cli:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
