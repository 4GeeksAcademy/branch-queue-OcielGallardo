"""Demo CLI del sistema Branch-Queue. Solo stdlib (input/print)."""

from branch_queue import BranchQueue, EmptyQueueError, VALID_SERVICES


def format_ticket(ticket):
    if ticket is None:
        return "(nadie en espera)"
    return (
        f"#{ticket.number} {ticket.client_name} "
        f"[{ticket.service_type}] llegada={ticket.issued_at:%H:%M:%S}"
    )


def prompt_service():
    print("Tipo de servicio:")
    for i, service in enumerate(VALID_SERVICES, start=1):
        print(f"  {i}) {service}")
    eleccion = input("Elige numero o nombre: ").strip().lower()
    if eleccion in ("1", "2", "3"):
        return VALID_SERVICES[int(eleccion) - 1]
    return eleccion


def main():
    queue = BranchQueue()
    print("=== Branch-Queue (fila de banco, en memoria) ===")
    while True:
        print("\n1) Emitir ticket  2) Llamar siguiente  3) Peek siguiente")
        print("4) Listar en espera  5) Stats globales  0) Salir")
        op = input("> ").strip()
        try:
            if op == "1":
                client_name = input("Nombre del cliente: ")
                service_type = prompt_service()
                print("Emitido:", format_ticket(queue.issue_ticket(client_name, service_type)))
            elif op == "2":
                print("Atendiendo:", format_ticket(queue.call_next(prompt_service())))
            elif op == "3":
                print("Siguiente:", format_ticket(queue.peek_next(prompt_service())))
            elif op == "4":
                waiting = queue.list_waiting()
                for service in VALID_SERVICES:
                    print(f"-- {service} --")
                    tickets = waiting[service]
                    if not tickets:
                        print("   (vacio)")
                    for t in tickets:
                        print("  ", format_ticket(t))
            elif op == "5":
                stats = queue.stats()
                print("Por servicio:", stats["per_service"])
                print("Total en espera:", stats["total"])
            elif op == "0":
                print("Fin (los tickets en memoria se descartan).")
                break
            else:
                print("Opcion no valida.")
        except (ValueError, EmptyQueueError) as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
