import unittest
from unittest.mock import MagicMock, patch

import requests
from keboola.component.exceptions import UserException

from client import HeliosNephriteClient


def _make_client():
    client = HeliosNephriteClient(
        server_url="https://test.example.com",
        user_name="user",
        password="pass",
        db_profile="default",
    )
    client._auth_user = "user"
    client._auth_token = "token"
    return client


def _mock_response(json_data=None, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    if status_code >= 400:
        http_err = requests.exceptions.HTTPError(response=resp)
        resp.raise_for_status.side_effect = http_err
    else:
        resp.raise_for_status.return_value = None
    return resp


class TestGetEntitiesPagination(unittest.TestCase):
    def test_single_page(self):
        client = _make_client()
        records = [{"id": i} for i in range(5)]
        with patch.object(client, "_make_request", return_value={"value": records}):
            batches = list(client.get_entities("companies", batch_size=1000))
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0], records)

    def test_multiple_pages(self):
        client = _make_client()
        page1 = [{"id": i} for i in range(3)]
        page2 = [{"id": i} for i in range(3, 5)]
        responses = [{"value": page1}, {"value": page2}]
        with patch.object(client, "_make_request", side_effect=responses):
            batches = list(client.get_entities("companies", batch_size=3))
        self.assertEqual(len(batches), 2)
        self.assertEqual(batches[0], page1)
        self.assertEqual(batches[1], page2)

    def test_empty_response_stops_iteration(self):
        client = _make_client()
        with patch.object(client, "_make_request", return_value={"value": []}):
            batches = list(client.get_entities("companies"))
        self.assertEqual(batches, [])

    def test_passes_timestamp_param(self):
        client = _make_client()
        with patch.object(client, "_make_request", return_value={"value": []}) as mock_req:
            list(client.get_entities("companies", timestamp=12345))
        call_params = mock_req.call_args[0][1]
        self.assertEqual(call_params["Timestamp"], 12345)

    def test_no_timestamp_param_when_none(self):
        client = _make_client()
        with patch.object(client, "_make_request", return_value={"value": []}) as mock_req:
            list(client.get_entities("companies", timestamp=None))
        call_params = mock_req.call_args[0][1]
        self.assertNotIn("Timestamp", call_params)


class TestGetEntitiesErrorHandling(unittest.TestCase):
    def _make_http_error(self, status_code):
        resp = MagicMock()
        resp.status_code = status_code
        resp.text = "error"
        return requests.exceptions.HTTPError(response=resp)

    def test_401_raises_user_exception(self):
        client = _make_client()
        with patch.object(client, "_make_request", side_effect=self._make_http_error(401)):
            with self.assertRaises(UserException) as ctx:
                list(client.get_entities("companies"))
        self.assertIn("Authentication", str(ctx.exception))

    def test_404_raises_user_exception(self):
        client = _make_client()
        with patch.object(client, "_make_request", side_effect=self._make_http_error(404)):
            with self.assertRaises(UserException) as ctx:
                list(client.get_entities("unknown_entity"))
        self.assertIn("not found", str(ctx.exception))
        self.assertNotIn("sync action", str(ctx.exception))

    def test_500_raises_user_exception(self):
        client = _make_client()
        with patch.object(client, "_make_request", side_effect=self._make_http_error(500)):
            with self.assertRaises(UserException):
                list(client.get_entities("companies"))


if __name__ == "__main__":
    unittest.main()
