@echo off

REM Diretório onde o repositório será clonado
set "REPO_DIR=C:\Users\rafae\Desktop\Migracao"

REM URL do repositório Git
set "REPO_URL=https://github.com/rafated/BALANCADELIVERY"

REM Definir os arquivos que deseja clonar
set "FILES_TO_CLONE=GUI_pesagem.py recibo_processing.py"

REM Caminho para o script .bat que será executado após o clone
set "BAT_SCRIPT=C:\Users\rafae\Desktop\Migracao\scripts_apoio\reiniciar_balanca.bat"

REM Remover repositório Git existente se já existir
if exist "%REPO_DIR%\.git" (
    rmdir /s /q "%REPO_DIR%\.git"
)

REM Criar o diretório de clone, se não existir
if not exist "%REPO_DIR%" (
    mkdir "%REPO_DIR%"
)

REM Navegar para o diretório de destino
cd /d "%REPO_DIR%"

REM Inicializar o repositório Git
git init

REM Adicionar o repositório remoto
git remote add origin "%REPO_URL%"

REM Ativar o Sparse Checkout
git config core.sparseCheckout true

REM Criar o arquivo sparse-checkout com os arquivos que você deseja clonar
(for %%f in (%FILES_TO_CLONE%) do (
    echo %%f
)) > "%REPO_DIR%\.git\info\sparse-checkout"

REM Fazer o pull para obter apenas os arquivos especificados
REM Verificar o branch principal: main ou master
git ls-remote --heads origin main

git pull origin master


REM Mensagem de sucesso para o clone parcial
echo Clone parcial realizado com sucesso!

REM Executar o arquivo .bat após o processo de clone
echo Executando o script BAT...
cmd.exe /c "%BAT_SCRIPT%"

echo Script BAT executado com sucesso!
pause
