# Script para ejecutar ANA con el entorno virtual activado

# Activar entorno virtual
& .\ana_env\Scripts\Activate.ps1

# Ejecutar el servidor FastAPI con Uvicorn
Write-Host "Iniciando servidor ANA en http://localhost:8000" -ForegroundColor Green
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Desactivar al finalizar
deactivate
