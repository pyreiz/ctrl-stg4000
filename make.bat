@ECHO OFF
if "%1" == "" goto help

if "%1" == "help" (
	:help
    echo.Please use `make ^<target^>` where ^<target^> is one of
	echo.  test       to run pytest, mpyp and coverage html
	goto end

:end