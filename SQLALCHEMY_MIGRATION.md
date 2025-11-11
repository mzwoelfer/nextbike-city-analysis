# SQLAlchemy Migration

## Übersicht

Das Projekt wurde von einer eigenen SQL-Klasse (mit psycopg) auf SQLAlchemy ORM umgestellt.

## Änderungen

### Collection Module

#### Neue Dateien
- `collection/data_collection/database/models.py`: SQLAlchemy ORM-Modelle für Cities, Bikes und Stations

#### Geänderte Dateien
- `collection/data_collection/database/postgres.py`: 
  - Umgestellt von direkten SQL-Queries auf SQLAlchemy ORM
  - Verwendet jetzt `create_engine()` und `sessionmaker()`
  - Bulk-Inserts mit `bulk_insert_mappings()` für bessere Performance
  - Automatische Tabellenerstellung mit `Base.metadata.create_all()`
  - Connection Pooling und Pre-Ping für robuste Verbindungen

### Processing Module

#### Geänderte Dateien
- `processing/nextbike_processing/database.py`:
  - Umgestellt auf SQLAlchemy Engine
  - Context Manager für Verbindungen (kompatibel mit pandas)
  - Connection Pooling für bessere Performance

## Vorteile der Umstellung

### 1. **ORM-Modelle**
   - Typsichere Datenbankzugriffe
   - Klare Tabellendefinitionen in Python
   - Automatische Tabellenerstellung

### 2. **Connection Pooling**
   - Wiederverwendung von Datenbankverbindungen
   - Bessere Performance bei vielen Abfragen
   - Automatisches Connection Health-Checking (`pool_pre_ping=True`)

### 3. **Bessere Fehlerbehandlung**
   - Rollback bei Fehlern
   - SQLAlchemy Exception-Hierarchie
   - Session-Management

### 4. **Bulk-Operationen**
   - `bulk_insert_mappings()` für schnellere Inserts
   - Effizientere Batch-Operationen

### 5. **Datenbankagnostisch**
   - Einfacher Wechsel zu anderen Datenbanken (MySQL, SQLite, etc.)
   - Dialekt-spezifische Features (z.B. PostgreSQL's `ON CONFLICT`)

### 6. **Wartbarkeit**
   - Weniger SQL-String-Manipulation
   - Bessere IDE-Unterstützung
   - Einfacheres Testen mit Mock-Sessions

## Migration für Entwickler

### Alte Implementierung (psycopg)
```python
# Direkte SQL-Queries
cursor.execute(
    "INSERT INTO bikes (...) VALUES (%s, %s, ...)",
    bike.as_tuple()
)
```

### Neue Implementierung (SQLAlchemy)
```python
# ORM-basiert
session.bulk_insert_mappings(BikeModel, bike_data)
session.commit()
```

## Kompatibilität

- ✅ Alle bestehenden Funktionen bleiben gleich
- ✅ Dataclasses (City, Bike, Station) bleiben unverändert
- ✅ API bleibt identisch (`insert_city_information()`, etc.)
- ✅ Keine Änderungen an Tests erforderlich
- ✅ Pandas-Kompatibilität erhalten (Processing)

## Abhängigkeiten

Die `requirements.txt` enthält bereits SQLAlchemy:
```
SQLAlchemy==2.0.36
psycopg[binary]==3.2.3  # SQLAlchemy nutzt psycopg als Treiber
```

## Datenbankschema

Das Schema wird jetzt automatisch aus den ORM-Modellen erstellt:

```python
# models.py
class BikeModel(Base):
    __tablename__ = 'bikes'
    
    id = Column(Integer, primary_key=True)
    bike_number = Column(Text, nullable=False)
    # ... weitere Felder
```

## Testing

Die bestehenden Tests sollten ohne Änderungen funktionieren, da die öffentliche API gleich geblieben ist.

## Bekannte Unterschiede

1. **Tabellenerstellung**: SQLAlchemy erstellt Tabellen automatisch (wenn sie nicht existieren)
2. **Connection Pooling**: Verbindungen werden wiederverwendet
3. **Error Messages**: SQLAlchemy-spezifische Exceptions statt psycopg-Exceptions

## Troubleshooting

### Problem: "No module named 'sqlalchemy'"
**Lösung**: `pip install SQLAlchemy==2.0.36`

### Problem: Connection Pool erschöpft
**Lösung**: Sessions ordnungsgemäß schließen (wird automatisch gemacht)

### Problem: Tabellen werden nicht erstellt
**Lösung**: `Base.metadata.create_all(engine)` wird automatisch aufgerufen

## Weitere Optimierungen

Mögliche zukünftige Verbesserungen:

- [ ] Relationships zwischen Modellen (Foreign Keys)
- [ ] Alembic für Schema-Migrations
- [ ] Query-Optimierung mit SQLAlchemy's Query-Builder
- [ ] Async-Support mit `sqlalchemy.ext.asyncio`
- [ ] Soft Deletes und Audit-Logging

