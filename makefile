SHELL := /bin/bash #to be able to execute `source`

.PHONY: build clean tetst upload docs
build: clean
	python setup.py  sdist bdist_wheel

clean:
	rm -rf dist */*.egg-info *.egg-info  build
	rm -rf .test

test: build
	./test/runtest

upload: build
	twine check dist/*
	twine upload dist/* --verbose

docs:	
	make -C docs html
