from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.database import clientes_collection, productos_collection, inscripciones_collection, transacciones_collection
from app.schemas.transaccion import Transaccion
from bson import ObjectId 
from datetime import datetime
from dotenv import load_dotenv
import os


load_dotenv()
router = APIRouter()

print("MAIL_USERNAME:", os.getenv("MAIL_USERNAME"))
print("MAIL_PASSWORD:", os.getenv("MAIL_PASSWORD"))
print("MAIL_FROM:", os.getenv("MAIL_FROM"))


conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "default_user@example.com"),  
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "default_password"),     
    MAIL_FROM=os.getenv("MAIL_FROM", "default_from@example.com"),  
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Notificación de Fondos",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)



async def enviar_correo(email, asunto, cuerpo):
    try:
        mensaje = MessageSchema(
            subject=asunto,
            recipients=[email],
            body=cuerpo,
            subtype="html"
        )
        fm = FastMail(conf)
        await fm.send_message(mensaje)  
        print(f"Correo enviado a {email} con éxito.")
    except Exception as e:
        print(f"Error al enviar correo: {e}")     




def transaccion_serializer(transaccion):
    transaccion["_id"] = str(transaccion["_id"]) if "_id" in transaccion else None
    transaccion["idCliente"] = str(transaccion["idCliente"]) if isinstance(transaccion["idCliente"], ObjectId) else transaccion["idCliente"]
    transaccion["idProducto"] = str(transaccion["idProducto"]) if isinstance(transaccion["idProducto"], ObjectId) else transaccion["idProducto"]
    return transaccion





@router.post("/transacciones/apertura/")
async def suscribirse_fondo(transaccion: Transaccion, background_tasks: BackgroundTasks):
    cliente = clientes_collection.find_one({"id": int(transaccion.idCliente)})
    producto = productos_collection.find_one({"id": int(transaccion.idProducto)})

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if "saldo" not in cliente:
        raise HTTPException(status_code=400, detail="El cliente no tiene un saldo definido. Por favor, verifique la base de datos.")
    if cliente["saldo"] < producto["monto_minimo"]:
        raise HTTPException(status_code=400, detail=f"No tiene saldo disponible para vincularse al fondo {producto['nombre']}")
    
    nuevo_saldo = cliente["saldo"] - producto["monto_minimo"]
    clientes_collection.update_one({"id": int(transaccion.idCliente)}, {"$set": {"saldo": nuevo_saldo}})


    inscripcion = {
        "idCliente": int(transaccion.idCliente),
        "idProducto": int(transaccion.idProducto),
        "fecha": datetime.now(),
        "tipo": "apertura",
        "monto": producto["monto_minimo"]
    }
    inscripciones_collection.insert_one(inscripcion)

    
    transaccion_data = {
        "idCliente": int(transaccion.idCliente),
        "idProducto": int(transaccion.idProducto),
        "fecha": datetime.now(),
        "tipo": "apertura",
        "monto": producto["monto_minimo"]
    }
    transacciones_collection.insert_one(transaccion_data)  

   
    if cliente["email"]:
        background_tasks.add_task(
            enviar_correo,
            cliente["email"],
            "Suscripción Exitosa",
            f"Te has suscrito exitosamente al fondo {producto['nombre']} con un monto de {producto['monto_minimo']}"
        )
    return {
        "mensaje": f"Suscripción al fondo {producto['nombre']} realizada con éxito",
        "nuevo_saldo": nuevo_saldo,
        "notificacion": f"Se ha enviado una notificación a {cliente['email']} sobre la suscripción."
    }




@router.post("/transacciones/cancelacion/")
async def cancelar_suscripcion(transaccion: Transaccion, background_tasks: BackgroundTasks):
    inscripcion = inscripciones_collection.find_one({"idCliente": int(transaccion.idCliente), "idProducto": int(transaccion.idProducto)})
    if not inscripcion:
        raise HTTPException(status_code=404, detail="El cliente no está suscrito a este fondo")

    
    producto = productos_collection.find_one({"id": int(transaccion.idProducto)})    
    cliente = clientes_collection.find_one({"id": int(transaccion.idCliente)})

    nuevo_saldo = cliente["saldo"] + producto["monto_minimo"]
    clientes_collection.update_one({"id": int(transaccion.idCliente)}, {"$set": {"saldo": nuevo_saldo}})

    
    inscripciones_collection.delete_one({"idCliente": int(transaccion.idCliente), "idProducto": int(transaccion.idProducto)})

    
    cancelacion = {
        "idCliente": int(transaccion.idCliente),
        "idProducto": int(transaccion.idProducto),
        "fecha": datetime.now(),
        "tipo": "cancelacion",
        "monto": producto["monto_minimo"]
    }
    transacciones_collection.insert_one(cancelacion)


    if cliente.get("email"):
        background_tasks.add_task(
            enviar_correo,
            cliente["email"],
            "Cancelación de Suscripción",
            f"Has cancelado tu suscripción al fondo {producto['nombre']}."
        )

    return {
        "mensaje": f"Cancelación del fondo {producto['nombre']} realizada con éxito",
        "nuevo_saldo": nuevo_saldo,
        "notificacion": f"Se ha enviado una notificación a {cliente['email']} sobre la cancelación."
    }

    
    


@router.get("/transacciones/")
async def ver_historial_transacciones(tipo: str = None):
    try:
        if tipo:
            transacciones = list(transacciones_collection.find({"tipo": tipo}))
            if not transacciones:
                return {"mensaje": f"No se encontraron transacciones de tipo '{tipo}'."}
        else:
            transacciones = list(transacciones_collection.find())
            if not transacciones:
                return {"mensaje": "No se encontraron transacciones registradas."}

        
        transacciones_serializadas = [transaccion_serializer(transaccion) for transaccion in transacciones]
        return transacciones_serializadas

    except Exception as e:
        print(f"Error al obtener el historial de transacciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener el historial de transacciones: {str(e)}")
