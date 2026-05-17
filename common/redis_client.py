import redis
from redis.sentinel import Sentinel


DEFAULT_SENTINEL_PORT = 26379
DEFAULT_SOCKET_TIMEOUT_SECONDS = 1.0


class RedisClientManager:
    def __init__(
        self,
        *,
        redis_url: str,
        sentinel_hosts_raw: str = "",
        master_name: str = "mymaster",
        db: int = 0,
        socket_timeout: float = DEFAULT_SOCKET_TIMEOUT_SECONDS,
        socket_connect_timeout: float = DEFAULT_SOCKET_TIMEOUT_SECONDS,
        decode_responses: bool = True,
    ) -> None:
        self.redis_url = redis_url
        self.sentinel_hosts_raw = sentinel_hosts_raw
        self.master_name = master_name
        self.db = db
        self.socket_timeout = socket_timeout
        self.socket_connect_timeout = socket_connect_timeout
        self.decode_responses = decode_responses
        self._sentinel: Sentinel | None = None
        self._client = None

    @property
    def mode(self) -> str:
        return "sentinel" if self.sentinel_hosts_raw else "direct"

    def get_client(self):
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def get_health_dependencies(self) -> dict[str, str]:
        dependencies = {
            "redis": "unavailable",
            "redis_mode": self.mode,
        }

        try:
            self.get_client().ping()
            dependencies["redis"] = "ok"

            master_address = self.get_master_address()
            if master_address:
                dependencies["redis_master"] = master_address
        except Exception:
            pass

        return dependencies

    def get_master_address(self) -> str | None:
        if self.mode != "sentinel":
            return None

        host, port = self._get_sentinel().discover_master(self.master_name)
        return f"{host}:{port}"

    def _build_client(self):
        if self.mode == "sentinel":
            return self._get_sentinel().master_for(
                self.master_name,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                db=self.db,
                decode_responses=self.decode_responses,
            )

        return redis.from_url(
            self.redis_url,
            decode_responses=self.decode_responses,
        )

    def _get_sentinel(self) -> Sentinel:
        if self._sentinel is None:
            self._sentinel = Sentinel(
                self._parse_sentinel_hosts(self.sentinel_hosts_raw),
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
            )
        return self._sentinel

    @staticmethod
    def _parse_sentinel_hosts(raw: str) -> list[tuple[str, int]]:
        hosts: list[tuple[str, int]] = []

        for token in raw.split(","):
            token = token.strip()
            if not token:
                continue

            host, _, port = token.partition(":")
            hosts.append((host, int(port or DEFAULT_SENTINEL_PORT)))

        return hosts
