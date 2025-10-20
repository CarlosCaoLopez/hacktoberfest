# Imagen base
FROM python:3.10-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de la app
COPY . /app

# Instalar dependencias
RUN pip install --no-cache-dir streamlit requests python-dotenv

# Exponer el puerto de Streamlit
EXPOSE 8001

# Comando de arranque
CMD ["streamlit", "run", "chat.py", "--server.port=8001", "--server.address=0.0.0.0"]
