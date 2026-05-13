import httpx

from common.errors import UnauthorizedError, ServiceUnavailableError
from common.service_discovery import resolve_service_instances


def extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise UnauthorizedError("Authorization header is missing")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid authorization header format")

    return parts[1]


def verify_authorization_header(authorization: str | None) -> dict:
    extract_bearer_token(authorization)
    instances = resolve_service_instances("auth-service")
    last_error: Exception | None = None

    for instance in instances:
        try:
            response = httpx.get(
                f"{instance.instance_url}/verify",
                headers={"Authorization": authorization},
                timeout=5,
            )
            if response.status_code == 401:
                raise UnauthorizedError(response.json().get("detail", "Invalid token"))
            response.raise_for_status()
            return response.json()
        except UnauthorizedError:
            raise
        except Exception as error:
            last_error = error

    raise ServiceUnavailableError(f"Auth service unavailable: {last_error}")
