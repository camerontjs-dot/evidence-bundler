"""Offline failure witnesses; no API/model invocation or scientific attempt."""
from __future__ import annotations

import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import prepare_writer as route


class TransportFailureWitnesses(unittest.TestCase):
    def setup_receipts(self, root, corrupt=False):
        (root / "writer").mkdir()
        data = b'{"model":"offline-witness","raw":true,"prompt":"witness"}'
        freeze = {"request_sha256": route.digest(data), "route_code_sha256": route.digest(Path(route.__file__).read_bytes())}
        (root / "WRITER-ROUTE-FREEZE.PUBLIC.json").write_text(json.dumps(freeze))
        (root / "writer/REQUEST.native.json").write_bytes(data + (b" " if corrupt else b""))

    def test_missing_backend_preserves_consumed_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.setup_receipts(root)
            with patch.object(route, "HERE", root), patch.object(route.urllib.request, "urlopen", side_effect=urllib.error.URLError("offline witness: backend absent")) as backend:
                with self.assertRaises(urllib.error.URLError):
                    route.invoke()
            self.assertEqual(backend.call_count, 1)
            failure = json.loads((root / "writer/TRANSPORT-FAILURE.PUBLIC.json").read_bytes())
            self.assertTrue(failure["invocation_consumed"])
            self.assertFalse(failure["retry_permitted"])
            self.assertFalse((root / "writer/RESPONSE.native.json").exists())

    def test_mutated_request_stops_before_backend(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.setup_receipts(root, corrupt=True)
            with patch.object(route, "HERE", root), patch.object(route.urllib.request, "urlopen") as backend:
                with self.assertRaises(AssertionError):
                    route.invoke()
            backend.assert_not_called()
            self.assertFalse((root / "writer/ATTEMPT-START.PUBLIC.json").exists())


if __name__ == "__main__":
    unittest.main()
