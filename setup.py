import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().strip().split()

with open("nbmanips/VERSION", "r", encoding="utf-8") as fh:
    version = fh.read()

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
    packages=['nbmanips'],
    include_package_data=True,
    entry_points={
        'console_scripts': ['nbmanips=nbmanips.__main__:nbmanips',
                            'nb=nbmanips.__main__:nbmanips'],
    },
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    keywords=['jupyter', 'notebook', 'ipynb', 'slides', 'notebooks'],
)
