@echo off
:: Verifica se o script está sendo executado com privilégios de administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Solicitando direitos de administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: O restante do script começa aqui

rem Fecha o segundo script usando o PID salvo
set /p PID2=<pid_r_processing.txt
if defined PID2 (
    taskkill /PID %PID2% /F
    echo Segundo script fechado com sucesso.
) else (
    echo Erro: PID do segundo script não encontrado.
)

rem Fecha o terceiro script pelo título da janela
taskkill /FI "WINDOWTITLE eq Balanca_McDelivery" /F
echo Terceiro script (GUI) fechado com sucesso.

echo Todos os scripts foram fechados.

rem Inicia o segundo script Python em uma nova janela de console com um título de janela único
cmd /c start "recibo_processing" python "C:/Users/rafae/OneDrive/Desktop/Balv1/Services/Micro_Services/recibo_processing.py"
timeout /t 2 /nobreak > nul

rem Minimiza a janela do segundo script
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

echo Todos os scripts foram iniciados com sucesso, minimizados, e os PIDs foram salvos.
