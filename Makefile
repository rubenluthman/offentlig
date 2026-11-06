VENV := venv
PATH := $(CURDIR)/$(VENV)/bin:$(PATH)
export PATH
FONTS := fonts/OffentligSans
FONTSPECTOR ?= $(VENV)/bin/fontspector
SANS_REF ?= build/public-sans-reference

.PHONY: venv build test proof specimen install qa verify clean

venv:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
	python3 -m venv $(VENV)/diffenator
	$(VENV)/diffenator/bin/pip install -r requirements-qa.txt

build:
	cd sources && gftools builder config-OffentligSans.yaml

test:
	$(VENV)/bin/pytest -q tests

proof:
	$(VENV)/bin/python scripts/proof_page.py
	PATH="$(CURDIR)/$(VENV)/diffenator/bin:$$PATH" diffenator2 proof $(FONTS)/ttf/*.ttf -o build/proof/diffenator2

specimen:
	$(VENV)/bin/python scripts/specimen.py

install:
	@test -d $(FONTS)/otf || (echo "Run 'make build' first" && exit 1)
	mkdir -p "$$HOME/Library/Fonts"
	cp $(FONTS)/otf/OffentligSans-*.otf "$$HOME/Library/Fonts/"

qa:
	mkdir -p build
	-$(FONTSPECTOR) -p universal --skip-network --json build/fsp-universal.json $(FONTS)/ttf/*.ttf $(FONTS)/variable/*.ttf > build/fsp-universal.txt
	-$(FONTSPECTOR) -p opentype --skip-network --json build/fsp-opentype.json $(FONTS)/ttf/*.ttf $(FONTS)/variable/*.ttf > build/fsp-opentype.txt
	$(VENV)/bin/python scripts/fsp_summary.py build/fsp-universal.json
	$(VENV)/bin/python scripts/fsp_summary.py build/fsp-opentype.json

verify:
	./scripts/verify_commit.sh

clean:
	rm -rf fonts build
