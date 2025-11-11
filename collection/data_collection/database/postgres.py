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

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

    def insert_city_information(self, city):
        """Insert or update city information using SQLAlchemy"""
        session = self.Session()
        try:
            # Use INSERT ... ON CONFLICT DO NOTHING pattern
            stmt = insert(CityModel).values(
                city_id=city.city_id,
                city_name=city.city_name,
                timezone=city.timezone,
                latitude=city.latitude,
                longitude=city.longitude,
                set_point_bikes=city.set_point_bikes,
                available_bikes=city.available_bikes,
                last_updated=city.last_updated
            )

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
            # Prepare data for bulk insert
            bike_data = [
                {
                    'bike_number': bike.bike_number,
                    'latitude': bike.latitude,
                    'longitude': bike.longitude,
                    'active': bike.active,
                    'state': bike.state,
                    'bike_type': bike.bike_type,
                    'station_number': bike.station_number,
                    'station_uid': bike.station_uid,
                    'last_updated': bike.last_updated,
                    'city_id': bike.city_id,
                    'city_name': bike.city_name
                }
                for bike in bike_entries
            ]

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
            # Prepare data for bulk insert
            station_data = [
                {
                    'uid': station.uid,
                    'latitude': station.latitude,
                    'longitude': station.longitude,
                    'name': station.name,
                    'spot': station.spot,
                    'station_number': station.station_number,
                    'maintenance': station.maintenance,
                    'terminal_type': station.terminal_type,
                    'last_updated': station.last_updated,
                    'city_id': station.city_id,
                    'city_name': station.city_name
                }
                for station in station_entries
            ]

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
