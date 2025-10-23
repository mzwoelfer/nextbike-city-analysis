from abc import ABC, abstractmethod

# ---------- registry utils ----------
_DATABASE_BACKENDS = {}

def register_backend(name):
    def wrapper(cls):
        _DATABASE_BACKENDS[name] = cls
        return cls

    return wrapper

def get_backend(name):
    try:
        return _DATABASE_BACKENDS[name]
    except KeyError:
        raise ValueError(f"Unknown database backend: {name}")

# ---------- Base Database Class ----------
class AbstractDatabaseClient(ABC):
    @abstractmethod
    def insert_city_information(self, city):
        pass

    @abstractmethod
    def insert_bike_entries(self, bike_entries):
        pass

    @abstractmethod
    def insert_station_entries(self, station_entries):
        pass


class DatabaseClient:
    def __init__(self, config: AppConfig):
        backend_cls = get_backend(config.db_type)
        self.client: AbstractDatabaseClient = backend_cls(config)

    def __getattr__(self, name):
        return getattr(self.client, name)
