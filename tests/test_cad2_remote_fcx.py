import unittest
import sys
import types
from unittest.mock import patch

# Keep this isolated adapter test independent of the PostgreSQL runtime.
database_connections = types.ModuleType("database_connections")
database_connections.probe_environment = lambda *_args, **_kwargs: {}
database_connections.required_url = lambda *_args, **_kwargs: "postgresql://test"
sys.modules.setdefault("database_connections", database_connections)

import cad2_remote_fcx


class _Client:
    portfolio_called = False

    def market(self):
        return {
            "permissions": {"trading": True, "buy": True, "sell": True},
            "market": {"market_open": True},
            "securities": [{"ticker": "FCX", "price": 12, "previous_price": 10}],
            "price_history": {"FCX": [{
                "recorded_at": "2026-08-15T12:00:00Z",
                "price": 12,
                "volume": 7,
                "buy_volume": 5,
                "sell_volume": 2,
                "trade_count": 3,
            }]},
        }

    def portfolio(self, *_args):
        self.portfolio_called = True
        raise AssertionError("An unlinked market viewer must not request a portfolio")


class _Config:
    community_id = "cad2"


class Cad2RemoteFcxTests(unittest.TestCase):
    def test_unlinked_resident_receives_read_only_live_market(self):
        client = _Client()
        with patch.object(cad2_remote_fcx, "_client", return_value=client), patch.object(
            cad2_remote_fcx.CommunityConfig, "load", return_value=_Config()
        ):
            payload = cad2_remote_fcx.build_market_payload(
                user={"id": 42, "name": "Resident"},
                identity_id="",
                game_bank_balance=0,
                game_bank_synced_at="",
            )

        self.assertTrue(payload["market_open"])
        self.assertEqual(payload["securities"][0]["ticker"], "FCX")
        self.assertEqual(payload["price_history"]["FCX"][0]["volume"], 7)
        self.assertEqual(payload["price_history"]["FCX"][0]["buy_volume"], 5)
        self.assertEqual(payload["price_history"]["FCX"][0]["sell_volume"], 2)
        self.assertEqual(payload["account"]["status"], "unlinked")
        self.assertFalse(payload["trading_access"]["can_trade_equity"])
        self.assertFalse(client.portfolio_called)


if __name__ == "__main__":
    unittest.main()
