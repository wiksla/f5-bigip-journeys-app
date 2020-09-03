import json
import logging
from time import sleep
from time import time
from typing import List

import requests
from requests.exceptions import ConnectionError

from journeys.validators.exceptions import JourneysConnectionError
from journeys.validators.exceptions import JourneysError

logging.getLogger("requests").setLevel(logging.WARNING)


class QkviewIsNotOperational(JourneysError):
    """qkview timeout value was exceeded after uploading qkview to iHealth."""


class IHealthClient:
    """iHealth API client."""

    def __init__(self, client, logger):
        self.client = client
        self.log = logger

    def add_qkview(self, filepath):
        """Upload QKView to iHealth."""
        self.log.debug(f"Trying to upload qkview {filepath} to iHealth....")
        qkview = {}

        for i in range(2):
            try:
                r = self.client.session.post(
                    url=f"{self.client.BASE_URL}/qkviews",
                    files={"qkview": open(filepath, "rb")},
                    params={"visible_in_gui": True},
                    allow_redirects=False,
                ).json()
                qkview_id = r.get("id")
                qkview["id"] = qkview_id
                self.log.info(f"Qkview uploaded sucessfully! ID: {qkview_id}")

                if qkview_id:
                    self.log.info(
                        f"Waiting until qkview {qkview_id} is extracted and operational"
                    )
                    self._ensure_qkview_is_operational(qkview_id=qkview_id)
                    qkview["status"] = "operational"
                return qkview

            except QkviewIsNotOperational:
                self.log.debug(
                    f"Qkview {qkview_id} is not operational after 20 minutes."
                )
                qkview["status"] = "timeout"
                return qkview
            except ConnectionError as e:
                self.log.debug(
                    f"Connection Error while uploading qkview to iHealth {e}."
                )
                self.log.debug("Retrying...")
                sleep(2)

        return qkview

    def remove_qkviews(self, qkviews: List[int]):
        """Remove qkviews from iHealth."""
        for qkview in qkviews:
            for i in range(10):
                try:
                    self._ensure_qkview_is_operational(qkview_id=qkview)
                    # ensures that loop is not hogging iHealth API
                    sleep(1)
                    self.client.session.delete(
                        url=f"{self.client.BASE_URL}/qkviews/{qkview}"
                    )
                    break
                except ConnectionError:
                    self.log.debug(
                        f"Connection Error while removing Qkview ID {qkview}. Retrying {i}."
                    )
                    sleep(1)
                except QkviewIsNotOperational:
                    self.log.info(
                        f"Error while removing Qkview ID {qkview}. Qkview is not operational."
                    )
                    return
            self.log.debug(f"Qkview ID {qkview} removed from iHealth")

    def get_qkview_overview(self, qkview_id) -> dict:
        """Get QKView overview."""
        return self.client.session.get(
            url=f"{self.client.BASE_URL}/qkviews/{qkview_id}/overview"
        ).json()

    def _ensure_qkview_is_operational(self, qkview_id, timeout=1500):
        end_time = time() + timeout
        while time() <= end_time:
            url = f"{self.client.BASE_URL}/qkviews/{qkview_id}"
            r = self.client.session.get(
                url=url, headers=self.client.CONTENT_TYPE_HEADER
            )

            # workaround: iHealth return 404 if task is queued (bz: 708040)
            if r.status_code == 404:
                sleep(timeout / 30)
                continue
            if r.json().get("processing_status") == "COMPLETE":
                self.log.debug(f"Qkview ID {qkview_id} processing COMPLETE")
                return
            else:
                sleep(timeout / 30)
        msg = f"Qkview with id: {qkview_id} is not operational after {timeout} timeout"
        self.log.debug(msg)
        raise QkviewIsNotOperational(msg)


class IHealthConnector:
    """Authenticate user and create session to iHealth."""

    BASE_URL = "https://ihealth-api.f5.com/qkview-analyzer/api"
    AUTH_URL = "https://api.f5.com/auth/pub/sso/login/ihealth-api"
    CONTENT_TYPE_HEADER = {
        "content-type": "application/json",
    }

    def __init__(self, credentials):
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({"User-Agent": "JourneysQkviewComparer"})
        self._authenticate(credentials)
        self.session.headers.update(
            {"Accept": "application/vnd.f5.ihealth.api.v1.0+json"}
        )

    def _authenticate(self, credentials):
        http_status_code = self.session.post(
            url=self.AUTH_URL,
            data=json.dumps(credentials),
            headers=self.CONTENT_TYPE_HEADER,
        )
        if http_status_code.status_code != 200:
            raise JourneysConnectionError(
                "Authentication error: Wrong username or password."
            )


def get_ihealth_handler(ihealth_username, ihealth_password, log=None) -> IHealthClient:
    """Get IHealthClient with IHealthConnector using specified F5 Support login and password."""
    return IHealthClient(
        IHealthConnector(
            credentials={"user_id": ihealth_username, "user_secret": ihealth_password}
        ),
        log,
    )
