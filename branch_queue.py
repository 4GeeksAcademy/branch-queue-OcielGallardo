"""In-memory ticket queues for a bank branch.

    Standard library only: collections.deque and datetime.
    No persistence: everything lives in memory.
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime

VALID_SERVICES = ("deposito", "retiro", "gestion_cuenta")


@dataclass(frozen=True)
class Ticket:
    """A ticket issued for a client."""

    number: int
    client_name: str
    service_type: str
    issued_at: datetime


class EmptyQueueError(Exception):
    """Raised when an agent tries to call an empty service queue."""


class BranchQueue:
    """Manage one FIFO queue per service with global ticket numbering."""

    def __init__(self) -> None:
        self._queues: dict[str, deque[Ticket]] = {
            service: deque() for service in VALID_SERVICES
        }
        self._counter: int = 0

    @staticmethod
    def _validate_service(service_type: str) -> str:
        service = service_type.strip().lower()
        if service not in VALID_SERVICES:
            raise ValueError(
                f"Servicio invalido: {service_type!r}. "
                f"Debe ser uno de: {', '.join(VALID_SERVICES)}."
            )
        return service

    @staticmethod
    def _validate_client(client_name: str) -> str:
        name = client_name.strip()
        if not name:
            raise ValueError("El nombre del cliente no puede estar vacio.")
        return name

    def issue_ticket(self, client_name: str, service_type: str) -> Ticket:
        """Register a new client in the selected service queue."""
        name = self._validate_client(client_name)
        service = self._validate_service(service_type)
        self._counter += 1
        ticket = Ticket(
            number=self._counter,
            client_name=name,
            service_type=service,
            issued_at=datetime.now(),
        )
        self._queues[service].append(ticket)
        return ticket

    def call_next(self, service_type: str) -> Ticket:
        """Remove and return the longest-waiting client for a service."""
        service = self._validate_service(service_type)
        queue = self._queues[service]
        if not queue:
            raise EmptyQueueError(
                f"No hay clientes esperando para '{service}'. "
                "Puedes atender otro servicio disponible."
            )
        return queue.popleft()

    def peek_next(self, service_type: str) -> Ticket | None:
        """Return the next client without removing it."""
        service = self._validate_service(service_type)
        queue = self._queues[service]
        if not queue:
            return None
        return queue[0]

    def list_waiting(self) -> dict[str, list[Ticket]]:
        """Return waiting clients grouped by service in FIFO order."""
        return {service: list(queue) for service, queue in self._queues.items()}

    def stats(self) -> dict:
        """Return waiting counts per service and their total."""
        per_service = {service: len(queue) for service, queue in self._queues.items()}
        total = sum(per_service.values())
        result: dict = dict(per_service)
        result.update({"per_service": dict(per_service), "total": total})
        return result
