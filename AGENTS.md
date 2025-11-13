# AGENTS.md - Nextbike City Analysis

## Projektübersicht

Nextbike City Analysis ist ein vollständiges System zur Sammlung, Verarbeitung und Visualisierung von Nextbike-Fahrraddaten. Das Projekt ermöglicht es, Fahrradtrips in verschiedenen Städten zu analysieren und interaktiv auf einer Karte darzustellen.

## Architektur

Das Projekt folgt einer dreistufigen Pipeline-Architektur:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Collection    │ ───> │   Processing    │ ───> │ Visualization   │
│   (Python)      │      │   (Python)      │      │   (JavaScript)  │
└─────────────────┘      └─────────────────┘      └─────────────────┘
        │                        │                         │
        ▼                        ▼                         ▼
   PostgreSQL DB           Datenanalyse            Web Dashboard
   (Docker)                & Trip-Extraktion       (GitHub Pages)
```

---

## Komponenten

### 1. Collection (Datensammlung)

**Verzeichnis**: `collection/`

#### Funktion
Sammelt alle 60 Sekunden Daten von der Nextbike API und speichert diese in einer PostgreSQL-Datenbank.

#### Technologie-Stack
- **Python 3.11** (Alpine Docker Image)
- **PostgreSQL 15** (Datenbank)
- **Docker & Docker Compose** (Containerisierung)
- **SQLAlchemy 2.0.36** (ORM & Datenbankabstraktion)
- **Hauptabhängigkeiten**:
  - `requests==2.32.3` (API-Anfragen)
  - `psycopg[binary]==3.2.3` (PostgreSQL-Treiber für SQLAlchemy)
  - `SQLAlchemy==2.0.36` (ORM, Connection Pooling)
  - `python-dotenv==1.0.1` (Umgebungsvariablen)

#### Kernkomponenten

**`query_nextbike.py`** - Hauptskript für die Datensammlung
- **Dataclasses**:
  - `City`: Speichert Stadtinformationen (ID, Name, Koordinaten, verfügbare Räder)
  - `Bike`: Speichert Fahrradinformationen (Nummer, Position, Status, Station)
  - `Station`: Speichert Stationsinformationen
  
**`database/`** - Datenbankabstraktion (SQLAlchemy ORM)
- `base.py`: Basis-Datenbankklasse mit Registry-Pattern
- `models.py`: SQLAlchemy ORM-Modelle (CityModel, BikeModel, StationModel)
- `postgres.py`: PostgreSQL-Implementierung mit SQLAlchemy
  - Engine mit Connection Pooling
  - Session-Management
  - Bulk-Insert-Operationen
  - Automatische Tabellenerstellung

#### Datenmodell
```sql
-- Tabellen:
public.cities     -- Stadtinformationen
public.bikes      -- Fahrrad-Positionsdaten (Zeitreihen)
public.stations   -- Stationsinformationen
```

#### Docker-Setup
```yaml
services:
  postgres:          # PostgreSQL Datenbank
  data_collector:    # Python-Skript läuft alle 60 Sekunden
