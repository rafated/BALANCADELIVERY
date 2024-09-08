@echo off
:: Verifica se o script está sendo executado com privilégios de administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitando direitos de administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: O restante do seu script começa aqui

rem Inicia o primeiro script Python em uma nova janela de console com um título de janela único
cmd /c start "save_data_printer" python "C:/Users/rafae/OneDrive/Desktop/Balv1/Services/Micro_Services/save_data_printer.py"
timeout /t 2 /nobreak > nul

powershell -command "(New-Object -ComObject Shell.Application).MinimizeAll()"

rem Captura o PID do primeiro script usando o título da janela
for /f "tokens=2 delims=," %%i in ('tasklist /v /fo csv ^| findstr /i "save_data_printer"') do set PID1=%%i

rem Salva o PID do primeiro script
if defined PID1 (
    echo %PID1% > pid_sd_printer.txt
    echo PID do primeiro script salvo: %PID1%
) else (
    echo Erro ao capturar o PID do primeiro script.
)

rem Inicia o segundo script Python em uma nova janela de console com um título de janela único
cmd /c start "recibo_processing" python "C:/Users/rafae/OneDrive/Desktop/Balv1/Services/Micro_Services/recibo_processing.py"
timeout /t 2 /nobreak > nul

powershell -command "(New-Object -ComObject Shell.Application).MinimizeAll()"

rem Captura o PID do segundo script usando o título da janela
for /f "tokens=2 delims=," %%i in ('tasklist /v /fo csv ^| findstr /i "recibo_processing"') do set PID2=%%i

rem Salva o PID do segundo script
if defined PID2 (
    echo %PID2% > pid_r_processing.txt
    echo PID do segundo script salvo: %PID2%
) else (
    echo Erro ao capturar o PID do segundo script.
)

rem Inicia o terceiro script Python em uma nova janela de console com um título de janela único
cmd /c start "gui" python "C:/Users/rafae/OneDrive/Desktop/Balv1/Services/Main_Services/gui_beta.py"
timeout /t 2 /nobreak > nul

echo Todos os scripts foram iniciados com sucesso e os PIDs foram salvos.
