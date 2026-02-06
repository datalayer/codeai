# Copyright (c) 2025-2026 Datalayer, Inc.
#
# BSD 3-Clause License

SHELL=/bin/bash

.DEFAULT_GOAL := default

.PHONY: clean build codeai

VERSION = "0.0.3"

default: all ## Default target is all.

help: ## display this help.
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

all: clean dev ## Clean Install and Build

install:
	pip install .

dev:
	pip install ".[test,lint,typing]"

build:
	pip install build
	python -m build .

clean: ## clean
	git clean -fdx

build-docker:
	docker buildx build --platform linux/amd64,linux/arm64 -t datalayer/codeai:${VERSION} .
	docker image tag datalayer/codeai:${VERSION} datalayer/codeai:latest

start-docker:
	docker run -i --rm \
	  -e SERVER_URL=http://localhost:8888 \
	  -e TOKEN=MY_TOKEN \
	  -e NOTEBOOK_PATH=notebook.ipynb \
	  --network=host \
	  datalayer/codeai:latest

pull-docker:
	docker image pull datalayer/codeai:latest

push-docker:
	docker push datalayer/codeai:${VERSION}
	docker push datalayer/codeai:latest

publish-pypi: # publish the pypi package
	git clean -fdx && \
		python -m build
	@exec echo
	@exec echo twine upload ./dist/*-py3-none-any.whl
	@exec echo
	@exec echo https://pypi.org/project/codeai/#history

codeai:
	@AWS_ACCESS_KEY_ID=${DATALAYER_BEDROCK_AWS_ACCESS_KEY_ID} \
	AWS_SECRET_ACCESS_KEY=${DATALAYER_BEDROCK_AWS_SECRET_ACCESS_KEY} \
	AWS_DEFAULT_REGION=${DATALAYER_BEDROCK_AWS_DEFAULT_REGION} \
	  codeai --eggs