```

**CONTAINERFILE (Multi-Stage Build)**:
- Stage 1: Dependencies installieren
- Stage 2: Produktions-Image mit Anwendung

#### Konfiguration
`.env` Datei benötigt:
```ini
DB_TYPE=postgres
DB_HOST=postgres
DB_PORT=5432
DB_NAME=nextbike_data
DB_USER=bike_admin
DB_PASSWORD=mybike
CITY_IDS=467  # Komma-separiert für mehrere Städte
```

---

### 2. Processing (Datenverarbeitung)

**Verzeichnis**: `processing/`

#### Funktion
Extrahiert Fahrrad-Trips aus den gesammelten Rohdaten, berechnet Routen und bereitet Daten für die Visualisierung auf.

#### Technologie-Stack
- **Python 3.12** (Slim Docker Image)
- **Hauptabhängigkeiten**:
  - `psycopg[binary]==3.2.3` (Datenbankzugriff)
  - `pandas==2.2.3` (Datenanalyse)
  - `osmnx==1.9.3` (OpenStreetMap Netzwerk)
  - `networkx==3.4.2` (Graphenalgorithmen)
  - `geopy==2.4.1` (Geodaten-Berechnung)
  - `scikit-learn==1.5.2` (Machine Learning)
  - `matplotlib==3.9.2` (Visualisierung)

#### Kernmodule

**`main.py`** - Einstiegspunkt
- Kommandozeilen-Argumente: `--city-id`, `--export-folder`, `--date`
- Orchestriert Stations- und Trip-Verarbeitung

**`trips.py`** - Trip-Extraktion & Routing
- `fetch_trip_data()`: SQL-Abfrage für Fahrtenbewegungen
  - Verwendet WINDOW-Funktionen (LEAD) für zeitliche Sequenzen
  - Filtert nur Bewegungen (Position hat sich geändert)
- `calculate_shortest_path()`: Berechnet kürzeste Route über OSM-Straßennetz
  - Verwendet OSMnx für Routing
  - NetworkX für Shortest-Path-Algorithmus
- `add_timestamps_to_segments()`: Interpoliert Zeitstempel für Routensegmente
- `remove_gps_errors()`: Filtert GPS-Fehler (< 60m Bewegung, < 1 Minute)

**`stations.py`** - Stations-Verarbeitung
- Extrahiert und aggregiert Stationsdaten

**`database.py`** - Datenbankverbindung
- PostgreSQL-Verbindungsmanagement mit psycopg

**`cities.py`** - Städte-Koordinaten
- `get_city_coordinates_from_database()`: Holt Stadtkoordinaten

**`utils.py`** - Hilfsfunktionen
- `ensure_directory_exists()`: Verzeichniserstellung
- `save_json()`, `save_csv()`, `save_gzipped_csv()`: Datenexport

**`config.py`** - Konfiguration
- Lädt Umgebungsvariablen für DB-Zugriff

#### Algorithmus: Trip-Extraktion
```python
1. Hole alle Bike-Positionen für einen Tag, sortiert nach bike_number und Zeit
2. Nutze SQL WINDOW-Funktion LEAD() um Start- und Endpositionen zu paaren
3. Filtere nur Bewegungen (Position hat sich geändert)
4. Berechne Duration (end_time - start_time)
5. Für jede Bewegung:
   - Lade OSM-Straßennetzwerk für die Region
   - Berechne kürzesten Pfad zwischen Start/Ziel
   - Interpoliere Zeitstempel für Wegpunkte
