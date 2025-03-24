# Artikel-Tracking Anwendung - Installationsanleitung

Diese Anleitung beschreibt die Installation und Konfiguration der Artikel-Tracking-Anwendung.

## Voraussetzungen

* Python 3.8 oder höher
* MySQL 5.7+ oder MS SQL Server 2016+
* Pip (Python-Paketmanager)
* Git (optional)

## Installation

### Schritt 1: Anwendung herunterladen

Klonen Sie das Repository oder laden Sie das Paket herunter:

```bash
git clone https://github.com/ihrusername/artikel-tracker.git
cd artikel-tracker
```

### Schritt 2: Virtuelle Umgebung erstellen (empfohlen)

```bash
# Unter Windows:
python -m venv venv
venv\Scripts\activate

# Unter Linux/macOS:
python3 -m venv venv
source venv/bin/activate
```

### Schritt 3: Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### Schritt 4: Datenbank einrichten

1. Erstellen Sie eine Datenbank in Ihrem MySQL- oder MS SQL-Server
2. Verwenden Sie das passende Datenbankschema aus dem `config`-Verzeichnis:
   * `schema_mysql.sql` für MySQL
   * `schema_mssql.sql` für MS SQL Server

```bash
# Beispiel für MySQL
mysql -u root -p < config/schema_mysql.sql

# Beispiel für MS SQL Server (mit sqlcmd)
sqlcmd -S localhost -i config/schema_mssql.sql -U sa -P IhrPasswort
```

### Schritt 5: Konfiguration erstellen

Kopieren Sie die Beispielkonfiguration und passen Sie sie an:

```bash
cp config/config.ini.example config/config.ini
```

Bearbeiten Sie die Datei `config/config.ini` und stellen Sie insbesondere die Datenbankverbindungsdaten ein:

```ini
[Database]
type = mysql  # oder mssql
host = localhost
port = 3306   # oder 1433 für MSSQL
username = benutzer
password = passwort
database = inventar
```

### Schritt 6: Verzeichnisstruktur erstellen

Die Anwendung benötigt einige Verzeichnisse für Logs, Berichte und zwischengespeicherte Daten:

```bash
mkdir -p logs reports data/inventory data/cache
```

## Starten der Anwendung

### Normale Ausführung

```bash
python main.py
```

### Headless-Modus (nur für Hintergrundaufgaben ohne GUI)

```bash
python main.py --no-gui
```

### Einmalige Aufgabenausführung

```bash
python main.py --run-now
```

## Fehlersuche

### Verbindungsprobleme zur Datenbank

- Überprüfen Sie Ihre Firewall-Einstellungen
- Stellen Sie sicher, dass der Datenbankserver läuft
- Überprüfen Sie Benutzername und Passwort in der Konfigurationsdatei
- Prüfen Sie, ob der Benutzer Zugriff auf die Datenbank hat

### Log-Dateien überprüfen

Bei Problemen können die Log-Dateien wichtige Hinweise geben:

```bash
cat logs/artikel_tracker_YYYY-MM-DD.log
```

### Fehlende Abhängigkeiten

Falls bestimmte Python-Module nicht gefunden werden:

```bash
pip install -r requirements.txt --no-cache-dir
```

## Konfigurationsoptionen

Die wichtigsten Konfigurationsoptionen finden Sie in der Datei `config/config.ini`:

- **Datenbank**: Verbindungseinstellungen, Typ, Benutzerdaten
- **Scheduler**: Zeit für tägliche Abfrage, Wiederholungsversuche
- **Reporting**: Thresholds, Exportpfade, Formate
- **Logging**: Log-Level, Pfade, Rotation
- **UI**: Thema, Sprache, Aktualisierungsintervall

## Weitere Informationen

Ausführlichere Informationen finden Sie in der Datei `readme.md`.
