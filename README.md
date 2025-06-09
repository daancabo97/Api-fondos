# Fondos360

## Cómo ejecutar el proyecto

A). Instale las dependencias:

pip install -r requirements.txt

B). Ejecute el servidor de desarrollo:

uvicorn app.main:app --reload

C). Accede a la documentación interactiva en:

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Notas

- Asegúrese de tener MongoDB corriendo en su máquina.
- Configure las variables de entorno necesarias en un archivo `.env` si usa correo electrónico.