6. Entferne GPS-Fehler (zu kurze Bewegungen)
7. Exportiere als JSON/CSV
```

#### Ausgabeformat
```
data/
├── trips_<city_id>_<date>.json.gz    # Komprimierte Trip-Daten
├── trips_<city_id>_<date>.csv        # Trip-CSV
└── stations_<city_id>_<date>.json    # Stationsdaten
```

---

### 3. Visualization (Webvisualisierung)

**Verzeichnis**: `visualization/`

#### Funktion
Interaktive Webanwendung zur Darstellung von Fahrrad-Trips auf einer Karte mit Zeitrafferfunktion.

#### Technologie-Stack
- **Vanilla JavaScript** (ES6 Modules)
- **Leaflet.js 1.9.4** (Kartendarstellung)
- **HTML5 & CSS3**
- **Python http.server** (Lokaler Entwicklungsserver)

#### Architektur

**Modulare JavaScript-Struktur:**

```
scripts/
├── main.js        # Einstiegspunkt, Orchestrierung
├── state.js       # Zentraler State-Management
├── map.js         # Leaflet-Karten-Initialisierung
├── data.js        # Daten-Loading (manifest.json)
├── playback.js    # Zeitraffer-Steuerung
├── trips.js       # Trip-Rendering auf Karte
├── stations.js    # Stations-Marker
├── table.js       # Trip-Tabelle
├── utils.js       # Hilfsfunktionen
└── navigation.js  # UI-Navigation
```

#### Kernfunktionen

**State Management (`state.js`)**
```javascript
export default {
  map: null,           // Leaflet Map-Objekt
  tripsData: [],       // Geladene Trip-Daten
  stationsData: [],    // Stationsdaten
  currentTimeMinutes: 0, // Aktuelle Zeit im Zeitraffer
  isPlaying: false,    // Playback-Status
  city_id: null,       // Aktuelle Stadt-ID
  date: null,          // Aktuelles Datum
  cities: {}           // Verfügbare Städte
}
```

**Daten-Loading (`data.js`)**
- `loadAvailableFiles()`: Lädt `manifest.json` für verfügbare Datendateien
- `loadTripsData(cityId, date)`: Lädt Trip-Daten für Stadt und Datum
- `loadStationData(cityId, date)`: Lädt Stationsdaten

**Playback (`playback.js`)**
- Zeitraffer-Simulation: 1440 Minuten (24 Stunden)
- Play/Pause-Steuerung
- Slider-Updates (alle 100ms)

**Trip-Rendering (`trips.js`)**
- `drawTrips()`: Zeichnet alle aktiven Trips zur aktuellen Zeit
- `highlightTripOnMap()`: Hebt einzelnen Trip hervor
- Verwendet Leaflet Polylines mit Farbcodierung

**UI-Komponenten:**
- Karte (Leaflet)
- Zeit-Slider (0-1440 Minuten)
- Play/Pause-Button
- Stadt-Auswahl-Dropdown
- Datum-Navigation (vorheriger/nächster Tag)
- Statistik-Anzeige (Trips gesamt, aktive Räder)
- Trip-Tabelle

#### Visualisierung-Features
- ✅ Echtzeit-Zeitraffer von Fahrten
- ✅ Interaktive Karte mit Zoom/Pan
- ✅ Stations-Marker
- ✅ Trip-Routen mit Zeitstempeln
- ✅ Statistiken (Trips/Tag, aktive Räder)
- ✅ Mehrere Städte unterstützt
- ✅ Datum-Navigation

---

## Testing

### Collection Tests

**Verzeichnis**: `collection/data_collection/tests/`

#### Test-Dateien
- `test_bike_class.py`: Unit-Tests für Bike-Dataclass
  - Test Bike-Erstellung aus API-Daten
  - Test mehrere Bikes pro Station
  - Test Attribut-Validierung
  
- `test_city_class.py`: Unit-Tests für City-Dataclass
  
- `test_station_class.py`: Unit-Tests für Station-Dataclass
  
- `test_cli.py`: Tests für Command-Line Interface

#### Test-Framework
- **unittest** (Python Standard Library)

#### Test ausführen
```bash
cd collection/data_collection
python -m unittest discover tests/
```

### Processing Tests
**Status**: Keine Tests im Repository vorhanden
**Empfehlung**: Integration-Tests für Trip-Extraktion hinzufügen

### Visualization Tests
**Status**: Keine automatisierten Tests
**Empfehlung**: JavaScript-Tests mit Jest/Mocha hinzufügen

---

## Deployment

### Lokales Entwicklungs-Setup

#### 1. Vollständiger Stack (Validation)
```bash
# 1. Repository klonen
git clone https://github.com/zwoefler/nextbike-city-analysis.git
cd nextbike-city-analysis

# 2. Collection starten
cd collection
cp .env.example .env
docker build --file CONTAINERFILE -t nextbike_collector:multiple_cities .
docker compose --file docker-compose.yaml up -d
cd ..

# 3. Processing (nach einigen Minuten)
cd processing
cp .env.example .env
docker build --file CONTAINERFILE -t nextbike-processing:latest .
docker run --rm --env-file .env \
  -e DB_HOST=nextbike_postgres \
  --network collection_nextbike_network \
  -v "$(pwd)/../data/:/app/data" \
  nextbike-processing:latest \
  --city-id 467 --export-folder /app/data --date $(date +%Y-%m-%d)
cd ..

# 4. Visualisierung starten
cd visualization
python3 -m http.server 8000
# Öffne http://localhost:8000
```

### Produktions-Deployment

#### Collection (Dauerhafter Betrieb)
**Empfohlene Umgebung**: Linux VM mit IPv4

1. **Server-Setup**:
   ```bash
   # IPv4 erforderlich (Nextbike API)
   # Docker & Docker Compose installieren
   ```

2. **Installation**:
   ```bash
   cd collection
   cp .env.example .env
   # .env anpassen (CITY_IDS, DB-Credentials)
   docker build -f CONTAINERFILE -t nextbike_collector:multiple_cities .
   docker compose up -d
   ```

3. **Monitoring**:
   ```bash
   docker compose logs -f data_collector
   docker compose ps
   ```

4. **Updates**:
   ```bash
   docker build -f CONTAINERFILE -t nextbike_collector:multiple_cities .
   docker compose up -d --no-deps --build data_collector
   ```

#### Processing (Tägliche Ausführung)

**Option 1: Manuell**
```bash
python3 -m nextbike_processing.main \
  --city-id 467 \
  --export-folder ../data/ \
  --date $(date +%Y-%m-%d)
