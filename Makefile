PROJECT_NAME := wyoming_azure_speech
VERSION := $(shell git describe --tags --always | sed -r 's/-([[:digit:]]*)-.*/.dev\1/')
export VERSION

PYTHON_VERSION := 3.13
export PYTHON_VERSION
VENV_DIRECTORY := .venv

BUILD_DIR := build
DIST_DIR := dist
SRC_FILES := $(shell find $(PROJECT_NAME) -name '*.py')
WHEEL := $(DIST_DIR)/$(PROJECT_NAME)-$(VERSION)-py3-none-any.whl

DOCKER_CMD :=
ifeq ($(wildcard /.dockerenv)$(RUNNER_OS),)
ifneq ($(shell which docker),)
  DOCKER_CMD := docker run $(if $(TERM),-it )--rm --user $(shell id -u):$(shell id -g) --volume $(PWD):$(PWD) --workdir $(PWD) python:$(PYTHON_VERSION)
endif
endif

ifneq ($(V),)
  Q :=
else
  Q := @
endif

$(VENV_DIRECTORY): requirements.txt dev-requirements.txt
	$(Q)$(DOCKER_CMD) python -m venv $(VENV_DIRECTORY)
	$(Q)$(DOCKER_CMD) $(VENV_DIRECTORY)/bin/python -m pip install $(foreach req,$^,-r $(req))
	$(Q)touch $(VENV_DIRECTORY)
	
$(WHEEL): $(VENV_DIRECTORY) setup.py $(SRC_FILES)
	$(Q)$(DOCKER_CMD) $(VENV_DIRECTORY)/bin/python -m build --wheel

clean:
	$(Q)rm -rf $(VENV_DIRECTORY) $(BUILD_DIR) $(PROJECT_NAME).egg-info $(DIST_DIR)
	$(Q)find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	
format: $(VENV_DIRECTORY)
	$(Q)$(DOCKER_CMD) $(VENV_DIRECTORY)/bin/ruff format .
	$(Q)$(DOCKER_CMD) $(VENV_DIRECTORY)/bin/ruff check --select ALL --fix --unsafe-fixes .

lint: $(VENV_DIRECTORY)
	$(Q)$(DOCKER_CMD) $(VENV_DIRECTORY)/bin/ruff format --diff .
	$(Q)$(DOCKER_CMD) $(VENV_DIRECTORY)/bin/ruff check --select ALL --diff --unsafe-fixes .

run: $(VENV_DIRECTORY)
	$(Q)$(DOCKER_CMD) $(VENV_DIRECTORY)/bin/python -m $(PROJECT_NAME) --debug

shell: $(VENV_DIRECTORY)
	$(Q)$(DOCKER_CMD) bash -c "bash --rcfile <(cat ~/.bashrc && echo source $(VENV_DIRECTORY)/bin/activate)"

.PHONY := clean format lint shell
.DEFAULT_GOAL := $(WHEEL)
