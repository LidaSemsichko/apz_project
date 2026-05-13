from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Request

from common.logging_utils import configure_logging
from common.schemas import (
    HealthResponse,
    ServiceDiscoveryResponse,
    ServiceHeartbeatRequest,
    ServiceHeartbeatResponse,
    ServiceInstance,
    ServiceRegistrationRequest,
    ServiceRegistrationResponse,
)


INSTANCE_NAME = os.getenv("INSTANCE_NAME", "config-server")
STALE_AFTER_SECONDS = int(os.getenv("STALE_AFTER_SECONDS", "30"))
LOGGER = configure_logging("config-server")


@dataclass(slots=True)
class RegisteredInstance:
    instance_name: str
    instance_url: str
    last_seen: datetime


@dataclass(slots=True)
class ConfigServerState:
    services: dict[str, dict[str, RegisteredInstance]] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    app_instance.state.config_server_state = ConfigServerState()
    LOGGER.info("event=service_started instance=%s", INSTANCE_NAME)
    try:
        yield
    finally:
        LOGGER.info("event=service_stopped instance=%s", INSTANCE_NAME)


app = FastAPI(title="Config Server", lifespan=lifespan)


def get_state(request: Request) -> ConfigServerState:
    return request.app.state.config_server_state


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@app.get("/health", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    return HealthResponse(service="config-server", instance=INSTANCE_NAME)


@app.post("/register", response_model=ServiceRegistrationResponse)
async def register_service(
    payload: ServiceRegistrationRequest,
    request: Request,
) -> ServiceRegistrationResponse:
    state = get_state(request)
    instance = RegisteredInstance(
        instance_name=payload.instance_name,
        instance_url=payload.instance_url.rstrip("/"),
        last_seen=now_utc(),
    )

    async with state.lock:
        service_instances = state.services.setdefault(payload.service_name, {})
        service_instances[payload.instance_name] = instance
        instance_count = len(service_instances)

    LOGGER.info(
        "event=service_registered service_name=%s instance_name=%s instance_url=%s instance_count=%s",
        payload.service_name,
        payload.instance_name,
        payload.instance_url,
        instance_count,
    )
    return ServiceRegistrationResponse(
        service_name=payload.service_name,
        instance_name=payload.instance_name,
        instance_url=payload.instance_url.rstrip("/"),
        registered=True,
    )


@app.post("/heartbeat", response_model=ServiceHeartbeatResponse)
async def heartbeat(
    payload: ServiceHeartbeatRequest,
    request: Request,
) -> ServiceHeartbeatResponse:
    state = get_state(request)

    async with state.lock:
        service_instances = state.services.get(payload.service_name, {})
        instance = service_instances.get(payload.instance_name)
        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"{payload.service_name}/{payload.instance_name} is not registered",
            )
        instance.last_seen = now_utc()

    return ServiceHeartbeatResponse(
        service_name=payload.service_name,
        instance_name=payload.instance_name,
        accepted=True,
    )


@app.get("/services/{service_name}", response_model=ServiceDiscoveryResponse)
async def get_service_instances(
    service_name: str,
    request: Request,
) -> ServiceDiscoveryResponse:
    state = get_state(request)
    stale_before = now_utc() - timedelta(seconds=STALE_AFTER_SECONDS)

    async with state.lock:
        service_instances = state.services.get(service_name, {})
        active_instances = [
            ServiceInstance(
                instance_name=instance.instance_name,
                instance_url=instance.instance_url,
            )
            for instance in service_instances.values()
            if instance.last_seen >= stale_before
        ]

    if not active_instances:
        raise HTTPException(
            status_code=404,
            detail=f"No active instances registered for {service_name}",
        )

    return ServiceDiscoveryResponse(
        service_name=service_name,
        instances=active_instances,
    )
