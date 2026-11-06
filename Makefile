VENV := venv
PATH := $(CURDIR)/$(VENV)/bin:$(PATH)
export PATH
FONTS := fonts/OffentligSans
FONTSPECTOR ?= $(VENV)/bin/fontspector
SANS_REF ?= build/public-sans-reference

.PHONY: venv build test proof install qa verify clean

venv:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
	python3 -m venv $(VENV)/diffenator
	$(VENV)/diffenator/bin/pip install -r requirements-qa.txt

build:
	cd sources && gftools builder config-OffentligSans.yaml

test:
	pytest -q tests

proof:
	python3 scripts/proof_page.py
	$(VENV)/diffenator/bin/diffenator2 proof $(FONTS)/ttf/*.ttf -o build/proof

install:
	@test -d $(FONTS)/otf || (echo "Run 'make build' first" && exit 1)
	mkdir -p "$$HOME/Library/Fonts"
	cp $(FONTS)/otf/OffentligSans-*.otf "$$HOME/Library/Fonts/"

qa:
	mkdir -p build
	-$(FONTSPECTOR) -p universal --skip-network --json build/fsp-universal.json $(FONTS)/ttf/*.ttf $(FONTS)/variable/*.ttf > build/fsp-universal.txt
	-$(FONTSPECTOR) -p opentype --skip-network --json build/fsp-opentype.json $(FONTS)/ttf/*.ttf $(FONTS)/variable/*.ttf > build/fsp-opentype.txt
	python3 scripts/fsp_summary.py build/fsp-universal.json
	python3 scripts/fsp_summary.py build/fsp-opentype.json

verify:
	./scripts/verify_commit.sh

clean:
	rm -rf fonts build
