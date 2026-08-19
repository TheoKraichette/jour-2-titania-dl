FROM python:3.12-slim

WORKDIR /app

# L'index CPU-only : sans lui, pip tire les paquets CUDA (~3 Go) pour rien.
COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    --extra-index-url https://pypi.org/simple -r requirements.txt

COPY main.py .
COPY bureau/ ./bureau/

ENV PYTHONUNBUFFERED=1
# Le conteneur n'a que les coeurs de l'hôte : torch en prend trop par défaut et
# passe son temps à se synchroniser. Ajustable au lancement.
ENV OMP_NUM_THREADS=4

CMD ["python", "main.py"]