```

**Option 2: Cronjob**
```bash
# Täglich um 1:00 Uhr ausführen
0 1 * * * cd /path/to/processing && ./scripts/daily_trip_extractor.sh
```

**Option 3: Docker**
```bash
docker run --rm --env-file .env \
  -e DB_HOST=nextbike_postgres \
  --network collection_nextbike_network \
  -v "$(pwd)/../data/:/app/data" \
  nextbike-processing:latest \
  --city-id 467 --export-folder /app/data --date $(date +%Y-%m-%d)
```

#### Visualization (GitHub Pages)

**Deployment-Prozess**:

1. **Daten aktualisieren**:
   ```bash
   # Trip-Daten in data/ ablegen
   # Generiere manifest.json
   cd visualization
   ./create_manifest.sh
   ```

2. **GitHub Pages Publishing**:
   ```bash
   # Automatisches Skript
   ./update-gh-pages.sh
   ```

**Was `update-gh-pages.sh` macht**:
```bash
1. Checkout master branch
2. Pull latest changes
3. Checkout gh-pages branch
4. Reset gh-pages to master
5. Restore data/ directory aus gh-pages
6. .gitignore anpassen: data/ erlauben
7. Commit & Push data/ zu gh-pages
8. Zurück zu master
```

**Wichtig**:
- Nur `data/` wird zu `gh-pages` gepusht
- `master` branch bleibt sauber (ohne große Datendateien)
- GitHub Pages serviert automatisch von `gh-pages` branch

#### Remote Database Access (SSH Tunneling)

Wenn PostgreSQL auf einem Server läuft:

**SSH Config** (`~/.ssh/config`):
```
Host nextbike_postgres
  HostName <SERVER_IP>
  User <USERNAME>
  Port 22
  IdentityFile <SSH_KEY_PATH>
```

**SSH Port Forwarding**:
```bash
ssh -f -L 5432:localhost:5432 <USER>@<SERVER_IP> -N
```

---

## Datenfluss

```
┌──────────────────────────────────────────────────────────────┐
│ 1. COLLECTION (Jede Minute)                                  │
│                                                               │
│  Nextbike API ──GET──> query_nextbike.py                    │
│                              │                                │
│                              ▼                                │
│                        PostgreSQL DB                          │
│                    (bikes, stations, cities)                  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. PROCESSING (Täglich)                                      │
│                                                               │
│  PostgreSQL DB ──SQL──> main.py                              │
│                              │                                │
│                              ├──> trips.py                    │
│                              │     ├─ fetch_trip_data()       │
│                              │     ├─ calculate_routes()      │
│                              │     └─ remove_gps_errors()     │
│                              │                                │
│                              ├──> stations.py                 │
│                              │                                │
│                              ▼                                │
│                         JSON/CSV Export                       │
│                    (trips_*.json, stations_*.json)            │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. VISUALIZATION (GitHub Pages)                              │
│                                                               │
│  Browser ──fetch──> manifest.json                            │
│                              │                                │
│                              ├──> trips_*.json                │
│                              ├──> stations_*.json             │
│                              │                                │
│                              ▼                                │
│                      Leaflet Map Rendering                    │
│                    (Playback + Interaction)                   │
└──────────────────────────────────────────────────────────────┘
```

---

## SQLAlchemy ORM-Implementation

Das Projekt nutzt **SQLAlchemy 2.0.36** als ORM-Layer für alle Datenbankzugriffe.

### Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│  Application Layer (Dataclasses: City, Bike, Station)      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Database Abstraction Layer (AbstractDatabaseClient)        │
│  - Registry Pattern für Backend-Auswahl                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  SQLAlchemy ORM Layer                                       │
│  ├─ Engine (Connection Pooling)                             │
│  ├─ SessionMaker (Transaction Management)                   │
│  └─ Models (CityModel, BikeModel, StationModel)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PostgreSQL Database (via psycopg driver)                   │
└─────────────────────────────────────────────────────────────┘
```

