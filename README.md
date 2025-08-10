# Cache Distribuido con FastAPI, SQLite y Docker

Este proyecto implementa un sistema de caché distribuido, con persistencia local por nodo en SQLite, API HTTP con FastAPI y replicación best-effort entre nodos.

## Tecnologías
- FastAPI (API HTTP y validación)
- Uvicorn (ASGI server)
- Pydantic (modelos de datos)
- SQLite (persistencia local por nodo)
- httpx (replicación asíncrona entre nodos)
- Docker / Docker Compose (orquestación de nodos)
- Pytest (tests)

## Estructura
- `server/main.py`: Endpoints y lógica de negocio (memoria + TTL + versionado + replicación)
- `server/persistence.py`: Acceso a SQLite (creación de tabla, guardar, cargar, borrar)
- `server/config.py`: Configuración (variables de entorno, rutas internas, path DB)
- `server/utils/replication.py`: Replicación HTTP a otros nodos
- `server/schemas/cache_item.py`: Modelo de entrada para items del caché
- `docker-compose.yml`: Define 3 nodos del clúster
- `Dockerfile`: Imagen base Python 3.11 con app y dependencias
- `postman/cache-demo-collection.json`: Colección para probar

---

## Ejecución local (sin Docker)

### Requisitos
- Python 3.11+

### 1) Crear y activar entorno virtual
- Windows (PowerShell):
  ```powershell
  python -m venv .venv
  . .venv\Scripts\Activate.ps1
  ```
- macOS / Linux (bash):
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 2) Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3) Ejecutar la API
```bash
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```
- Documentación interactiva: `http://localhost:8001/docs`

### 4) Ejecutar tests
```bash
pytest -q
```

> Nota: el proyecto inicializa la base de datos al importar `server/persistence.py`, por lo que los tests funcionan sin eventos de startup.

---

## Ejecución con Docker (1 nodo)

```bash
docker build -t jikkosoft-cache .

docker run --rm -p 8001:8000 \
  -e NODE_ID=node1 \
  -e NODES="http://localhost:8001" \
  -e INTERNAL_TOKEN=secret \
  -v $(pwd)/data/node1:/app/data \
  jikkosoft-cache
```
- API en `http://localhost:8001`
- Docs en `http://localhost:8001/docs`

> En Windows PowerShell, sustituye `$(pwd)` por la ruta absoluta del proyecto, por ejemplo: `-v C:\ruta\al\repo\data\node1:/app/data`.

---

## Ejecución con Docker Compose (clúster de 3 nodos)

```bash
docker compose up --build
```
Nodos:
- Node 1: `http://localhost:8001`
- Node 2: `http://localhost:8002`
- Node 3: `http://localhost:8003`

Cada servicio monta su directorio de datos persistente: `./data/nodeX -> /app/data`.

Variables de entorno relevantes:
- `NODE_ID`: `node1` | `node2` | `node3`
- `NODES`: lista separada por comas de URLs internas de los nodos
- `INTERNAL_TOKEN`: token compartido para llamadas internas y evitar bucles de replicación

---

## Endpoints principales

- PUT `/cache/{key}`
  - Body (JSON):
    ```json
    {
      "value": {"cualquier": "json"},
      "version": 1,
      "ttl_ms": 30000
    }
    ```
  - Respuesta: `{ "status": "stored", "node": "node1" }`
  - Notas:
    - `version` es obligatoria (entero incremental). Se rechaza con 409 si no supera la versión existente.
    - `ttl_ms` es opcional; si se omite, el ítem no expira.

- GET `/cache/{key}`
  - Respuesta (200):
    ```json
    {
      "value": {"cualquier": "json"},
      "version": 1,
      "expires_at": "2025-01-01T00:00:00.000000"
    }
    ```
  - 404 si no existe o si expiró (mensaje `Expired` o `Not found`).

- DELETE `/cache/{key}`
  - Respuesta: `{ "status": "deleted", "node": "node1" }`

