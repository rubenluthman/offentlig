VENV := venv
PATH := $(CURDIR)/$(VENV)/bin:$(PATH)
export PATH
FONTS := fonts/OffentligSans
FONTSPECTOR ?= $(VENV)/bin/fontspector
SANS_REF ?= build/public-sans-reference
SANS_REF_COMMIT ?= e40fcf567
MAIN_REF ?= build/main-reference
# Heavy targets queue on the machine-wide lock when a `heavy-run` command is installed, and run directly where it is not (CI).
HEAVY := $(shell command -v heavy-run)
DIFFENATOR2 = $(HEAVY) env PATH="$(CURDIR)/$(VENV)/diffenator/bin:$$PATH" diffenator2

.PHONY: venv build test proof diff-public-sans diff-main specimen social-preview install qa verify clean

venv:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
	python3 -m venv $(VENV)/diffenator
	$(VENV)/diffenator/bin/pip install -r requirements-qa.txt

build:
	cd sources && $(HEAVY) gftools builder config-OffentligSans.yaml

PYTEST_JOBS ?= 4

# A green run leaves build/test-stamp, a hash of everything the tests read; `make verify` skips its own run when the hash still matches.
test:
	rm -f build/test-stamp
	$(HEAVY) $(VENV)/bin/pytest -q -n $(PYTEST_JOBS) --dist worksteal tests
	python3 scripts/test_stamp.py write

proof:
	$(VENV)/bin/python scripts/proof_page.py
	$(HEAVY) env PATH="$(CURDIR)/$(VENV)/diffenator/bin:$$PATH" diffenator2 proof $(FONTS)/ttf/*.ttf -o build/proof/diffenator2

# Public Sans at SANS_REF_COMMIT, cloned once into SANS_REF (its fonts/ttf holds the built TTFs).
$(SANS_REF)/fonts/ttf:
	rm -rf $(SANS_REF)
	git clone --filter=blob:none --no-checkout https://github.com/uswds/public-sans.git $(SANS_REF)
	git -C $(SANS_REF) checkout -q $(SANS_REF_COMMIT)

# Compare the current build with Public Sans. Output: build/diff-public-sans
diff-public-sans: $(SANS_REF)/fonts/ttf
	@test -d $(FONTS)/ttf || (echo "Run 'make build' first" && exit 1)
	$(DIFFENATOR2) diff -fb $(SANS_REF)/fonts/ttf/*.ttf -fa $(FONTS)/ttf/*.ttf -o build/diff-public-sans

# Build origin/main in a plain copy of its files (MAIN_REF, made with git archive rather than
# a registered worktree, which would outlive the checkout it sits in), then compare the
# current build with it. The copy is rebuilt when origin/main has moved. Output: build/diff-main
diff-main:
	@test -d $(FONTS)/ttf || (echo "Run 'make build' first" && exit 1)
	@test -n "$(MAIN_REF)" || (echo "MAIN_REF is empty" && exit 1)
	@ref=$$(git rev-parse origin/main) || exit 1; \
	if [ ! -d "$(MAIN_REF)/$(FONTS)/ttf" ] || [ "$$(cat "$(MAIN_REF)/.main-commit" 2>/dev/null)" != "$$ref" ]; then \
	  echo "Building origin/main $$ref in $(MAIN_REF)"; \
	  git worktree remove --force "$(MAIN_REF)" 2>/dev/null; \
	  rm -rf "$(MAIN_REF)" && mkdir -p "$(MAIN_REF)" && \
	  git archive "$$ref" | tar -x -C "$(MAIN_REF)" && \
	  (cd "$(MAIN_REF)/sources" && $(HEAVY) gftools builder config-OffentligSans.yaml) && \
	  echo "$$ref" > "$(MAIN_REF)/.main-commit" || exit 1; \
	fi
	$(DIFFENATOR2) diff -fb $(MAIN_REF)/$(FONTS)/ttf/*.ttf -fa $(FONTS)/ttf/*.ttf -o build/diff-main

specimen:
	$(VENV)/bin/python scripts/specimen.py

social-preview:
	$(VENV)/bin/python scripts/specimen.py --social

install:
	@test -d $(FONTS)/otf || (echo "Run 'make build' first" && exit 1)
	mkdir -p "$$HOME/Library/Fonts"
	cp $(FONTS)/otf/OffentligSans-*.otf "$$HOME/Library/Fonts/"

qa:
	mkdir -p build
	-$(HEAVY) $(FONTSPECTOR) -p universal --skip-network --json build/fsp-universal.json $(FONTS)/ttf/*.ttf $(FONTS)/variable/*.ttf > build/fsp-universal.txt
	-$(HEAVY) $(FONTSPECTOR) -p opentype --skip-network --json build/fsp-opentype.json $(FONTS)/ttf/*.ttf $(FONTS)/variable/*.ttf > build/fsp-opentype.txt
	@status=0; \
	for r in universal opentype; do \
	  $(VENV)/bin/python scripts/fsp_summary.py build/fsp-$$r.json || status=1; \
	done; \
	exit $$status

verify:
	./scripts/verify_commit.sh

clean:
	rm -rf fonts build
