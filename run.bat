@echo off
setlocal EnableDelayedExpansion

REM Unified entrypoint script for CSAI4014 Quadrotor Project

if "%1"=="" goto help
if "%1"=="test" goto test
if "%1"=="experiments" goto experiments
if "%1"=="figures" goto figures
if "%1"=="report" goto report
if "%1"=="slides" goto slides
if "%1"=="all" goto all
if "%1"=="help" goto help

:test
echo Running unit test suite...
python -m pytest tests/ -v
goto end

:experiments
echo Running headless batch experiments...
python experiments/run_experiments.py
goto end

:figures
echo Generating figures and tables from results...
python analysis/plots.py
python analysis/tables.py
goto end

:report
echo Compiling LaTeX report...
cd report
pdflatex -interaction=nonstopmode report.tex
pdflatex -interaction=nonstopmode report.tex
cd ..
goto end

:slides
echo Generating presentation slides...
python slides/generate_slides.py
goto end

:all
call :test
call :experiments
call :figures
call :report
call :slides
goto end

:help
echo Usage: run.bat [target]
echo Targets:
echo   test         Run pytest unit tests
echo   experiments  Run simulation experiments (E1 to E5)
echo   figures      Generate publication figures and tables
echo   report       Compile LaTeX report to PDF
echo   slides       Generate slide deck presentation
echo   all          Run full end-to-end pipeline
goto end

:end
