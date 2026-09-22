"""Tests for the BranchQueue service."""

import unittest

from branch_queue import BranchQueue, EmptyQueueError, VALID_SERVICES


class TestBranchQueue(unittest.TestCase):
    def setUp(self):
        self.queue = BranchQueue()

    def test_global_sequential_numbering(self):
        first = self.queue.issue_ticket("Ana", "deposito")
        second = self.queue.issue_ticket("Luis", "retiro")
        third = self.queue.issue_ticket("Mia", "deposito")
        self.assertEqual((first.number, second.number, third.number), (1, 2, 3))

    def test_ticket_stores_client_and_service(self):
        ticket = self.queue.issue_ticket("Ana", "deposito")
        self.assertEqual(ticket.client_name, "Ana")
        self.assertEqual(ticket.service_type, "deposito")
        self.assertIsNotNone(ticket.issued_at)

    def test_fifo_per_service(self):
        self.queue.issue_ticket("Ana", "deposito")
        self.queue.issue_ticket("Mia", "deposito")
        first = self.queue.call_next("deposito")
        second = self.queue.call_next("deposito")
        self.assertEqual(first.client_name, "Ana")
        self.assertEqual(second.client_name, "Mia")

    def test_services_are_isolated(self):
        self.queue.issue_ticket("Ana", "deposito")
        self.queue.issue_ticket("Luis", "retiro")
        called = self.queue.call_next("deposito")
        self.assertEqual(called.client_name, "Ana")
        self.assertEqual(self.queue.peek_next("retiro").client_name, "Luis")

    def test_peek_does_not_consume(self):
        self.queue.issue_ticket("Ana", "deposito")
        self.assertEqual(self.queue.peek_next("deposito").client_name, "Ana")
        self.assertEqual(self.queue.peek_next("deposito").client_name, "Ana")
        self.assertEqual(self.queue.stats()["total"], 1)

    def test_call_next_raises_descriptive_error_for_empty_queue(self):
        with self.assertRaisesRegex(EmptyQueueError, "retiro"):
            self.queue.call_next("retiro")

    def test_list_waiting_is_grouped_and_ordered(self):
        self.queue.issue_ticket("Ana", "deposito")
        self.queue.issue_ticket("Mia", "deposito")
        self.queue.issue_ticket("Luis", "retiro")
        waiting = self.queue.list_waiting()
        self.assertEqual(
            [ticket.client_name for ticket in waiting["deposito"]], ["Ana", "Mia"]
        )
        self.assertEqual([ticket.client_name for ticket in waiting["retiro"]], ["Luis"])
        self.assertEqual(waiting["gestion_cuenta"], [])
        self.assertEqual(set(waiting), set(VALID_SERVICES))

    def test_stats(self):
        self.queue.issue_ticket("Ana", "deposito")
        self.queue.issue_ticket("Mia", "deposito")
        self.queue.issue_ticket("Luis", "retiro")
        stats = self.queue.stats()
        self.assertEqual(
            stats["per_service"],
            {"deposito": 2, "retiro": 1, "gestion_cuenta": 0},
        )
        self.assertEqual(stats["total"], 3)

    def test_acceptance_scenario(self):
        self.queue.issue_ticket("Ana", "deposito")
        self.queue.issue_ticket("Luis", "retiro")
        self.queue.issue_ticket("Mia", "deposito")
        self.assertEqual(self.queue.peek_next("deposito").number, 1)
        self.assertEqual(self.queue.call_next("deposito").number, 1)
        waiting = self.queue.list_waiting()
        self.assertEqual([ticket.number for ticket in waiting["deposito"]], [3])
        stats = self.queue.stats()
        self.assertEqual(stats["per_service"]["deposito"], 1)
        self.assertEqual(stats["per_service"]["retiro"], 1)
        self.assertEqual(stats["per_service"]["gestion_cuenta"], 0)
        self.assertEqual(stats["total"], 2)

    def test_invalid_service(self):
        with self.assertRaises(ValueError):
            self.queue.issue_ticket("Ana", "caja_rapida")
        with self.assertRaises(ValueError):
            self.queue.call_next("caja_rapida")
        with self.assertRaises(ValueError):
            self.queue.peek_next("caja_rapida")

    def test_empty_client_name(self):
        with self.assertRaises(ValueError):
            self.queue.issue_ticket("   ", "deposito")


if __name__ == "__main__":
    unittest.main()
