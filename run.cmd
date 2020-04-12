@ECHO off

:: setup
PUSHD "%~dp0"
FOR /F "tokens=* USEBACKQ" %%F IN (`powershell "$datetime=Get-Date -format 'yyyy-MM-dd,HH.mm.ss';write-host $datetime"`) DO SET "dt=%%~F"
REM alternative: SET "temp_folder=.\temp"
SET "temp_folder=%TEMP%\%RANDOM%%RANDOM%%RANDOM%%RANDOM%"
SET "pptx_file_path="%temp_folder%\newCPU.pptx""
SET "pptx_archive_file_path="%temp_folder%\newCPU.zip""
SET "decompressed_path=".\pptx_content""
SET "pptx_backup_file_path="%temp_folder%\newCPU_%dt%.pptx""
for %%F in ("%pptx_file_path%") DO SET "pptx_file_path_name=%%~nxF"
for %%F in ("%pptx_archive_file_path%") DO SET "pptx_archive_file_path_name=%%~nxF"
mkdir "%temp_folder%"

:: compiling from files to pptx
ECHO.
ECHO.
ECHO now "compiling" files to pptx...
IF EXIST %pptx_file_path% MOVE %pptx_file_path% %pptx_backup_file_path%
REM next line is necessary to fix compress-archive limitation
powershell Get-ChildItem -Path %decompressed_path% -File -Recurse ^| %% {$_.LastWriteTime = ^(Get-Date)}
powershell Get-ChildItem %decompressed_path% -Recurse ^| Compress-Archive -Force -CompressionLevel NoCompression -DestinationPath %pptx_archive_file_path%
REN %pptx_archive_file_path% %pptx_file_path_name%
ECHO ...done

:: opening powerpoint
ECHO.
ECHO.
ECHO now opening compiled file...
ECHO ^!^!^! please keep this window open until you finished editing
START /wait "" %pptx_file_path%

:: decompressing pptx
ECHO.
ECHO.
ECHO ...pptx file closed, updating decompressed folder...
REN %pptx_file_path% %pptx_archive_file_path_name%
RMDIR /s /q %decompressed_path%
powershell Expand-Archive -Path %pptx_archive_file_path% -DestinationPath %decompressed_path%
DEL /q %pptx_archive_file_path%
ECHO ...done

:: ending
rmdir "%temp_folder%"
ECHO.
ECHO.
ECHO all done!
POPD
PAUSE