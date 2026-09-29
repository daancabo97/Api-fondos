# Fondos360

API REST para que un cliente de BTG Pactual maneje sus fondos sin depender de un comercial. FastAPI y MongoDB.

Con ella puede:

1. Suscribirse a un fondo (apertura).
2. Salirse de un fondo (cancelación). El monto de vinculación vuelve al saldo.
3. Ver el historial de aperturas y cancelaciones.
4. Recibir un aviso por email o SMS, según el canal que eligió al registrarse.

Cada transacción tiene un `transaccion_id` propio. El saldo inicial es COP $500.000. Si no alcanza para el monto mínimo del fondo, la API responde: `No tiene saldo disponible para vincularse al fondo <nombre>`.

## Requisitos

- Python 3.10
- MongoDB en local (`mongodb://localhost:27017`)

## Ejecución

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

En Linux o macOS, activa el entorno con `source .venv/bin/activate` y copia el entorno con `cp .env.example .env`.

Con la API en marcha:

- Swagger: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json
- Salud: http://127.0.0.1:8000/health

## Primer uso

El catálogo de fondos lo crea un administrador. El rol no viaja en el registro: primero se crea el usuario y después se promueve en MongoDB.

1. **POST /clientes/** para registrar a quien será admin.

```json
{
  "cliente": {
    "nombre": "Ana",
    "apellidos": "García",
    "ciudad": "Bogotá",
    "saldo": 500000,
    "email": "ana@gmail.com",
    "telefono": "+573001234567",
    "canal_notificacion": "email"
  },
  "password": "Password123*"
}
```

El correo debe ser de `gmail.com`, `outlook.com` o `hotmail.com`. La contraseña pide al menos 8 caracteres, una mayúscula, una minúscula, un número y un carácter de `* # & _ - .`. El teléfono es obligatorio. `canal_notificacion` solo admite `email` o `sms`.

2. En MongoDB, asígnale el rol:

```javascript
db.clientes.updateOne({ email: "ana@gmail.com" }, { $set: { rol: "admin" } })
```

3. **POST /login** con ese email y contraseña. Copia `access_token`, pulsa **Authorize** en Swagger y pega solo el token.

4. **POST /productos/** una vez por fondo:

| id | nombre | monto mínimo | categoría |
|----|--------|--------------|-----------|
| 1 | FPV_BTG_PACTUAL_RECAUDADORA | 75000 | FPV |
| 2 | FPV_BTG_PACTUAL_ECOPETROL | 125000 | FPV |
| 3 | DEUDAPRIVADA | 50000 | FIC |
| 4 | FDO-ACCIONES | 250000 | FIC |
| 5 | FPV_BTG_PACTUAL_DINAMICA | 100000 | FPV |

```json
{ "id": 1, "nombre": "FPV_BTG_PACTUAL_RECAUDADORA", "monto_minimo": 75000, "categoria": "FPV" }
```

5. Registra al cliente que va a operar (otro **POST /clientes/**), inicia sesión con él y autoriza Swagger con su token.

6. Suscripción, historial y salida:

- **POST /transacciones/apertura/** con `{ "idCliente": 1, "idProducto": 1 }`
- **GET /transacciones/** para el historial de ese cliente
- **POST /transacciones/cancelacion/** con el mismo cuerpo para desvincularse

La apertura responde `transaccion_id`, `nuevo_saldo` y `notificacion`.

## Quién puede hacer qué

| Rol | Cómo se obtiene | Qué hace |
|-----|-----------------|----------|
| `cliente` | Lo asigna el servidor en **POST /clientes/** | Ve y opera solo sus datos |
| `admin` | Se escribe en MongoDB (`rol: "admin"`) | Crea y borra el catálogo, lista clientes y cambia saldos |

El nombre del usuario no concede el rol. Tras cambiar `rol` en la base hay que volver a hacer login para que el JWT lo traiga.

Consultar productos, sucursales y disponibilidad no exige token. Crearlos o borrarlos sí exige admin. Transacciones, visitas propias y datos de un cliente exigen el token de ese cliente.

## Notificaciones

Tras una apertura o una cancelación, la API avisa en segundo plano por el canal del cliente.

- **Email:** configura `MAIL_USERNAME`, `MAIL_PASSWORD` y `MAIL_FROM`. En Gmail hace falta una contraseña de aplicación.
- **SMS:** Twilio envía el mensaje si existen `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` y `TWILIO_FROM_NUMBER`. Sin esas variables el SMS queda en el log, no sale al teléfono.

## Variables de entorno

| Variable | Desarrollo | Producción |
|----------|------------|------------|
| `ENVIRONMENT` | `development` | `production` |
| `MONGO_URI` | `mongodb://localhost:27017` | URI del cluster con replica set |
| `DATABASE_NAME` | `BTG` | Nombre de la base |
| `SECRET_KEY` | cualquier valor local | clave larga (`openssl rand -hex 32`) |
| `MAIL_*` | opcional | necesario para email real |
| `TWILIO_*` | opcional | necesario para SMS real |

Con `ENVIRONMENT=production` la API no arranca si `SECRET_KEY` sigue siendo el valor de desarrollo.

En MongoDB standalone el débito del saldo es atómico (`$inc`) y, si falla la inscripción o el registro, se revierte. Si el cluster es un replica set, apertura y cancelación usan una transacción multi-documento.

## Arquitectura

```
app/
├── main.py            # ensambla la aplicación
├── presentation/      # routers, DTOs y JWT
├── business/services/ # reglas de negocio
├── persistence/       # acceso a cada colección
└── database/          # conexión y configuración
```

El detalle está en `docs/ARQUITECTURA_FONDOS360.md`. La consulta SQL de la parte 2 está en `docs/parte2_consulta.sql`.

## Pruebas

Los tests usan la base `BTG_test`, separada de `BTG`.

```bash
pytest test/ -q
ruff check app test
pytest test/ -q --cov=app --cov-fail-under=90
```

GitHub Actions ejecuta ruff y pytest con cobertura mínima del 90 % en cada push o pull request a `main` o `master`.
