VENV := venv
PATH := $(CURDIR)/$(VENV)/bin:$(PATH)
export PATH
FONTS := fonts/OffentligSans
FONTSPECTOR ?= $(VENV)/bin/fontspector
SANS_REF ?= build/public-sans-reference
SANS_REF_COMMIT ?= e40fcf567
MAIN_REF ?= build/main-reference
DIFFENATOR2 = PATH="$(CURDIR)/$(VENV)/diffenator/bin:$$PATH" diffenator2

.PHONY: venv build test proof diff-public-sans diff-main specimen install qa verify clean

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

# Public Sans at SANS_REF_COMMIT, cloned once into SANS_REF (its fonts/ttf holds the built TTFs).
$(SANS_REF)/fonts/ttf:
	rm -rf $(SANS_REF)
	git clone --filter=blob:none --no-checkout https://github.com/uswds/public-sans.git $(SANS_REF)
	git -C $(SANS_REF) checkout -q $(SANS_REF_COMMIT)

# Compare the current build with Public Sans. Output: build/diff-public-sans
diff-public-sans: $(SANS_REF)/fonts/ttf
	@test -d $(FONTS)/ttf || (echo "Run 'make build' first" && exit 1)
	$(DIFFENATOR2) diff -fb $(SANS_REF)/fonts/ttf/*.ttf -fa $(FONTS)/ttf/*.ttf -o build/diff-public-sans

# Build origin/main in a separate worktree (MAIN_REF), then compare the current build with it.
# Delete MAIN_REF to rebuild it. Output: build/diff-main
diff-main:
	@test -d $(FONTS)/ttf || (echo "Run 'make build' first" && exit 1)
	@if [ ! -d $(MAIN_REF)/$(FONTS)/ttf ]; then \
	  git worktree remove --force $(MAIN_REF) 2>/dev/null || true; \
	  git worktree add --detach $(MAIN_REF) origin/main && \
	  (cd $(MAIN_REF)/sources && gftools builder config-OffentligSans.yaml); \
	fi
	$(DIFFENATOR2) diff -fb $(MAIN_REF)/$(FONTS)/ttf/*.ttf -fa $(FONTS)/ttf/*.ttf -o build/diff-main

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
	@status=0; \
	for r in universal opentype; do \
	  $(VENV)/bin/python scripts/fsp_summary.py build/fsp-$$r.json || status=1; \
	done; \
	exit $$status

verify:
	./scripts/verify_commit.sh

clean:
	rm -rf fonts build
