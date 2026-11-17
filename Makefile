.PHONY: all test experiments figures report slides demo help

PYTHON ?= python

help:
	@echo "make test         unit tests (pytest)"
	@echo "make experiments  run all Webots scenarios headless (about 20 min)"
	@echo "make figures      figures, tables, report numbers and video script"
	@echo "make report       build report/report.pdf"
	@echo "make slides       build slides/slides.pptx and slides.pdf"
	@echo "make demo         live rendered demo (square mission, Method B)"
	@echo "make all          everything above except the demo"

test:
	$(PYTHON) -m pytest tests/ -q

experiments:
	$(PYTHON) experiments/run_experiments.py

figures:
	$(PYTHON) analysis/plots.py
	$(PYTHON) analysis/tables.py

report: figures
	cd report && pdflatex -interaction=nonstopmode report.tex && pdflatex -interaction=nonstopmode report.tex \
	  && $(PYTHON) page_counts.py && pdflatex -interaction=nonstopmode report.tex

slides: figures
	$(PYTHON) slides/generate_slides.py

demo:
	$(PYTHON) experiments/demo.py E2 improved

all: test experiments report slides