### ORM-Modelle

**`database/models.py`** definiert drei Hauptmodelle:

```python
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class CityModel(Base):
    __tablename__ = 'cities'
    city_id = Column(Integer, unique=True)
    city_name = Column(Text)
    # ... weitere Felder

class BikeModel(Base):
    __tablename__ = 'bikes'
    bike_number = Column(Text)
    latitude = Column(Float)
    # ... weitere Felder

class StationModel(Base):
    __tablename__ = 'stations'
    uid = Column(Integer)
    name = Column(Text)
    # ... weitere Felder
```

### Connection Pooling

SQLAlchemy verwaltet automatisch einen Connection Pool:

```python
engine = create_engine(
    connection_string,
    pool_pre_ping=True,  # Health-Check vor Verwendung
    echo=False           # SQL-Logging
)
```

**Vorteile**:
- Wiederverwendung bestehender Verbindungen
- Automatisches Reconnect bei verlorenen Verbindungen
- Reduzierte Latenz bei häufigen Queries

### Bulk-Operationen

Für hohe Performance bei vielen Inserts:

```python
# Verwendet dataclass __dict__ für einfaches unpacking
bike_data = [bike.__dict__ for bike in bike_entries]
session.bulk_insert_mappings(BikeModel, bike_data)
```

**Performance**:
- ~10x schneller als einzelne Inserts
- Optimiert für Zeitreihen-Daten (jede Minute neue Bike-Positionen)
- Vereinfacht durch direktes dataclass unpacking

### Transaction-Management

Automatisches Rollback bei Fehlern:

```python
try:
    session.execute(stmt)
    session.commit()
except exc.SQLAlchemyError as e:
    session.rollback()
    raise e
finally:
    session.close()
```

### Dialekt-spezifische Features

PostgreSQL-spezifisches `ON CONFLICT`:

```python
from sqlalchemy.dialects.postgresql import insert

stmt = insert(CityModel).values(...)
stmt = stmt.on_conflict_do_nothing(index_elements=['city_id'])
```

### Migration von psycopg zu SQLAlchemy

**Siehe**: `SQLALCHEMY_MIGRATION.md` für Details

**Hauptunterschiede**:
- ❌ Alt: `cursor.execute(sql, params)` 
- ✅ Neu: `session.bulk_insert_mappings(Model, data)`

**Kompatibilität**:
- ✅ Alle APIs bleiben gleich
- ✅ Keine Änderungen an Dataclasses erforderlich
- ✅ Tests funktionieren ohne Anpassung

---

## Technische Details

### Datenbankschema (PostgreSQL)

```sql
-- cities Tabelle
CREATE TABLE public.cities (
    city_id INTEGER PRIMARY KEY,
    city_name VARCHAR,
    timezone VARCHAR,
    latitude FLOAT,
    longitude FLOAT,
    set_point_bikes INTEGER,
    available_bikes INTEGER,
    last_updated TIMESTAMP
);

-- bikes Tabelle (Zeitreihen)
CREATE TABLE public.bikes (
    bike_number VARCHAR,
    latitude FLOAT,
    longitude FLOAT,
    active BOOLEAN,
    state VARCHAR,
    bike_type VARCHAR,
    station_number INTEGER,
    station_uid INTEGER,
    last_updated TIMESTAMP,
    city_id INTEGER,
    city_name VARCHAR
);
CREATE INDEX idx_bikes_city_date ON bikes(city_id, last_updated);
CREATE INDEX idx_bikes_number_time ON bikes(bike_number, last_updated);

-- stations Tabelle
CREATE TABLE public.stations (
    station_uid INTEGER,
    station_number INTEGER,
    latitude FLOAT,
    longitude FLOAT,
    name VARCHAR,
    bikes_available INTEGER,
    last_updated TIMESTAMP,
    city_id INTEGER
);
```

