# DESIGN.md — Branch-Queue

Solo biblioteca estandar: `collections.deque`, `datetime`. Sin persistencia.

## 1. Por que una cola separada por tipo de servicio es mas eficiente que una unica cola compartida

Estructura actual: `dict[str, deque[Ticket]]` — una `deque` FIFO por cada servicio en
`("deposito", "retiro", "gestion_cuenta")`, mas un contador global `_contador`.

`call_next(service_type)` hace:

1. Validar servicio: `O(1)` (lookup en tupla/dict).
2. `cola = self._colas[service_type]`: `O(1)`.
3. `cola.popleft()`: `O(1)` en `deque`.

Costo total: **`O(1)`**, sin recorrer nada.

Con una unica cola compartida (`deque` o `list` global con todos los tickets mezclados),
`call_next("deposito")` tendria que buscar el primer ticket de ese servicio saltando los
de otros servicios:

- Recorrido lineal `O(n)` en el peor caso (ej: 100 retiros antes del primer deposito).
- Si se usa `list.pop(0)` o `del lista[i]`, cada atencion mueve todos los elementos
  posteriores en memoria: `O(n)` por llamada.
- `peek_next` y `list_waiting` sufririan el mismo escaneo en cada llamada.

En cambio, con colas separadas cada operacion toca solo su cola: `popleft/append/[0]/len`
son `O(1)`, `list_waiting()` es `O(n)` solo porque copia lo que va a mostrar (inevitable),
y `stats()` es `O(k)` con `k = numero de servicios (3)`, no `O(n)`.

Compromiso consciente: se pierde el orden global de llegada entre servicios (el ticket #2
de retiro puede atenderse antes que el #3 de deposito). Es lo deseado aqui: cada agente
atiende solo su propia cola, y la numeracion global (`_contador`) se conserva solo como
auditoria/FIFO dentro de cada servicio.

## 2. Que pasa si dos agentes del mismo servicio llaman a `call_next` al mismo tiempo

Escenario: cola `deposito = [A, B]`, dos agentes ejecutan `call_next("deposito")`
concurrentemente (hilos, o dos procesos contra el mismo objeto en memoria).

Sin sincronizacion, ambos podrian leer `cola[0] == A` antes de que ninguno retire,
y ambos atenderian a A (doble llamado), dejando B sin atender y A atendido dos veces.

Mutacion que debe ocurrir primero: **el `popleft()` (extraccion) debe ser atomico
respecto a la lectura**. El orden correcto es:

1. Adquirir exclusion mutua de esa cola (ej: `threading.Lock` por servicio).
2. Comprobar vacia -> retornar `None` (o mensaje) sin mutar.
3. `ticket = cola.popleft()` **dentro del lock** — esta es la mutacion critica y debe
   ocurrir antes de devolver/mostrar el ticket a nadie.
4. Liberar el lock y recien entonces retornar `ticket`.

Nunca: leer `cola[0]`, mostrarlo / imprimirlo / asignarlo a un agente, y despues
`popleft()`. Esa ventana entre lectura y extraccion es la condicion de carrera.

En CPython el GIL hace que un `deque.popleft()` aislado sea atomico en la practica,
pero dos sentencias (`if cola: t = cola[0]` ... `popleft()`) ya no lo son. Con hilos
reales se usaria un `Lock`; con procesos / multi-instancia se necesitaria una cola
externa atomica (DB con `SELECT ... FOR UPDATE SKIP LOCKED`, Redis `LPOP`, etc.).
Este proyecto es en memoria y monohilo (CLI), asi que no incluye locks: lo documenta
como limite conocido.
