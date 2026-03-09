# ANA - Asistente de Análisis Psicológico

Sistema de análisis psicológico con procesamiento de lenguaje natural.

##  Configuración Inicial

### Requisitos Previos
- Python 3.8 o superior
- PowerShell (Windows)

### Instalación

1. **Ejecuta el script de configuración:**
   ```powershell
   .\setup.ps1
   ```
   Este script:
   - Crea el entorno virtual (si no existe)
   - Activa el entorno
   - Instala todas las dependencias

2. **Configura tus credenciales:**
   - Copia `config.example.py` a `config.py`
   - Edita `config.py` y añade tu API key de HuggingFace (opcional)

##  Uso

### Activar el entorno manualmente:
```powershell
.\ana_env\Scripts\Activate.ps1
```

### Ejecutar la aplicación:
```powershell
python main.py
```

##  Estructura del Proyecto

```
ANA/
├── core/                    # Módulos principales
│   ├── analysis_engine.py   # Motor de análisis
│   ├── cognitive_bank.py    # Banco cognitivo
│   ├── decision_engine.py   # Motor de decisiones
│   ├── memory.py            # Sistema de memoria
│   └── personality.py       # Módulo de personalidad
├── models/                  # Modelos de datos
├── services/                # Servicios externos
├── data/                    # Datos del usuario (no versionado)
├── logs/                    # Logs de ejecución (no versionado)
├── main.py                  # Punto de entrada
├── config.py                # Configuración (no versionado)
└── requirements.txt         # Dependencias de Python
```

##  Variables de Configuración

Edita `config.py` para personalizar:
- `USE_HUGGINGFACE`: Usar modelos de HuggingFace (True/False)
- `HUGGINGFACE_API_KEY`: Tu API key de HuggingFace
- `PROACTIVE_INTERVAL_MINUTES`: Intervalo de interacciones proactivas
- `WEIGHTS`: Pesos para el análisis
- `THRESHOLDS`: Umbrales de alerta

##  Notas

- El archivo `config.py` contiene información sensible y está excluido del control de versiones
- Los datos del usuario se almacenan en la carpeta `data/`
- Los logs se guardan en la carpeta `logs/`
