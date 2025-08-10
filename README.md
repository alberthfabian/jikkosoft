## Índice

- [Sección 1 - Arquitectura del Sistema de Juego Multijugador](#sección-1---arquitectura-del-sistema-de-juego-multijugador)
  - [Diagrama General de Arquitectura](#diagrama-general-de-arquitectura)
  - [Diagrama de Componentes](#diagrama-de-componentes)
  - [Diseño Técnico y Arquitectural](#diseño-técnico-y-arquitectural)
  - [Alta concurrencia y baja latencia](#alta-concurrencia-y-baja-latencia)
  - [Consistencia y fiabilidad de los datos](#consistencia-y-fiabilidad-de-los-datos)
  - [Escalabilidad y tolerancia a fallos](#escalabilidad-y-tolerancia-a-fallos)
  - [Seguridad y privacidad](#seguridad-y-privacidad)
  - [Stack tecnológico y justificación](#stack-tecnológico-y-justificación)
  - [Estrategia de almacenamiento y gestión de datos](#estrategia-de-almacenamiento-y-gestión-de-datos)
  - [Mecanismos de escalabilidad](#mecanismos-de-escalabilidad)
  - [Tolerancia a fallos](#tolerancia-a-fallos)
  - [Medidas de seguridad](#medidas-de-seguridad)
  - [Serverless Architecture](#serverless-architecture)
  - [Event-Driven con Scheduler (Cron)](#event-driven-con-scheduler-cron)
  - [Separación Control Plane vs Data Plane](#separación-control-plane-vs-data-plane)
  - [API Gateway Pattern (y Gateway Aggregation)](#api-gateway-pattern-y-gateway-aggregation)
  - [Funciones con Responsabilidad Única (FaaS decomposition)](#funciones-con-responsabilidad-única-faas-decomposition)
  - [CQRS “lite” (Segregación de Lectura/Escritura)](#cqrs-lite-segregación-de-lecturaescritura)
  - [Multi-Region Deployment](#multi-region-deployment)
  - [Read-Local / Replicate-Global (Eventual Consistency)](#read-local--replicate-global-eventual-consistency)
  - [Dead-Letter Queue + Retries](#dead-letter-queue--retries)
  - [Defense in Depth (Seguridad en Capas)](#defense-in-depth-seguridad-en-capas)
  - [Observability Pattern](#observability-pattern)
  - [1. Excelencia Operativa](#1-excelencia-operativa)
  - [2. Seguridad](#2-seguridad)
  - [3. Fiabilidad](#3-fiabilidad)
  - [4. Eficiencia en el Rendimiento](#4-eficiencia-en-el-rendimiento)
  - [5. Optimización de Costos](#5-optimización-de-costos)
  - [6. Sostenibilidad](#6-sostenibilidad)
  - [Estimación de costos mensuales (USD)](#estimación-de-costos-mensuales-usd)

- [Sección 2 - Desafío de Codificación](#sección-2---desafío-de-codificación)
  - [Cache Distribuido con FastAPI, SQLite y Docker](#cache-distribuido-con-fastapi-sqlite-y-docker)
  - [Tecnologías](#tecnologías)
  - [Estructura](#estructura)
  - [Ejecución local (sin Docker)](#ejecución-local-sin-docker)
  - [Ejecución con Docker (1 nodo)](#ejecución-con-docker-1-nodo)
  - [Ejecución con Docker Compose (clúster de 3 nodos)](#ejecución-con-docker-compose-clúster-de-3-nodos)
  - [Endpoints principales](#endpoints-principales)
  - [Patrones de diseño aplicados](#patrones-de-diseño-aplicados)
  - [¿Cómo funciona el caché distribuido?](#cómo-funciona-el-caché-distribuido)
  - [Cómo este proyecto cumple los objetivos](#cómo-este-proyecto-cumple-los-objetivos)
  - [Variables de entorno](#variables-de-entorno)
  - [Colección Postman](#colección-postman)
  - [Notas y mejoras posibles](#notas-y-mejoras-posibles)


# Sección 1 - Arquitectura del Sistema de Juego Multijugador

## Diagrama General de Arquitectura
<p align="center">
  <img src="assets/aws.jpg" width="700" alt="Diagrama AWS">
</p>

## Diagrama de Componentes
<p align="center">
  <img src="assets/component.jpg" width="700" alt="Diagrama de Componentes">
</p>

---

## Diseño Técnico y Arquitectural

1. **Inicio de sesión:** El jugador obtiene su identidad en Cognito.  
2. **Lista de mundos:** El cliente pide a API Gateway la lista de partidas; Lambda consulta DynamoDB y devuelve la información.  
3. **Unirse a una partida:** Otra Lambda revisa que haya espacio y crea la sesión del jugador en GameLift.  
4. **Conexión en tiempo real:** El cliente se conecta directamente al servidor del juego con los datos recibidos.  
5. **Juego activo:** GameLift valida y gestiona la partida, guardando información importante en DynamoDB.  
6. **Mantenimiento:** Un proceso programado revisa partidas activas, inicia o detiene mundos según sea necesario y envía métricas a CloudWatch.  

---

## Alta concurrencia y baja latencia

- **En el borde (Edge):** CloudFront, WAF y Shield reciben las peticiones antes de llegar a la nube. Esto ayuda a manejar miles de conexiones, proteger de ataques y acercar el contenido al jugador.  
- **Plano de control sin servidores:** Usamos API Gateway y funciones Lambda, que se adaptan automáticamente al número de solicitudes sin necesidad de servidores fijos.  
- **Tiempo real optimizado:** La comunicación del juego (movimientos, acciones) va directa al servicio GameLift, reduciendo pasos y ganando velocidad.  
- **Regiones cercanas:** El sistema conecta a cada jugador al servidor más cercano geográficamente para minimizar el retraso.  

---

## Consistencia y fiabilidad de los datos

- DynamoDB con replicación global para que los datos estén disponibles en varias regiones.  
- Datos críticos manejados con reglas de idempotencia para evitar duplicados o errores.  
- El estado real lo mantiene GameLift; DynamoDB guarda información de referencia.  
- Sesiones caducadas se eliminan automáticamente con procesos programados.  

---

## Escalabilidad y tolerancia a fallos

- Diseño horizontal: Lambdas y API Gateway manejan desde pocos hasta miles de jugadores sin cambios manuales.  
- GameLift y DynamoDB en múltiples zonas de disponibilidad y regiones.  
- Reintentos automáticos y colas para manejar fallos temporales.  
- Monitoreo con CloudWatch y X-Ray.  

---

## Seguridad y privacidad

- Amazon Cognito da credenciales temporales con permisos mínimos.  
- WAF y Shield protegen contra ataques.  
- Comunicación cifrada y datos almacenados de forma segura.  
- Servidores aislados en red privada.  
- Mínima información personal almacenada.  

---

## Stack tecnológico y justificación

- **Cliente:** Unity/Unreal → aceleran el desarrollo, redes integradas y fácil integración cloud.  
- **Protección y distribución:** CloudFront + WAF + Shield → respuesta rápida, filtrado y mitigación de ataques.  
- **Autenticación:** Amazon Cognito → identidades seguras sin login propio.  
- **Gestión de solicitudes:** API Gateway + Lambda → escalables y facturación por uso.  
- **Juego en tiempo real:** Amazon GameLift → hosting optimizado para juegos con baja latencia.  
- **Datos:** DynamoDB Global Tables → velocidad y replicación multi-región.  
- **Automatización y monitoreo:** EventBridge, CloudWatch, X-Ray → tareas programadas y visibilidad del sistema.  
- **Seguridad:** IAM → permisos mínimos y controlados.  

---

## Estrategia de almacenamiento y gestión de datos

**Tablas lógicas:**
- **WorldConfiguration:** Configuración fija de cada mundo.  
- **WorldSessions:** Lista de partidas activas y conectados.  
- **WorldPlayerData:** Progreso y estadísticas no críticas.  

**Reglas clave:**
- Validaciones de cupo antes de unir jugadores.  
- Lecturas rápidas y flexibles para lista de mundos.  
- Índices por estado y región.  
- Limpieza automática de partidas viejas.  
- Cifrado y mínima información personal.  

---

## Mecanismos de escalabilidad

- API Gateway y Lambda se adaptan solos al tráfico.  
- DynamoDB ajusta capacidad automáticamente.  
- GameLift escala servidores según demanda.  
- CloudFront distribuye la carga global.  

---

## Tolerancia a fallos

- Multi-zona y multi-región.  
- Capacidad de mover jugadores a otra región.  
- Reintentos automáticos y manejo de errores.  
- Recuperación automática de estados.  

---

## Medidas de seguridad

- Filtrado de tráfico malicioso (WAF, Shield).  
- Credenciales temporales (Cognito).  
- Cifrado y aislamiento de servidores.  
- Registros y auditorías.  
- Mínima recolección de datos personales.  


# Serverless Architecture

Lógica en funciones administradas (sin servidores propios) y servicios 100% gestionados.
- AWS Lambda (ListWorlds, JoinWorld, WorldManager), API Gateway, DynamoDB, Cognito, EventBridge, CloudWatch.

---

## Event-Driven con Scheduler (Cron)

Procesos que se ejecutan por eventos; aquí, un temporizador.
- EventBridge dispara WorldManager cada minuto para orquestar mundos/sesiones.

---

## Separación Control Plane vs Data Plane

Un plano de control que crea/gestiona sesiones y un plano de datos que mueve el tráfico de juego en tiempo real.
- Control plane: API Gateway + Lambdas + DynamoDB.
- Data plane: cliente conecta directo a GameLift por TCP.

---

## API Gateway Pattern (y Gateway Aggregation)

Un único punto de entrada HTTP que enruta a múltiples funciones/servicios.
- Amazon API Gateway exponiendo ListWorlds y JoinWorld bajo la misma API.

---

## Funciones con Responsabilidad Única (FaaS decomposition)

Dividir la lógica en funciones pequeñas y enfocadas.
- ListWorlds (lee mundos), JoinWorld (une y crea player session), WorldManager (gestiona/arranca mundos).

---

## CQRS “lite” (Segregación de Lectura/Escritura)

Separar consultas de comandos sin infraestructura adicional compleja.
- ListWorlds (lectura) vs JoinWorld/WorldManager (escritura/actualización).

---

## Multi-Region Deployment

Desplegar y replicar datos en varias regiones para baja latencia/alta disponibilidad.
- DynamoDB Global Tables (WorldConfiguration, WorldSessions, WorldPlayerData) y GameLift multi-Region fleet.
- Persiste/consulta en la región cercana; replica globalmente.

---

## Read-Local / Replicate-Global (Eventual Consistency)

Leer/escribir en la región local y replicar a las demás (aceptando consistencia eventual).
- Dónde se ve: comportamiento nativo de DynamoDB Global Tables usado por Lambdas y GameLift.

---

## Dead-Letter Queue + Retries

Reintentos automáticos y, si fallan, envío a una cola de “cartas muertas” para inspección/recuperación.
- SQS (DLQ) conectado a WorldManager en caso de fallo; Lambda hace retry/backoff.
- “On failure” desde WorldManager a SQS.

---

## Defense in Depth (Seguridad en Capas)

Múltiples barreras en distintas capas.
- Shield (DDoS) + CloudFront (edge) + WAF (reglas) + Cognito (identidad) + IAM (permisos finos).

---

## Observability Pattern

Monitoreo, métricas y trazas centralizadas.
- CloudWatch (logs/métricas) y X-Ray (tracing); Game servers envían métricas.

---

## 1. Excelencia Operativa

Que todo se pueda operar y actualizar sin interrumpir el juego.
- Aquí se usa AWS CDK / CloudFormation para desplegar y actualizar la infraestructura automáticamente.
- Cuando se actualiza la flota de Amazon GameLift, se crea una flota nueva, se prueba y recién después se apaga la anterior, evitando cortes a los jugadores.

---

## 2. Seguridad

Que los jugadores y sistemas estén protegidos en todo momento.
- Amazon Cognito e IAM controlan quién puede acceder a las APIs.
- Solo solicitudes autenticadas pasan por API Gateway.
- Shield y WAF protegen contra ataques en la red y tráfico malicioso.

---

## 3. Fiabilidad

Que el juego siga funcionando incluso si algo falla.
- Si un servidor de juego cae, GameLift lanza uno nuevo con los mismos datos del mundo (almacenados en DynamoDB).
- DynamoDB Global Tables mantiene los datos replicados para que estén siempre disponibles.

---

## 4. Eficiencia en el Rendimiento

Que los jugadores tengan la menor latencia posible y el juego responda rápido.
- GameLift conecta al cliente directo por TCP al servidor más cercano.
- Servidores distribuidos en varias regiones para reducir la distancia física y el retardo.

---

## 5. Optimización de Costos

Pagar solo por lo que realmente usas.
- Lambdas, API Gateway y DynamoDB escalan según el tráfico.
- GameLift ajusta la cantidad de servidores activos según la cantidad de jugadores, evitando pagar por servidores vacíos.

---

## 6. Sostenibilidad

Reducir el impacto ambiental usando solo los recursos necesarios.
- Servicios administrados y sin servidor (serverless) que solo consumen recursos cuando hay actividad.
- Se ejecuta lo justo y necesario para la carga de jugadores en cada momento.

---

## Estimación de costos mensuales (USD)

Se tomó como base un escenario de referencia (≈1.500 usuarios concurrentes CCU, 150 jugadores por mundo, sesiones de 15 min). Esto da un estimado mensual orientativo en `us-east-1`.

Supuestos clave:
- 6k req/h a ListWorlds y 6k req/h a JoinWorld (12k req/h totales)
- WorldManager cada 1 min
- 5 instancias C5.xlarge en GameLift (2 procesos por instancia)
- 40 métricas personalizadas y ~100 MB/h de logs
- Tablas DynamoDB Global Tables (lecturas/escrituras pequeñas ~1 KB)

| Componente | Supuesto de uso mensual (resumen) | Costo aprox/mes |
| --- | --- | --- |
| API Gateway – ListWorlds | 6k req/h | $4.38 |
| Lambda – ListWorlds (128 MB) | 6k inv/h | $10.01 |
| DynamoDB – lecturas (ListWorlds) | 6k lect/h (~1 KB) | $0.55 |
| API Gateway – JoinWorld | 6k req/h | $4.38 |
| Lambda – JoinWorld (128 MB) | 6k inv/h | $10.01 |
| DynamoDB – escrituras (JoinWorld) | 6k esc/h (~1 KB) | $5.47 |
| EventBridge (regla) | 60 eventos/h | $0.00 |
| Lambda – WorldManager (512 MB, ~5 s) | 60 inv/h | $1.83 |
| DynamoDB – R/W (WorldManager) | lect 60/h + esc 600/h | $0.56 |
| Accesos PlayerData (Global Tables) | 6k lect/h + 18k esc/h | $16.98 |
| GameLift – cómputo | 5× C5.xlarge | $847.16 |
| GameLift – transferencia | ~7.5 MB/s totales | $1,726.55 |
| CloudWatch Logs | ~100 MB/h | $36.32 |
| CloudWatch Métricas | ~40 métricas | $12.00 |
| DynamoDB – almacenamiento | ~5.4 GB | $1.38 |
| Cognito Identity Pool | Identidades federadas | $0.00 |
| CloudFront (frente a API) | 8.6 M req/mes, respuestas pequeñas | ~$4.00 |
| AWS WAF (1 ACL, ~10 reglas) | 8.6 M req/mes | ~$20.00 |
| AWS X-Ray | muestreo básico/trazas bajas | ~$3.00 |
| SQS – DLQ | fallos esporádicos | ~$1.00 |
| AWS Shield Standard / IAM | — | $0.00 |

**Total mensual aproximado:** $2,722.56  
**Costo por CCU (≈1,500):** ~$1.82/CCU/mes

Notas:
- Los grandes conductores del costo son GameLift (cómputo) y la transferencia de datos.
- WAF/CloudFront/X-Ray/SQS son relativamente pequeños con este patrón de tráfico.
- Si el tráfico real difiere (más lecturas/escrituras, otras regiones, tamaño de mensajes, más instancias), los números cambian aproximadamente de forma lineal.

# Sección 2 - Desafío de Codificación

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
- `app/app_factory.py`: Factoría de la app (`create_app`) y definición de endpoints. Hace el wiring de `CacheService` + `CacheRepository` + `ConflictResolutionStrategy` y configura la replicación.
- `app/main.py`: Punto de entrada. Crea la app vía la factoría y reexporta `replicate_to_others` para facilitar tests (monkeypatch).
- `app/services/cache_service.py`: Servicio de dominio. TTL/expiración, versionado (LWW), cache en memoria y disparo de replicación.
- `app/infrastructure/sqlite_repository.py`: Implementación de `CacheRepository` usando SQLite (guardar/cargar/borrar, parseo de fechas).
- `app/domain/repositories.py`: Interfaces de repositorios (p. ej., `CacheRepository`).
- `app/domain/conflict_resolution.py`: Estrategia de resolución de conflictos (por defecto `LastWriterWinsByVersion`).
- `app/utils/replication.py`: Replicación HTTP asíncrona a otros nodos, con `X-Internal-Token` y autoexclusión por URL propia.
- `app/persistence.py`: Inicialización de la base (`init_db`) y utilidades de acceso directo (helpers) a SQLite.
- `app/config.py`: Configuración (variables de entorno, rutas internas, path de la base de datos).
- `app/schemas/cache_item.py`: Modelo Pydantic de entrada para ítems del caché.
- `app/tests/`: Pruebas con Pytest. Ejecuta `pytest -q` desde la raíz del proyecto.
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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Documentación interactiva: `http://localhost:8001/docs`

### 4) Ejecutar tests
```bash
pytest -q
```

> Nota: el proyecto inicializa la base de datos al importar `app/persistence.py`, por lo que los tests funcionan sin eventos de startup.

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

### Patrones de diseño aplicados

- Repository (Repositorio)
  - Interfaz: `app/domain/repositories.py` → `CacheRepository`.
  - Implementación: `app/infrastructure/sqlite_repository.py` → `SQLiteCacheRepository`.
  - Propósito: desacoplar la persistencia de la lógica; permite cambiar SQLite por otra tecnología (p. ej., Redis) sin tocar el servicio o los endpoints.

- Service / Fachada
  - Archivo: `app/services/cache_service.py` → `CacheService`.
  - Responsabilidades: TTL y expiración, control de versiones (LWW), acceso al repositorio y disparo de replicación. Mantiene el mapa en memoria (`key -> { value, version, expires_at }`).
  - Beneficio: los endpoints quedan finos y la lógica de dominio es fácilmente testeable.

- Strategy (Estrategia) para resolución de conflictos
  - Interfaz: `app/domain/conflict_resolution.py` → `ConflictResolutionStrategy`.
  - Implementación por defecto: `LastWriterWinsByVersion` (acepta solo si `incoming_version` > `current_version`).
  - Beneficio: se puede sustituir por otras políticas sin cambiar el servicio.

- App Factory + Inyección de dependencias
  - Archivo: `app/app_factory.py` → `create_app()`.
  - Hace el wiring de `CacheService` + `CacheRepository` + `ConflictResolutionStrategy` y configura la replicación.
  - `app/main.py` ahora solo crea la app vía la factoría, manteniendo compatibilidad con los tests.

- Supplier de replicación (facilita tests)
  - Detalle: `CacheService` recibe un proveedor de la función `replicate_to_others`, que se resuelve desde `app.main`.
  - Beneficio: los tests pueden hacer `monkeypatch` de `app.main.replicate_to_others` sin acoplar el servicio a una implementación fija ni introducir latencias.

Extensión futura: se pueden añadir nuevas implementaciones de `CacheRepository` (p. ej., Redis), nuevas estrategias de conflicto, o estrategias de replicación (reintentos/backoff).

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
