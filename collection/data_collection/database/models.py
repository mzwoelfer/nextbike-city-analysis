"""SQLAlchemy ORM Models für Nextbike Datenbank"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class CityModel(Base):
    __tablename__ = 'cities'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(Integer, nullable=False, unique=True)
    city_name = Column(Text, nullable=False)
    timezone = Column(Text, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    set_point_bikes = Column(Integer, nullable=False)
    available_bikes = Column(Integer, nullable=False)
    last_updated = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<City(city_id={self.city_id}, name='{self.city_name}')>"


class BikeModel(Base):
    __tablename__ = 'bikes'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    bike_number = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    active = Column(Boolean)
    state = Column(Text)
    bike_type = Column(Text)
    station_number = Column(Integer)
    station_uid = Column(Integer)
    last_updated = Column(DateTime, nullable=False)
    city_id = Column(Integer, nullable=False)
    city_name = Column(Text, nullable=False)

    def __repr__(self):
        return f"<Bike(number='{self.bike_number}', city_id={self.city_id})>"


class StationModel(Base):
    __tablename__ = 'stations'
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    name = Column(Text, nullable=False)
    spot = Column(Boolean, nullable=False)
    station_number = Column(Integer)
    maintenance = Column(Boolean)
    terminal_type = Column(Text)
    last_updated = Column(DateTime, nullable=False)
    city_id = Column(Integer, nullable=False)
    city_name = Column(Text, nullable=False)

    def __repr__(self):
        return f"<Station(uid={self.uid}, name='{self.name}', city_id={self.city_id})>"

