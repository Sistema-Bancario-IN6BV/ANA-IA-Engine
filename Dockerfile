# --- Fase 4: imagen de desarrollo de ANA-IA-Engine ---
# (En la Fase 8 añadiremos etapas de build multi-stage para producción)

FROM python:3.11-slim

WORKDIR /usr/src/app

# tesseract-ocr/poppler-utils: binarios de sistema que pytesseract/pdf2image
# invocan por debajo (no son paquetes de pip). curl: usado solo por el healthcheck.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-spa \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# --extra-index-url trae los wheels CPU-only de PyTorch (sin CUDA), sin tener
# que modificar requirements.txt.
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
