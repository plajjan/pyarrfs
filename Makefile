

all:
	python setup.py build

install:
	python setup.py install

tgz:
	python setup.py sdist

clean:
	rm -rf *.pyc build dist MANIFEST