### API-Endpunkt

**Nextbike Live API**:
```
https://api.nextbike.net/maps/nextbike-live.json?city=<CITY_ID>
```

**Response-Struktur**:
```json
{
  "countries": [{
    "country": "DE",
    "lat": 48.0,
    "lng": 11.0,
    "name": "Deutschland",
    "cities": [{
      "uid": 467,
      "name": "Stadt",
      "alias": "stadt",
      "places": [{
        "uid": 1001,
        "lat": 48.1,
        "lng": 11.1,
        "number": 101,
        "bike_list": [{
          "number": "12345",
          "active": true,
          "state": "ok",
          "bike_type": "150"
        }]
      }]
    }]
  }]
}
```

### Performance-Optimierungen

1. **Collection**:
   - Multi-Stage Docker Build (kleineres Image)
   - Alpine Linux (minimale Basis)
   - SQLAlchemy Connection Pooling für PostgreSQL
   - Bulk-Insert-Operationen (`bulk_insert_mappings()`)
   - Pre-Ping Health Checks für robuste Verbindungen
   - Session-basiertes Transaction-Management

2. **Processing**:
   - WINDOW-Funktionen in SQL (effiziente Zeitreihenanalyse)
   - Batch-Processing pro Tag
   - Gzip-Kompression für JSON-Export
   - OSMnx-Caching für Straßennetzwerke
   - SQLAlchemy Engine mit Connection Pooling

3. **Visualization**:
   - Lazy Loading von Trip-Daten
   - Canvas-basiertes Rendering (Leaflet)
   - RequestAnimationFrame für Animationen
   - Manifest.json für schnelles File-Discovery

---

## Umgebungsvariablen

### Collection `.env`
```ini
DB_TYPE=postgres
DB_HOST=postgres
DB_PORT=5432
DB_NAME=nextbike_data
DB_USER=bike_admin
DB_PASSWORD=<SECURE_PASSWORD>
CITY_IDS=467,342,123  # Komma-separiert

# Optional: Custom table names
DB_CITIES_TABLE=public.cities
DB_BIKES_TABLE=public.bikes
DB_STATIONS_TABLE=public.stations
```

### Processing `.env`
```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nextbike_data
DB_USER=bike_admin
DB_PASSWORD=<SECURE_PASSWORD>
```

---

## Bekannte Einschränkungen

1. **IPv4-Abhängigkeit**: Nextbike API & GitHub unterstützen kein IPv6
2. **Speicherplatz**: Zeitreihendaten wachsen kontinuierlich
3. **GPS-Genauigkeit**: Fehlerhafte Positionen müssen gefiltert werden
4. **Routing-Approximation**: OSM-Routing entspricht nicht immer tatsächlicher Route
5. **Rate Limiting**: API-Abfragen auf 1/Minute begrenzt (im Code)

---

## Entwicklungs-Roadmap

### Fertig ✅
- Datensammlung mit PostgreSQL
- Trip-Extraktion mit SQL WINDOW-Funktionen
- Routing über OSM
- Interaktive Webvisualisierung
- GitHub Pages Deployment

### In Arbeit 🚧
- Visualization (laut README)

### Vorschläge für zukünftige Verbesserungen
- [ ] Automatisierte Tests für Processing
- [ ] CI/CD Pipeline (GitHub Actions)
- [ ] API für Trip-Abfragen
- [ ] Erweiterte Statistiken (Nutzungsmuster, beliebte Routen)
- [ ] Clustering-Analyse (häufige Start/Ziel-Paare)
- [ ] Predictive Analytics (Vorhersage Bike-Verfügbarkeit)
- [ ] Multi-City-Vergleiche
- [ ] Export zu anderen Formaten (GeoJSON, KML)

---

## Hilfreiche Befehle

### Collection

```bash
# Logs ansehen
docker compose logs -f data_collector

# Postgres direkt abfragen
docker exec -it nextbike_postgres psql -U bike_admin -d nextbike_data

# Service neustarten
docker compose restart data_collector

# Datenbank-Backup
docker exec nextbike_postgres pg_dump -U bike_admin nextbike_data > backup.sql
```

### Processing

