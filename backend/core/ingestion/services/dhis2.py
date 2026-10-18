import time

import requests
from django.conf import settings


class DHIS2RequestError(Exception):
    def __init__(
        self, message, request_info=None, response_body=None, status_code=None
    ):
        super().__init__(message)
        self.request_info = request_info or {}
        self.response_body = response_body
        self.status_code = status_code


class DHIS2Service:
    def __init__(self):
        self.base_url = settings.DHIS2_BASE_URL

        self.session = requests.Session()
        self.session.auth = (
            settings.DHIS2_USERNAME,
            settings.DHIS2_PASSWORD,
        )
        self.session.headers.update(
            {
                "Accept": "application/json",
            }
        )

    def test_connection(self):
        response = self.session.get(
            f"{self.base_url}/api/me",
            timeout=20,
            allow_redirects=False,
        )

        return {
            "status_code": response.status_code,
            "authenticated": response.status_code == 200,
            "redirect_location": response.headers.get("Location"),
        }

    def fetch_analytics(self, dx_ids, periods, org_unit_ids):
        """
        Fetch aggregate observations from DHIS2.

        Returns:
            request_info, response_body, status_code, duration_ms

        DHIS2 requires separate 'dimension' parameters.
        """

        if not dx_ids or not periods or not org_unit_ids:
            raise ValueError(
                "At least one dx ID, period and organisation unit must be provided."
            )

        url = f"{self.base_url}/api/analytics.json"

        params = [
            ("dimension", f"dx:{';'.join(dx_ids)}"),
            ("dimension", f"pe:{';'.join(periods)}"),
            ("dimension", f"ou:{';'.join(org_unit_ids)}"),
            ("skipMeta", "false"),
        ]

        prepared = requests.Request(
            "GET",
            url,
            params=params,
        ).prepare()

        request_info = {
            "method": "GET",
            "url": prepared.url,
            "dx_ids": list(dx_ids),
            "periods": list(periods),
            "org_unit_ids": list(org_unit_ids),
        }

        last_error = None

        for attempt in range(1, settings.DHIS2_MAX_ATTEMPTS + 1):
            started = time.monotonic()

            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=(
                        settings.DHIS2_CONNECT_TIMEOUT,
                        settings.DHIS2_READ_TIMEOUT,
                    ),
                )

                duration_ms = int((time.monotonic() - started) * 1000)

                try:
                    payload = response.json()
                except ValueError:
                    payload = {"raw": response.text[:10000]}

                if response.status_code in (429, 500, 502, 503, 504):
                    last_error = DHIS2RequestError(
                        f"DHIS2 temporary HTTP error: {response.status_code}",
                        request_info=request_info,
                        response_body=payload,
                        status_code=response.status_code,
                    )

                    if attempt < settings.DHIS2_MAX_ATTEMPTS:
                        time.sleep(settings.DHIS2_RETRY_BACKOFF_SECONDS * attempt)
                        continue

                    raise last_error

                if not response.ok:
                    raise DHIS2RequestError(
                        f"DHIS2 rejected request: HTTP {response.status_code}",
                        request_info=request_info,
                        response_body=payload,
                        status_code=response.status_code,
                    )

                if not isinstance(payload, dict):
                    raise DHIS2RequestError(
                        "DHIS2 returned an unexpected JSON format",
                        request_info=request_info,
                        response_body=payload,
                        status_code=response.status_code,
                    )

                return (
                    request_info,
                    payload,
                    response.status_code,
                    duration_ms,
                )

            except (requests.Timeout, requests.ConnectionError) as exc:
                last_error = DHIS2RequestError(
                    f"DHIS2 connection failure: {exc}",
                    request_info=request_info,
                )

                if attempt < settings.DHIS2_MAX_ATTEMPTS:
                    time.sleep(settings.DHIS2_RETRY_BACKOFF_SECONDS * attempt)
                    continue

                raise last_error

        raise last_error
