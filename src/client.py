"""
Helios Nephrite API client with session-based authentication and rate limiting.
"""

import logging
from collections.abc import Generator

import backoff
import requests
from keboola.component.exceptions import UserException
from pyrate_limiter import Duration, Limiter, Rate


class HeliosNephriteClient:
    GENERAL_API_PATH = "/api/v1/general"

    def __init__(
        self,
        server_url: str,
        user_name: str,
        password: str,
        db_profile: str,
        language_id: str = "en",
        requests_per_minute: int = 30,
    ):
        self.server_url = server_url.rstrip("/")
        self._user_name = user_name
        self._password = password
        self._db_profile = db_profile
        self._language_id = language_id
        self._session = requests.Session()
        self._auth_user: str | None = None
        self._auth_token: str | None = None

        rate = Rate(requests_per_minute, Duration.MINUTE)
        self._limiter = Limiter(rate)

        logging.debug(f"Client initialized with rate limit: {requests_per_minute} req/min")

    def login(self) -> None:
        logging.info(f"Authenticating to Helios Nephrite at {self.server_url}")

        try:
            response = self._session.post(
                f"{self.server_url}/api/Connect/LogIn",
                json={
                    "userName": self._user_name,
                    "password": self._password,
                    "languageId": self._language_id,
                    "dbProfile": self._db_profile,
                    "serverURL": self.server_url,
                },
                timeout=30,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise UserException(f"Failed to connect to Helios Nephrite: {e}")

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            raise UserException(
                f"Login failed: unexpected response from server (not JSON). Response: {response.text[:200]}"
            )

        if not data.get("success", True):  # Some APIs use success field
            error_msg = data.get("errorMessage") or data.get("message") or "Unknown error"
            raise UserException(f"Login failed: {error_msg}")

        self._auth_user = data.get("userName")
        self._auth_token = data.get("userId")

        if not self._auth_user or not self._auth_token:
            raise UserException("Login response missing userName or userId")

        logging.info("Successfully authenticated to Helios Nephrite")

    def logout(self) -> None:
        if self._auth_user and self._auth_token:
            try:
                self._session.post(
                    f"{self.server_url}/api/Connect/LogOut",
                    auth=(self._auth_user, self._auth_token),
                    timeout=10,
                )
                logging.info("Logged out from Helios Nephrite")
            except requests.exceptions.RequestException as e:
                logging.warning(f"Logout failed: {e}")
        self._session.close()

    @backoff.on_exception(
        backoff.expo,
        (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError,
        ),
        max_tries=5,
        giveup=lambda e: isinstance(e, requests.exceptions.HTTPError)
        and e.response is not None
        and e.response.status_code < 500,
    )
    def _make_request(self, url: str, params: dict) -> dict | list:
        self._limiter.try_acquire("api_request")

        response = self._session.get(
            url,
            params=params,
            auth=(self._auth_user, self._auth_token),
            timeout=60,
        )

        response.raise_for_status()
        return response.json()

    def get_entities(
        self,
        entity: str,
        timestamp: int | None = None,
        batch_size: int = 1000,
    ) -> Generator[list[dict]]:
        skip = 0
        total_fetched = 0
        url = f"{self.server_url}{self.GENERAL_API_PATH}/{entity}"

        logging.info(f"Starting extraction for entity: {entity}")
        if timestamp is not None:
            logging.info(f"Incremental load from timestamp: {timestamp}")

        while True:
            params = {"Top": batch_size, "Skip": skip}
            if timestamp is not None:
                params["Timestamp"] = timestamp

            logging.debug(f"Request URL: {url}, params: {params}")

            try:
                data = self._make_request(url, params)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    raise UserException("Authentication expired or invalid. Please check credentials.")
                elif e.response.status_code == 404:
                    raise UserException(f"Entity '{entity}' not found. Use sync action to list available entities.")
                else:
                    raise UserException(
                        f"API error for entity '{entity}': {e.response.status_code} - {e.response.text}"
                    )

            records = data.get("value", [])
            logging.debug(f"Response status: OK, Batch size: {len(records)}")

            if not records:
                if total_fetched == 0:
                    logging.warning(f"Entity {entity} returned empty response")
                break

            yield records

            total_fetched += len(records)
            logging.info(f"Extracted {total_fetched} records from {entity}")

            if len(records) < batch_size:
                break

            skip += batch_size