```bash
# Trips für heute extrahieren
python -m nextbike_processing.main \
  --city-id 467 \
  --export-folder ./data \
  --date $(date +%Y-%m-%d)

# Trips für spezifisches Datum
python -m nextbike_processing.main \
  --city-id 467 \
  --export-folder ./data \
  --date 2025-11-10
```

### Visualization

```bash
# Manifest generieren
cd visualization
./create_manifest.sh

# Lokalen Server starten
python3 -m http.server 8000

# Zu GitHub Pages deployen
./update-gh-pages.sh
```

---

## Quellen & Credits

**Inspiration**:
- [36c3 - Verkehrswende selber hacken](https://www.youtube.com/watch?v=WhgRRpA3b2c) von ubahnverleih & robbi5

**Visualization-Konzepte**:
- [Technologiestiftung Berlin - Bike-Sharing](https://github.com/technologiestiftung/bike-sharing)
- [Technologiestiftung Berlin - Bikesharing-Vis](https://github.com/technologiestiftung/bikesharing-vis)

**API-Dokumentation**:
- [WoBike - Nextbike API](https://github.com/ubahnverleih/WoBike/blob/master/Nextbike.md)

---

## Kontakt & Lizenz

**Repository**: [github.com/zwoefler/nextbike-city-analysis](https://github.com/zwoefler/nextbike-city-analysis)

**Lizenz**: Siehe LICENSE-Datei im Repository

---

## Anhang: Verzeichnisstruktur

```
nextbike-city-analysis/
├── README.md                    # Projekt-Übersicht
├── AGENTS.md                    # Diese Datei
├── LICENSE                      # Lizenz
├── requirements.txt             # Python Dependencies (Root)
├── city_ids_2025_02_15.md      # Liste aller Nextbike-Städte
├── update-gh-pages.sh          # Deployment-Skript
│
├── collection/                  # Datensammlung
│   ├── README.md
│   ├── CONTAINERFILE           # Docker Image Definition
│   ├── docker-compose.yaml     # Docker Compose Setup
│   ├── create_bike_and_stations_db.sql
│   └── data_collection/
│       ├── query_nextbike.py   # Haupt-Sammel-Skript
│       ├── requirements.txt
│       ├── database/
│       │   ├── __init__.py
│       │   ├── base.py         # Registry-Pattern
│       │   ├── models.py       # SQLAlchemy ORM-Modelle
│       │   └── postgres.py     # SQLAlchemy Implementation
│       └── tests/              # Unit Tests
│           ├── test_bike_class.py
│           ├── test_city_class.py
│           ├── test_station_class.py
│           └── test_cli.py
│
├── processing/                 # Datenverarbeitung
│   ├── README.md
│   ├── CONTAINERFILE
│   ├── requirements.txt
│   └── nextbike_processing/
│       ├── __init__.py
│       ├── main.py            # Einstiegspunkt
│       ├── config.py          # Konfiguration
│       ├── database.py        # DB-Verbindung
│       ├── trips.py           # Trip-Extraktion
│       ├── stations.py        # Stations-Verarbeitung
│       ├── cities.py          # Stadt-Daten
│       └── utils.py           # Hilfsfunktionen
│
├── visualization/             # Web-Visualisierung
│   ├── README.md
│   ├── index.html            # Haupt-HTML
│   ├── main.css              # Styling
│   ├── create_manifest.sh    # Manifest-Generator
│   ├── data/                 # Trip/Station-Daten (JSON)
│   └── scripts/              # JavaScript-Module
│       ├── main.js           # Einstiegspunkt
│       ├── state.js          # State Management
│       ├── map.js            # Leaflet Map
│       ├── data.js           # Daten-Loading
│       ├── playback.js       # Zeitraffer
│       ├── trips.js          # Trip-Rendering
│       ├── stations.js       # Stations-Marker
│       ├── table.js          # Trip-Tabelle
│       ├── utils.js          # Utils
│       └── navigation.js     # Navigation
│
├── scripts/                   # Build/Deploy-Skripte
│   ├── README.md
│   └── daily_trip_extractor.sh
│
└── docs/                      # Dokumentation
    ├── README.md
    └── setup-analysis-for-your-city.md
```

---

**Stand**: November 2025
**Version**: 1.0

