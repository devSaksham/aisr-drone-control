@echo off
REM Windows equivalent of the Makefile targets. Usage: run.bat [test|experiments|figures|report|slides|demo|all]
setlocal
if "%1"=="" goto help
goto %1

:test
python -m pytest tests/ -q
goto end

:experiments
python experiments/run_experiments.py
goto end

:figures
python analysis/plots.py
python analysis/tables.py
goto end

:report
call :figures
cd report
pdflatex -interaction=nonstopmode report.tex
pdflatex -interaction=nonstopmode report.tex
python page_counts.py
pdflatex -interaction=nonstopmode report.tex
cd ..
goto end

:slides
call :figures
python slides/generate_slides.py
goto end

:demo
python experiments/demo.py E2 improved
goto end

:all
call :test
call :experiments
call :report
call :slides
goto end

:help
echo Usage: run.bat [test^|experiments^|figures^|report^|slides^|demo^|all]

:end
endlocal
