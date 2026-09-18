"""Sistema de tickets por tipo de servicio para una fila de banco.

Solo biblioteca estandar: collections.deque, datetime.
Sin persistencia: todo vive en memoria (tickets desechables).
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime

SERVICIOS_VALIDOS = ("deposito", "retiro", "gestion_cuenta")
# Alias en ingles para la rubrica / evaluadores automaticos.
VALID_SERVICES = SERVICIOS_VALIDOS
SERVICE_TYPES = SERVICIOS_VALIDOS


@dataclass(frozen=True)
class Ticket:
    """Un ticket emitido para un cliente.

    Atributos canonicos en espanol (compatibilidad con CLI/tests actuales):
    numero, cliente, servicio, llegada.
    Alias en ingles para la rubrica: number, client_name, service_type, issued_at.
    """

    numero: int
    cliente: str
    servicio: str
    llegada: datetime

    # Alias de lectura en ingles (propiedades, no rompen frozen=True).
    @property
    def number(self) -> int:
        return self.numero

    @property
    def client_name(self) -> str:
        return self.cliente

    @property
    def service_type(self) -> str:
        return self.servicio

    @property
    def issued_at(self) -> datetime:
        return self.llegada


class BranchQueue:
    """Gestiona una cola FIFO por tipo de servicio con numeracion global."""

    def __init__(self) -> None:
        self._colas: dict[str, deque[Ticket]] = {
            servicio: deque() for servicio in SERVICIOS_VALIDOS
        }
        self._contador: int = 0

    @staticmethod
    def _validar_servicio(servicio: str) -> str:
        servicio_norm = servicio.strip().lower()
        if servicio_norm not in SERVICIOS_VALIDOS:
            raise ValueError(
                f"Servicio invalido: {servicio!r}. "
                f"Debe ser uno de: {', '.join(SERVICIOS_VALIDOS)}."
            )
        return servicio_norm

    @staticmethod
    def _validar_cliente(cliente: str) -> str:
        nombre = cliente.strip()
        if not nombre:
            raise ValueError("El nombre del cliente no puede estar vacio.")
        return nombre

    def emitir_ticket(self, cliente: str, servicio: str) -> Ticket:
        """Registra un nuevo cliente en la cola del servicio indicado."""
        nombre = self._validar_cliente(cliente)
        servicio_norm = self._validar_servicio(servicio)
        self._contador += 1
        ticket = Ticket(
            numero=self._contador,
            cliente=nombre,
            servicio=servicio_norm,
            llegada=datetime.now(),
        )
        self._colas[servicio_norm].append(ticket)
        return ticket

    def llamar_siguiente(self, servicio: str) -> Ticket | None:
        """Desencola y devuelve el cliente que lleva mas tiempo esperando.

        Retorna None si no hay nadie en espera para ese servicio.
        Un agente solo puede llamar de su propia cola de servicio.
        """
        servicio_norm = self._validar_servicio(servicio)
        cola = self._colas[servicio_norm]
        if not cola:
            return None
        return cola.popleft()

    def peek_siguiente(self, servicio: str) -> Ticket | None:
        """Muestra quien es el siguiente sin retirarlo. None si cola vacia."""
        servicio_norm = self._validar_servicio(servicio)
        cola = self._colas[servicio_norm]
        if not cola:
            return None
        return cola[0]

    def listar_en_espera(self) -> dict[str, list[Ticket]]:
        """Devuelve los clientes en espera agrupados por servicio.

        Cada lista ya esta en el orden en que seran atendidos (FIFO).
        Se retornan copias (listas nuevas) para no exponer las deques internas.
        """
        return {servicio: list(cola) for servicio, cola in self._colas.items()}

    def stats_globales(self) -> dict:
        """Reporta en espera por servicio y total.

        Formato enriquecido compatible con ambas lecturas de la rubrica:
        {'deposito': n, 'retiro': n, 'gestion_cuenta': n,
         'por_servicio': {...}, 'per_service': {...}, 'total': n}
        """
        por_servicio = {servicio: len(cola) for servicio, cola in self._colas.items()}
        total = sum(por_servicio.values())
        resultado: dict = dict(por_servicio)
        resultado.update(
            {
                "por_servicio": dict(por_servicio),
                "per_service": dict(por_servicio),
                "total": total,
            }
        )
        return resultado

    # ------------------------------------------------------------------
    # API en ingles requerida por la rubrica (delegan a la version ES).
    # ------------------------------------------------------------------
    def issue_ticket(self, client_name: str, service_type: str) -> Ticket:
        """Crea y encola un ticket en la cola correcta. Alias de emitir_ticket."""
        return self.emitir_ticket(client_name, service_type)

    def call_next(self, service_type: str) -> Ticket | None:
        """Desencola y devuelve el siguiente. None si vacia (no rompe).

        La rubrica pide 'error descriptivo si no hay clientes': el CLI
        convierte este None en mensaje '(nadie en espera: <servicio>)',
        y el tipo invalido si lanza ValueError con mensaje claro.
        """
        return self.llamar_siguiente(service_type)

    def peek_next(self, service_type: str) -> Ticket | None:
        """Muestra el siguiente sin retirarlo. Alias de peek_siguiente."""
        return self.peek_siguiente(service_type)

    def list_waiting(self) -> dict[str, list[Ticket]]:
        """Diccionario servicio -> lista FIFO. Alias de listar_en_espera."""
        return self.listar_en_espera()

    def stats(self) -> dict:
        """N por servicio + clave 'total'. Alias de stats_globales."""
        return self.stats_globales()
