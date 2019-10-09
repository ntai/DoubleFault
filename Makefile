
PYPI_USER := $(shell echo $$PYPI_USERNAME)
PYPI_PASSWORD := $(shell echo $$PYPI_PASSWORD)

.PHONY: bootstrap development setup upload install uninstall check manifest up

default: setup

setup: manifest
	python3 setup.py sdist bdist_wheel

upload: 
	twine upload --repository-url https://test.pypi.org/legacy/ dist/* --skip-existing -u ${PYPI_USER} -p ${PYPI_PASSWORD}

check:
	python3 setup.py develop
	python3 -m twine check

install:
	pip3 install --no-cache-dir -i https://test.pypi.org/simple/ DoubleFault

uninstall:
	pip3 uninstall doublefault

manifest:
	echo include requirements.txt> MANIFEST.in

# Setting up virtualenv
bootstrap:
	virtualenv -p python3 p3

# If you want to upload this as package, do this.
development:
	. p3/bin/activate && pip3 install --upgrade setuptools wheel twine
