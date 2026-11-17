.PHONY: all test experiments figures report slides clean help

PYTHON ?= python

help:
	@echo "Available make targets:"
	@echo "  make test         Run all unit tests via pytest"
	@echo "  make experiments  Run batch experiments E1-E5"
	@echo "  make figures      Generate all figures from results"
	@echo "  make report       Build PDF report from LaTeX"
	@echo "  make slides       Generate 17-slide presentation deck"
	@echo "  make all          Run full end-to-end pipeline"

test:
	$(PYTHON) -m pytest tests/ -v

experiments:
	$(PYTHON) experiments/run_experiments.py

figures:
	$(PYTHON) analysis/plots.py
	$(PYTHON) analysis/tables.py

report:
	cd report && pdflatex -interaction=nonstopmode report.tex && pdflatex -interaction=nonstopmode report.tex

slides:
	$(PYTHON) slides/generate_slides.py

all: test experiments figures report slides
