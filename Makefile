pytest:
	cd tests; python -m pytest

dist: pytest
	python setup.py sdist bdist_wheel

publish: dist
	python -m twine upload --skip-existing -u __token__ dist/*

setup: requirements.txt requirements-dev.txt setup.py
	pip install --upgrade pip
	pip install -r requirements-dev.txt
	pip install -e .

clean:
	rm -rf __pycache__
	rm -rf .ipynb_checkpoints
	rm -r dist
	rm -r build
	rm -r *.egg-info
