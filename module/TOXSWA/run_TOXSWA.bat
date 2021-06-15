echo off
set arg1=%1
SET batchpath=%~dp0
%batchpath%\TOXSWA.exe %arg1%
rem START /WAIT %batchpath%\TOXSWA_3.3.7-R.exe %arg1%
rem type NUL > %arg1%.done