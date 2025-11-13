from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from database.base import AbstractDatabaseClient, register_backend
from database.models import Base, CityModel, BikeModel, StationModel


@register_backend("postgres")
class PostgresClient(AbstractDatabaseClient):
    """Handle postgres entries using SQLAlchemy ORM"""

    def __init__(self, config):
        self.config = config

        # Create SQLAlchemy engine
        self.connection_string = (
            f"postgresql+psycopg://{self.config.db_user}:{self.config.db_password}"
            f"@{self.config.db_host}:{self.config.db_port}/{self.config.db_name}"
        )

        self.engine = create_engine(
            self.connection_string,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL debugging
        )

        # Create session factory
        self.Session = sessionmaker(bind=self.engine)


    def insert_city_information(self, city):
        """Insert or update city information using SQLAlchemy"""
        session = self.Session()
        try:
            # Use INSERT ... ON CONFLICT DO NOTHING pattern
            # Use dataclass fields directly via __dict__
            city_dict = {k: v for k, v in city.__dict__.items()}
            stmt = insert(CityModel).values(**city_dict)

            # ON CONFLICT DO NOTHING
            stmt = stmt.on_conflict_do_nothing(index_elements=['city_id'])

            session.execute(stmt)
            session.commit()
        except exc.SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def insert_bike_entries(self, bike_entries):
        """Insert bike entries in bulk using SQLAlchemy"""
        if not bike_entries:
            return

        session = self.Session()
        try:
            # Prepare data for bulk insert using dataclass __dict__
            bike_data = [bike.__dict__ for bike in bike_entries]

            # Bulk insert with SQLAlchemy
            session.bulk_insert_mappings(BikeModel, bike_data)
            session.commit()
        except exc.SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def insert_station_entries(self, station_entries):
        """Insert station entries in bulk using SQLAlchemy"""
        if not station_entries:
            return

        session = self.Session()
        try:
            # Prepare data for bulk insert using dataclass __dict__
            station_data = [station.__dict__ for station in station_entries]

            # Bulk insert with SQLAlchemy
            session.bulk_insert_mappings(StationModel, station_data)
            session.commit()
        except exc.SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def __del__(self):
        """Cleanup engine on deletion"""
        if hasattr(self, 'engine'):
            self.engine.dispose()
