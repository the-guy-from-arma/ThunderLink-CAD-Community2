import os
import sys
import types
import unittest
from unittest.mock import patch

# Configuration validation must remain testable without a PostgreSQL runtime.
database_connections = types.ModuleType("database_connections")
database_connections.probe_environment = lambda *_args, **_kwargs: {}
database_connections.required_url = lambda *_args, **_kwargs: "postgresql://test"
sys.modules.setdefault("database_connections", database_connections)

import community_config


class CommunityConfigOwnerVariablesTests(unittest.TestCase):
    base_environment = {
        "APP_DATABASE_ROLE": "cad2",
        "COMMUNITY_ID": "community_2",
        "DATABASE_URL": "postgresql://cad2:test@localhost:5432/cad2",
        "ARMA_SERVER_ID": "community-2-arma",
        "ARMA_BRIDGE_API_KEY": "test-bridge-key",
        "FCX_API_URL": "https://fcx.example.test",
        "FCX_API_KEY": "test-fcx-key",
        "FCX_COMMUNITY_ID": "community_2",
        "FCX_REMOTE_MARKET_ENABLED": "true",
        "FCX_GLOBAL_ADMIN_ENABLED": "false",
        "FCX_RUN_INTEGRATED_ENGINE": "0",
        "OWNER_EMAIL": "owner@example.test",
        "OWNER_PASSWORD": "test-owner-password",
        "OWNER_NAME": "CAD 2 Owner",
    }

    def load(self, overrides=None):
        environment = {**self.base_environment, **(overrides or {})}
        with patch.dict(os.environ, environment, clear=True), patch.object(
            community_config, "required_url", return_value=environment["DATABASE_URL"]
        ):
            return community_config.CommunityConfig.load()

    def test_owner_variables_are_required_from_environment(self):
        for variable in ("OWNER_EMAIL", "OWNER_PASSWORD", "OWNER_NAME"):
            with self.subTest(variable=variable):
                with self.assertRaisesRegex(RuntimeError, variable):
                    self.load({variable: ""})

    def test_owner_email_must_be_valid(self):
        with self.assertRaisesRegex(RuntimeError, "OWNER_EMAIL"):
            self.load({"OWNER_EMAIL": "not-an-email"})

    def test_owner_placeholders_are_rejected(self):
        for variable in ("OWNER_EMAIL", "OWNER_PASSWORD", "OWNER_NAME"):
            with self.subTest(variable=variable):
                with self.assertRaisesRegex(RuntimeError, variable):
                    self.load({variable: "CHANGE_ME"})

    def test_valid_owner_variables_pass_preflight_configuration(self):
        config = self.load()
        self.assertEqual(config.community_id, "community_2")


if __name__ == "__main__":
    unittest.main()
