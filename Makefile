.PHONY: test docs clean-pyc build release

test:
	tox

docs:
	$(MAKE) -C docs html

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

build:
	python setup.py bdist_wheel --universal

release: build
	python setup.py sdist bdist_wheel upload
