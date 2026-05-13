from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    service: str
    instance: str | None = None
    status: str = "ok"
    dependencies: dict[str, str] = Field(default_factory=dict)


class ServiceInstance(BaseModel):
    instance_name: str
    instance_url: str


class ServiceRegistrationRequest(BaseModel):
    service_name: str
    instance_name: str
    instance_url: str


class ServiceRegistrationResponse(BaseModel):
    service_name: str
    instance_name: str
    instance_url: str
    registered: bool


class ServiceHeartbeatRequest(BaseModel):
    service_name: str
    instance_name: str


class ServiceHeartbeatResponse(BaseModel):
    service_name: str
    instance_name: str
    accepted: bool


class ServiceDiscoveryResponse(BaseModel):
    service_name: str
    instances: list[ServiceInstance]
