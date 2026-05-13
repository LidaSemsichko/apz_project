import os
import threading
import time

import httpx

from common.errors import ServiceUnavailableError
from common.retry import retry
from common.schemas import ServiceInstance


CONFIG_SERVER_URL = os.getenv("CONFIG_SERVER_URL", "http://config-server:8000")


def register_service(
    service_name: str,
    instance_name: str,
    instance_url: str,
    *,
    config_server_url: str | None = None,
) -> None:
    base_url = config_server_url or CONFIG_SERVER_URL

    def operation() -> None:
        response = httpx.post(
            f"{base_url}/register",
            json={
                "service_name": service_name,
                "instance_name": instance_name,
                "instance_url": instance_url,
            },
            timeout=5,
        )
        response.raise_for_status()

    retry(operation, attempts=20, delay_seconds=2)


def heartbeat_service(
    service_name: str,
    instance_name: str,
    *,
    config_server_url: str | None = None,
) -> None:
    base_url = config_server_url or CONFIG_SERVER_URL
    response = httpx.post(
        f"{base_url}/heartbeat",
        json={
            "service_name": service_name,
            "instance_name": instance_name,
        },
        timeout=5,
    )
    response.raise_for_status()


def start_registration_heartbeat(
    service_name: str,
    instance_name: str,
    instance_url: str,
    *,
    config_server_url: str | None = None,
    interval_seconds: int = 10,
) -> None:
    base_url = config_server_url or CONFIG_SERVER_URL
    register_service(service_name, instance_name, instance_url, config_server_url=base_url)

    def heartbeat_loop() -> None:
        while True:
            try:
                heartbeat_service(service_name, instance_name, config_server_url=base_url)
            except Exception:
                try:
                    register_service(
                        service_name,
                        instance_name,
                        instance_url,
                        config_server_url=base_url,
                    )
                except Exception:
                    pass
            time.sleep(interval_seconds)

    thread = threading.Thread(target=heartbeat_loop, daemon=True)
    thread.start()


def resolve_service_instances(
    service_name: str,
    *,
    config_server_url: str | None = None,
) -> list[ServiceInstance]:
    base_url = config_server_url or CONFIG_SERVER_URL
    try:
        response = httpx.get(f"{base_url}/services/{service_name}", timeout=5)
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        if error.response.status_code == 404:
            raise ServiceUnavailableError(f"No instances registered for {service_name}")
        raise ServiceUnavailableError(f"Cannot resolve {service_name}: {error}") from error
    except httpx.RequestError as error:
        raise ServiceUnavailableError(f"Config server unavailable: {error}") from error

    payload = response.json()
    return [ServiceInstance(**item) for item in payload.get("instances", [])]


def check_service_registered(service_name: str) -> str:
    try:
        instances = resolve_service_instances(service_name)
        return "ok" if instances else "unavailable"
    except ServiceUnavailableError:
        return "unavailable"
