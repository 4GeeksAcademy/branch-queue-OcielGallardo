"""Tests del sistema Branch-Queue. Solo stdlib (unittest)."""

import unittest

from branch_queue import BranchQueue, SERVICIOS_VALIDOS


class TestBranchQueue(unittest.TestCase):
    def setUp(self):
        self.q = BranchQueue()

    def test_numeracion_global_secuencial(self):
        t1 = self.q.emitir_ticket("Ana", "deposito")
        t2 = self.q.emitir_ticket("Luis", "retiro")
        t3 = self.q.emitir_ticket("Mia", "deposito")
        self.assertEqual((t1.numero, t2.numero, t3.numero), (1, 2, 3))

    def test_registra_datos_del_ticket(self):
        t = self.q.emitir_ticket("Ana", "deposito")
        self.assertEqual(t.cliente, "Ana")
        self.assertEqual(t.servicio, "deposito")
        self.assertIsNotNone(t.llegada)

    def test_fifo_por_servicio(self):
        self.q.emitir_ticket("Ana", "deposito")
        self.q.emitir_ticket("Mia", "deposito")
        primero = self.q.llamar_siguiente("deposito")
        segundo = self.q.llamar_siguiente("deposito")
        self.assertEqual(primero.cliente, "Ana")
        self.assertEqual(segundo.cliente, "Mia")

    def test_aislamiento_entre_servicios(self):
        self.q.emitir_ticket("Ana", "deposito")
        self.q.emitir_ticket("Luis", "retiro")
        llamado = self.q.llamar_siguiente("deposito")
        self.assertEqual(llamado.cliente, "Ana")
        # La otra cola no se toca
        siguiente_retiro = self.q.peek_siguiente("retiro")
        self.assertEqual(siguiente_retiro.cliente, "Luis")

    def test_peek_no_consume(self):
        self.q.emitir_ticket("Ana", "deposito")
        self.assertEqual(self.q.peek_siguiente("deposito").cliente, "Ana")
        self.assertEqual(self.q.peek_siguiente("deposito").cliente, "Ana")
        self.assertEqual(self.q.stats_globales()["total"], 1)

    def test_cola_vacia_retorna_none(self):
        self.assertIsNone(self.q.llamar_siguiente("deposito"))
        self.assertIsNone(self.q.peek_siguiente("retiro"))

    def test_listar_en_espera_agrupado_y_ordenado(self):
        self.q.emitir_ticket("Ana", "deposito")
        self.q.emitir_ticket("Mia", "deposito")
        self.q.emitir_ticket("Luis", "retiro")
        espera = self.q.listar_en_espera()
        self.assertEqual([t.cliente for t in espera["deposito"]], ["Ana", "Mia"])
        self.assertEqual([t.cliente for t in espera["retiro"]], ["Luis"])
        self.assertEqual(espera["gestion_cuenta"], [])
        self.assertEqual(set(espera.keys()), set(SERVICIOS_VALIDOS))

    def test_stats_globales(self):
        self.q.emitir_ticket("Ana", "deposito")
        self.q.emitir_ticket("Mia", "deposito")
        self.q.emitir_ticket("Luis", "retiro")
        stats = self.q.stats_globales()
        self.assertEqual(
            stats["por_servicio"],
            {"deposito": 2, "retiro": 1, "gestion_cuenta": 0},
        )
        self.assertEqual(stats["total"], 3)

    def test_escenario_aceptacion(self):
        self.q.emitir_ticket("Ana", "deposito")  # #1
        self.q.emitir_ticket("Luis", "retiro")  # #2
        self.q.emitir_ticket("Mia", "deposito")  # #3
        self.assertEqual(self.q.peek_siguiente("deposito").numero, 1)
        self.assertEqual(self.q.llamar_siguiente("deposito").numero, 1)
        espera = self.q.listar_en_espera()
        self.assertEqual([t.numero for t in espera["deposito"]], [3])
        stats = self.q.stats_globales()
        self.assertEqual(stats["por_servicio"]["deposito"], 1)
        self.assertEqual(stats["por_servicio"]["retiro"], 1)
        self.assertEqual(stats["por_servicio"]["gestion_cuenta"], 0)
        self.assertEqual(stats["total"], 2)

    def test_servicio_invalido(self):
        with self.assertRaises(ValueError):
            self.q.emitir_ticket("Ana", "caja_rapida")
        with self.assertRaises(ValueError):
            self.q.llamar_siguiente("caja_rapida")
        with self.assertRaises(ValueError):
            self.q.peek_siguiente("caja_rapida")

    def test_cliente_vacio(self):
        with self.assertRaises(ValueError):
            self.q.emitir_ticket("   ", "deposito")


if __name__ == "__main__":
    unittest.main()
