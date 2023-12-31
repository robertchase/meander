PYTHONPATH := $(PWD):.
VENV := $(PWD)/.env

PATH := $(VENV)/bin:$(PATH)
BIN := PATH=$(PATH) PYTHONPATH=$(PYTHONPATH) $(VENV)/bin
py := $(BIN)/python3
pip := $(py) -m pip

.PHONY: test
test:
	$(BIN)/pytest tests

.PHONY: lint
lint:
	$(BIN)/pylint meander tests

.PHONY: black
black:
	$(BIN)/black meander tests

.PHONY: bump
bump:
	$(eval TMP := $(shell mktemp tmp.setup.XXXXXX))
	@awk '$$1=="version"{split($$3,n,".");$$0=sprintf("version = %d.%d.%d",n[1],n[2],n[3]+1)}{print}' setup.cfg > $(TMP)
	@mv $(TMP) setup.cfg
	@grep version setup.cfg

.PHONY: certs
certs:
	# https://stackoverflow.com/questions/10175812/how-to-generate-a-self-signed-ssl-certificate-using-openssl/41366949#41366949
	@openssl req -x509 -newkey rsa:4096 -sha256 -days 3650 \
     -nodes -keyout tmp.com.key -out tmp.com.crt -subj "/CN=example.com" \
     -addext "subjectAltName=DNS:example.com,DNS:*.example.com,IP:10.0.0.1"

.PHONY: bin
bin:
	@echo $(BIN)

.PHONY: venv
venv:
	python3 -m venv $(VENV)
	$(pip) install --upgrade pip
	$(pip) install -r requirements.txt
