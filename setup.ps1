# Script de inicialización del entorno ANA
# Este script activa el entorno virtual e instala las dependencias necesarias

Write-Host "=== Configuración del entorno ANA ===" -ForegroundColor Cyan

# Verificar si el entorno virtual existe
if (-not (Test-Path "ana_env")) {
    Write-Host "El entorno virtual no existe. Creándolo..." -ForegroundColor Yellow
    python -m venv ana_env
    Write-Host "Entorno virtual creado." -ForegroundColor Green
}

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
& .\ana_env\Scripts\Activate.ps1

# Actualizar pip
Write-Host "Actualizando pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Instalar dependencias
Write-Host "Instalando dependencias desde requirements.txt..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host "" -ForegroundColor Green
Write-Host "=== Configuración completada ===" -ForegroundColor Green
Write-Host "El entorno está listo. Para activarlo manualmente en el futuro, ejecuta:" -ForegroundColor Cyan
Write-Host "  .\ana_env\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "" -ForegroundColor Green
Write-Host "Para ejecutar la aplicación:" -ForegroundColor Cyan
Write-Host "  python main.py" -ForegroundColor White
