AWS_REGION := $(shell cat ~/.aws/region)
AWS_ACCOUNT_ID = $(shell cat ~/.aws/account-id)

PYPI_USER := $(shell echo $$PYPI_USERNAME)
PYPI_PASSWORD := $(shell echo $$PYPI_PASSWORD)
DFBOT := dfbot

.PHONY: bootstrap development setup upload install uninstall check manifest up docker run

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
	python3 -m venv venv

# If you want to upload this as package, do this.
development:
	. venv/bin/activate && pip3 install --upgrade setuptools wheel twine

docker:
	docker build -t ${DFBOT} .

run:
	nohup docker run --rm --name doublefault ${DFBOT} > /dev/null 2>&1 &

# You need to login so that you can push image
awslogin:
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com

awspush:
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.$(AWS_REGION).amazonaws.com/df_bot

