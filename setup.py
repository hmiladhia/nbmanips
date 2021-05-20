import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

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
    # install_requires=['scikit-learn==0.24.0'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    keywords=['jupyter', 'notebook', 'ipynb', 'slides', 'notebooks'],
)