- GET `/_health`
  - Respuesta: `{ "node": "node1", "status": "ok" }`

### Ejemplos (cURL)

```bash
# Guardar con TTL 30 segundos y versión 1
curl -X PUT "http://localhost:8001/cache/k1" \
  -H "Content-Type: application/json" \
  -d '{"value": {"x": 1}, "version": 1, "ttl_ms": 30000}'

# Consultar
curl "http://localhost:8001/cache/k1"

# Borrar
curl -X DELETE "http://localhost:8001/cache/k1"
```

> Las llamadas internas entre nodos usan la cabecera `X-Internal-Token: <INTERNAL_TOKEN>` y no requieren intervención del cliente.

---

## ¿Cómo funciona el caché distribuido?

### Memoria + Persistencia (Write-through)
- Cada nodo mantiene un diccionario en memoria: `key -> { value, version, expires_at }`.
- En cada `PUT`, se escribe en memoria y también en SQLite (write-through) para durabilidad.
- En el arranque, cada nodo carga sus datos desde SQLite y limpia elementos expirados.

### TTL (caducidad)
- `ttl_ms` define el tiempo de vida. Se computa `expires_at` en UTC.
- En `GET`, si el elemento está expirado, se elimina (memoria + DB) y retorna 404 (`Expired`).
- En el arranque se limpia lo expirado. No hay job de limpieza continuo en segundo plano (simplificación del demo).

### Replicación entre nodos (best-effort, asíncrona)
- En `PUT`/`DELETE` externos, el nodo replica la petición al resto vía HTTP asíncrono (`httpx`).
- Se evita replicar al propio nodo usando su URL interna (`self_internal_url`).
- Se usa `X-Internal-Token` para marcar llamadas internas y evitar bucles.
- Errores de red se ignoran en el demo (eventual consistency): la red o el nodo remoto puede fallar sin bloquear la escritura local.

### Conflictos y Consistencia
- Modelo de consistencia: eventual.
- Resolución de conflictos por versión (Last-Writer-Wins con entero creciente):
  - Si llega un `PUT` con `version <= versión_actual`, se rechaza con 409.
  - Los clientes deben aumentar la versión para cada actualización.
- Dado que la replicación es asíncrona, nodos pueden estar temporalmente desincronizados; con el tiempo convergen.

---

## Cómo este proyecto cumple los objetivos

1) Almacenar y recuperar datos de manera eficiente
- Acceso en memoria O(1) por clave para `GET`/`PUT`/`DELETE`.
- Persistencia SQLite para reinicios sin pérdida.
- Serialización JSON para valores arbitrarios.

2) Manejar problemas de consistencia distribuida
- Replicación asíncrona best-effort entre nodos para disponibilidad.
- Prevención de bucles de replicación con `X-Internal-Token` y autoexclusión por URL.
- Resolución de conflictos con versionado LWW (entero creciente) y 409 en versiones obsoletas.
- Eventual consistency: converge cuando la comunicación se restablece.

3) Proporcionar mecanismos para invalidación y caducidad (TTL)
- `ttl_ms` por item; cálculo de `expires_at` en `PUT`.
- Purga en `GET` cuando expira y limpieza en arranque.
- `DELETE` explícito para invalidación inmediata y replicada.

---

## Variables de entorno
- `NODE_ID` (por defecto `node1`)
- `NODES` (lista de URLs internas separadas por comas)
- `INTERNAL_TOKEN` (por defecto `secret`)

## Colección Postman
Importa `postman/cache-demo-collection.json` y apunta a `http://localhost:8001`, `8002`, `8003` según el nodo.

## Notas y mejoras posibles
- Migrar `@app.on_event("startup")` a manejadores de lifespan (FastAPI) para evitar warnings.
- Añadir un limpiador periódico de expirados.
- Retries/backoff y métricas para replicación.
- Autenticación/autorización para clientes externos.
