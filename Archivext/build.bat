cd /d %~dp0
pipenv run python -B -m PyInstaller --distpath=pyinstaller/dist/ --workpath=pyinstaller/build/ --clean --log-level=INFO  Archivext.spec
