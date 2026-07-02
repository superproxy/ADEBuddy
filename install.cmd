@echo off
chcp 65001 > nul
echo ========================================
echo   MyAgentPlugin Install Script
echo ========================================
echo.

echo [1/12] List available plugins...
python scripts\plugin-manager.py list
echo.

echo [2/12] Preparing .agents/skills directory...
if not exist ".agents" mkdir ".agents"
if not exist ".agents\skills" mkdir ".agents\skills"
echo.


echo [5/12] Install office plugin...
if exist "agents\plugins\office.plugin.json" (
    python scripts\plugin-manager.py install agents\plugins\office.plugin.json
)
echo.

echo [6/12] Install dev plugin...
if exist "agents\plugins\dev.plugin.json" (
    python scripts\plugin-manager.py install agents\plugins\dev.plugin.json
)
echo.

echo [7/12] Install frontend-design plugin...
if exist "agents\plugins\frontend-design.plugin.json" (
    python scripts\plugin-manager.py install agents\plugins\frontend-design.plugin.json
)
echo.

echo [8/12] Install productivity plugin...
if exist "agents\plugins\productivity.plugin.json" (
    python scripts\plugin-manager.py install agents\plugins\productivity.plugin.json
)
echo.

echo.

echo [11/12] Install superpowers plugin...
if exist "agents\plugins\superpowers.plugin.json" (
    python scripts\plugin-manager.py install agents\plugins\superpowers.plugin.json
)
echo.

echo [12/12] Initialize environment and sync to IDEs...
python scripts\init-env.py -a Generate
python scripts\init-ide.py -i All -f
echo.

echo ========================================
echo   Install Complete!
echo ========================================
echo.
echo Tip: To install more plugins, run:
echo   python scripts\plugin-manager.py install ^<plugin-file^>
echo.
@REM python scripts\init-ide.py -i trae-cn -f
@REM python scripts\init-ide.py -i Cursor -f
@REM python scripts\init-ide.py -i Codex -f
@REM python scripts\init-ide.py -i OpenCode -f
@REM python scripts\init-ide.py -i IDEA -f
@REM python scripts\init-ide.py -i trae-solo-cn -f
