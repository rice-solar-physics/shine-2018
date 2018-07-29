PYTHON=python
OUTDIR=site

all: references build

references:
	$(PYTHON) parse_references.py

build: references
	mkdocs build -d $(OUTDIR)