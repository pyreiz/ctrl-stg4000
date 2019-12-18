@ECHO OFF
REM Command file for Sphinx documentation

echo %0 %1
if "%1" == "" goto help

if "%1" == "help" (
	:help
    echo.Please use `make ^<target^>` where ^<target^> is one of
	echo.  test       to run pytest, mpyp and coverage html
	goto end
)
if "%1" == "test" (
	:test
	echo.  run pytest %2
    pytest %2
    echo.  run mypy
    mypy
    echo.  run coverage html
    coverage html    
	goto end
)
:end