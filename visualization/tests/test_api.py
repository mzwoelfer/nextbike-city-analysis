import unittest
from unittest.mock import MagicMock, patch

# Stub StaticFiles before api.py is imported — /app/data doesn't exist locally
with patch("starlette.staticfiles.StaticFiles", MagicMock()):
    from api import app

from fastapi.testclient import TestClient

client = TestClient(app)


def _mock_conn(rows):
    cursor = MagicMock()
    cursor.fetchall.return_value = rows
    cursor.__enter__ = lambda s: s
    cursor.__exit__ = MagicMock(return_value=False)

    conn = MagicMock()
    conn.cursor.return_value = cursor
    conn.__enter__ = lambda s: s
    conn.__exit__ = MagicMock(return_value=False)
    return conn


class TestAvailableEndpoint(unittest.TestCase):

    @patch("api.get_connection")
    def test_response_includes_city_name(self, mock_get_conn):
        mock_get_conn.return_value = _mock_conn([
            (467, "Gießen", ["2026-06-08", "2026-06-07"]),
        ])
        data = client.get("/api/available").json()
        self.assertIn("city_name", data[0])

    @patch("api.get_connection")
    def test_city_name_is_never_null(self, mock_get_conn):
        mock_get_conn.return_value = _mock_conn([
            (467, "Gießen", ["2026-06-08"]),
            (999, "999",    ["2026-06-08"]),
        ])
        data = client.get("/api/available").json()
        for item in data:
            self.assertIsNotNone(item.get("city_name"),
                                 f"city_name is null for city_id={item.get('city_id')}")
            self.assertNotEqual(item["city_name"], "")

    @patch("api.get_connection")
    def test_city_id_and_dates_still_present(self, mock_get_conn):
        mock_get_conn.return_value = _mock_conn([
            (467, "Gießen", ["2026-06-08"]),
        ])
        item = client.get("/api/available").json()[0]
        self.assertIn("city_id", item)
        self.assertIn("dates", item)
        self.assertIsInstance(item["dates"], list)


if __name__ == "__main__":
    unittest.main()