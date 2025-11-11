"""
Integration Tests für SQLAlchemy Database Implementation

Diese Tests verifizieren die SQLAlchemy-basierte Datenbankimplementierung.
"""
import unittest
from unittest.mock import MagicMock, patch
import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query_nextbike import City, Bike, Station


class TestSQLAlchemyIntegration(unittest.TestCase):
    """Test SQLAlchemy database integration"""

    def setUp(self):
        """Setup test data"""
        self.timestamp = datetime.datetime.now()

        self.test_city = City(
            city_id=123,
            city_name="TestCity",
            timezone="Europe/Berlin",
            latitude=52.52,
            longitude=13.40,
            set_point_bikes=100,
            available_bikes=80,
            last_updated=self.timestamp
        )

        self.test_bike = Bike(
            bike_number="TEST001",
            latitude=52.52,
            longitude=13.40,
            active=True,
            state="ok",
            bike_type="150",
            station_number=1,
            station_uid=1001,
            last_updated=self.timestamp,
            city_id=123,
            city_name="TestCity"
        )

        self.test_station = Station(
            uid=1001,
            latitude=52.52,
            longitude=13.40,
            name="Test Station",
            spot=True,
            station_number=1,
            maintenance=False,
            terminal_type="normal",
            last_updated=self.timestamp,
            city_id=123,
            city_name="TestCity"
        )

    @patch('database.postgres.create_engine')
    @patch('database.postgres.sessionmaker')
    def test_postgres_client_initialization(self, mock_sessionmaker, mock_create_engine):
        """Test that PostgresClient initializes with SQLAlchemy"""
        from database.postgres import PostgresClient

        # Mock config
        mock_config = MagicMock()
        mock_config.db_user = 'test_user'
        mock_config.db_password = 'test_pass'
        mock_config.db_host = 'localhost'
        mock_config.db_port = 5432
        mock_config.db_name = 'test_db'

        # Create client
        client = PostgresClient(mock_config)

        # Verify engine was created with correct connection string
        expected_conn_str = "postgresql+psycopg://test_user:test_pass@localhost:5432/test_db"
        mock_create_engine.assert_called_once()
        call_args = mock_create_engine.call_args
        self.assertEqual(call_args[0][0], expected_conn_str)

        # Verify pool_pre_ping is enabled
        self.assertTrue(call_args[1]['pool_pre_ping'])

    @patch('database.postgres.sessionmaker')
    @patch('database.postgres.create_engine')
    def test_insert_city_information(self, mock_create_engine, mock_sessionmaker):
        """Test city insertion with SQLAlchemy"""
        from database.postgres import PostgresClient

        # Setup mocks
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_config = MagicMock()
        mock_config.db_user = 'test'
        mock_config.db_password = 'test'
        mock_config.db_host = 'localhost'
        mock_config.db_port = 5432
        mock_config.db_name = 'test'

        client = PostgresClient(mock_config)

        # Insert city
        client.insert_city_information(self.test_city)

        # Verify session was used
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('database.postgres.sessionmaker')
    @patch('database.postgres.create_engine')
    def test_insert_bike_entries_bulk(self, mock_create_engine, mock_sessionmaker):
        """Test bulk bike insertion"""
        from database.postgres import PostgresClient

        # Setup mocks
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_config = MagicMock()
        mock_config.db_user = 'test'
        mock_config.db_password = 'test'
        mock_config.db_host = 'localhost'
        mock_config.db_port = 5432
        mock_config.db_name = 'test'

        client = PostgresClient(mock_config)

        # Insert bikes
        bike_entries = [self.test_bike]
        client.insert_bike_entries(bike_entries)

        # Verify bulk_insert_mappings was called
        mock_session.bulk_insert_mappings.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('database.postgres.sessionmaker')
    @patch('database.postgres.create_engine')
    def test_insert_station_entries_bulk(self, mock_create_engine, mock_sessionmaker):
        """Test bulk station insertion"""
        from database.postgres import PostgresClient

        # Setup mocks
        mock_session = MagicMock()
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_config = MagicMock()
        mock_config.db_user = 'test'
        mock_config.db_password = 'test'
        mock_config.db_host = 'localhost'
        mock_config.db_port = 5432
        mock_config.db_name = 'test'

        client = PostgresClient(mock_config)

        # Insert stations
        station_entries = [self.test_station]
        client.insert_station_entries(station_entries)

        # Verify bulk_insert_mappings was called
        mock_session.bulk_insert_mappings.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('database.postgres.sessionmaker')
    @patch('database.postgres.create_engine')
    def test_error_handling_rollback(self, mock_create_engine, mock_sessionmaker):
        """Test that errors trigger rollback"""
        from database.postgres import PostgresClient
        from sqlalchemy import exc

        # Setup mocks
        mock_session = MagicMock()
        mock_session.bulk_insert_mappings.side_effect = exc.SQLAlchemyError("Test error")
        mock_sessionmaker.return_value = MagicMock(return_value=mock_session)
        mock_config = MagicMock()
        mock_config.db_user = 'test'
        mock_config.db_password = 'test'
        mock_config.db_host = 'localhost'
        mock_config.db_port = 5432
        mock_config.db_name = 'test'

        client = PostgresClient(mock_config)

        # Insert should raise exception
        with self.assertRaises(exc.SQLAlchemyError):
            client.insert_bike_entries([self.test_bike])

        # Verify rollback was called
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    def test_dataclass_compatibility(self):
        """Test that dataclasses are compatible with SQLAlchemy mapping"""
        # Verify as_tuple still works (backward compatibility)
        city_tuple = self.test_city.as_tuple()
        self.assertEqual(len(city_tuple), 8)

        bike_tuple = self.test_bike.as_tuple()
        self.assertEqual(len(bike_tuple), 11)

        station_tuple = self.test_station.as_tuple()
        self.assertEqual(len(station_tuple), 11)


class TestSQLAlchemyModels(unittest.TestCase):
    """Test SQLAlchemy ORM models"""

    def test_city_model_attributes(self):
        """Test CityModel has all required attributes"""
        from database.models import CityModel

        # Check tablename
        self.assertEqual(CityModel.__tablename__, 'cities')

        # Check columns exist
        columns = [c.name for c in CityModel.__table__.columns]
        expected_columns = [
            'id', 'city_id', 'city_name', 'timezone',
            'latitude', 'longitude', 'set_point_bikes',
            'available_bikes', 'last_updated'
        ]
        for col in expected_columns:
            self.assertIn(col, columns)

    def test_bike_model_attributes(self):
        """Test BikeModel has all required attributes"""
        from database.models import BikeModel

        self.assertEqual(BikeModel.__tablename__, 'bikes')

        columns = [c.name for c in BikeModel.__table__.columns]
        expected_columns = [
            'id', 'bike_number', 'latitude', 'longitude',
            'active', 'state', 'bike_type', 'station_number',
            'station_uid', 'last_updated', 'city_id', 'city_name'
        ]
        for col in expected_columns:
            self.assertIn(col, columns)

    def test_station_model_attributes(self):
        """Test StationModel has all required attributes"""
        from database.models import StationModel

        self.assertEqual(StationModel.__tablename__, 'stations')

        columns = [c.name for c in StationModel.__table__.columns]
        expected_columns = [
            'id', 'uid', 'latitude', 'longitude', 'name',
            'spot', 'station_number', 'maintenance',
            'terminal_type', 'last_updated', 'city_id', 'city_name'
        ]
        for col in expected_columns:
            self.assertIn(col, columns)


if __name__ == '__main__':
    unittest.main()

