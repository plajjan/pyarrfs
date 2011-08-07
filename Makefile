

all:
	python setup.py build

install:
	python setup.py install

tgz:
	python setup.py sdist

clean:
	rm -rf *.pyc pyarrfs/*.pyc build dist MANIFEST

upload:
	python setup.py sdist upload
