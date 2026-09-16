"""Demo CLI del sistema Branch-Queue. Solo stdlib (input/print)."""

from branch_queue import SERVICIOS_VALIDOS, BranchQueue


def fmt(ticket):
    if ticket is None:
        return "(nadie en espera)"
    return (
        f"#{ticket.numero} {ticket.cliente} "
        f"[{ticket.servicio}] llegada={ticket.llegada:%H:%M:%S}"
    )


def pedir_servicio():
    print("Tipo de servicio:")
    for i, servicio in enumerate(SERVICIOS_VALIDOS, start=1):
        print(f"  {i}) {servicio}")
    eleccion = input("Elige numero o nombre: ").strip().lower()
    if eleccion in ("1", "2", "3"):
        return SERVICIOS_VALIDOS[int(eleccion) - 1]
    return eleccion


def main():
    q = BranchQueue()
    print("=== Branch-Queue (fila de banco, en memoria) ===")
    while True:
        print("\n1) Emitir ticket  2) Llamar siguiente  3) Peek siguiente")
        print("4) Listar en espera  5) Stats globales  0) Salir")
        op = input("> ").strip()
        try:
            if op == "1":
                cliente = input("Nombre del cliente: ")
                servicio = pedir_servicio()
                print("Emitido:", fmt(q.emitir_ticket(cliente, servicio)))
            elif op == "2":
                print("Atendiendo:", fmt(q.llamar_siguiente(pedir_servicio())))
            elif op == "3":
                print("Siguiente:", fmt(q.peek_siguiente(pedir_servicio())))
            elif op == "4":
                espera = q.listar_en_espera()
                for servicio in SERVICIOS_VALIDOS:
                    print(f"-- {servicio} --")
                    tickets = espera[servicio]
                    if not tickets:
                        print("   (vacio)")
                    for t in tickets:
                        print("  ", fmt(t))
            elif op == "5":
                stats = q.stats_globales()
                print("Por servicio:", stats["por_servicio"])
                print("Total en espera:", stats["total"])
            elif op == "0":
                print("Fin (los tickets en memoria se descartan).")
                break
            else:
                print("Opcion no valida.")
        except ValueError as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
