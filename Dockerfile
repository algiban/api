FROM python:3.10-slim

# Buat folder kerja
WORKDIR /app

# Salin file proyek
COPY . .

# Install dependency
RUN pip install --no-cache-dir -r requirements.txt

# Jalankan aplikasi
CMD ["python", "app.py"]
