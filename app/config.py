from pymongo import MongoClient
from dotenv import load_dotenv
from pymongo import MongoClient
import os


load_dotenv(dotenv_path=".env")


try:
    client = MongoClient("mongodb://localhost:27017")
    db = client["BTG"]
    print("Conexión exitosa a MongoDB")
    print("Colecciones en la base de datos 'BTG':", db.list_collection_names())
except Exception as e:
    print("Error al conectar a MongoDB:", e)

print("MAIL_USERNAME:", os.getenv("MAIL_USERNAME"))
print("MAIL_PASSWORD:", os.getenv("MAIL_PASSWORD"))
print("MAIL_FROM:", os.getenv("MAIL_FROM"))


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "BTG") 


client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]


print(f"Conectando a MongoDB en: {MONGO_URI}")
print(f"Usando la base de datos: {DATABASE_NAME}")
