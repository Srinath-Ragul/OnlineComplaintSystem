
import os
import sqlite3
import tempfile
import unittest

# Create a separate temporary database for testing
_fd, TEST_DB = tempfile.mkstemp(suffix=".db")
os.close(_fd)
os.environ["DATABASE_PATH"] = TEST_DB

from app import app


class TestComplaintApp(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)

    def test_submit_complaint(self):
        response = self.client.post(
            "/submit",
            data={
                "name": "Test User",
                "category": "Electricity",
                "description": "Test complaint"
            },
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)

        with sqlite3.connect(TEST_DB) as conn:
            result = conn.execute(
                "SELECT name, category, description FROM complaints "
                "WHERE name = ?",
                ("Test User",)
            ).fetchone()

        self.assertIsNotNone(result)
        self.assertEqual(result[0], "Test User")
        self.assertEqual(result[1], "Electricity")
        self.assertEqual(result[2], "Test complaint")

    def test_admin_requires_login(self):
        response = self.client.get("/admin")
        self.assertIn(response.status_code, (302, 401, 403))


if __name__ == "__main__":
    unittest.main(verbosity=2)
