import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("nbmanips/VERSION", "r", encoding="utf-8") as fh:
    version = fh.read().strip()

setuptools.setup(
    name="nbmanips",
    version=version,
    author="Dhia HMILA",
    author_email="dhiahmila@gmail.com",
    description="nbmanips allows you easily manipulate ipynb files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT',
    url="https://github.com/hmiladhia/nbmanips",
    packages=['nbmanips', 'nbmanips.cli'],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'nbmanips=nbmanips.__main__:nbmanips',
            'nb=nbmanips.__main__:nbmanips'],
    },
    install_requires=[
        'nbconvert>=6.0.0',
        'nbformat>=5.1.3',
        'html2text==2020.1.16',
        'cloudpickle>=1.6.*',
        'click>=7.1.*',
        'Pygments>=2.10.*',
        'colorama>=0.4.*'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    keywords=['jupyter', 'notebook', 'ipynb', 'slides', 'notebooks'],
)
