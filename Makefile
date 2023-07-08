PYTHONPATH := $(PWD)/.
VENV := $(PWD)/.env

PATH := $(VENV)/bin:$(PATH)
py := PATH=$(PATH) PYTHONPATH=$(PYTHONPATH) $(VENV)/bin/python3
pip := $(py) -m pip

.PHONY: jupyter
jupyter:
	$(py) -m jupyter notebook --notebook-dir=notebooks

.PHONY: play
play:
	@$(py) play.py

.PHONY: pythonpath
pythonpath:
	@echo $(PYTHONPATH)

.PHONY: venvdir
venvdir:
	@echo $(VENV)

.PHONY: venv
venv:
	python3 -m venv $(VENV)
	$(pip) install --upgrade pip
	$(pip) install -r requirements.txt
