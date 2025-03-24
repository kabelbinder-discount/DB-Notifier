# Artikel-Tracking-Anwendung

Eine Python-GUI-Anwendung zur Verfolgung von Lagerbeständen und Artikelstatusänderungen durch automatisierte Datenbankabfragen.

![Dashboard Screenshot](doc/img/dashboard_screenshot.png)

## Funktionen

- Tägliche automatisierte Datenbankabfragen zu konfigurierbaren Zeiten
- Unterstützung für MySQL- und MSSQL-Datenbanken
- Bestandsverfolgung und Änderungserkennung
- Überwachung des Artikelstatus (aktiv/deaktiviert)
- Vergleich historischer Daten
- Berichterstellung und Visualisierung
- Fallback-Mechanismen für den Umgang mit Abfragefehlern

## Anforderungen

- Python 3.8 oder höher
- PyQt5
- SQLAlchemy
- MySQL Connector Python (für MySQL-Verbindungen)
- pyodbc (für MSSQL-Verbindungen)
- APScheduler
- Pandas
- Matplotlib/Seaborn

## Installation

1. Repository klonen:
   ```
   git clone https://github.com/ihrusername/artikel-tracker.git
   cd artikel-tracker
   ```

2. Erforderliche Abhängigkeiten installieren:
   ```
   pip install -r requirements.txt
   ```

3. Anwendung konfigurieren:
   - Kopieren Sie `config/config.ini.example` nach `config/config.ini`
   - Bearbeiten Sie `config/config.ini` mit Ihren Datenbankverbindungsdetails und Scheduler-Einstellungen

4. Datenbank einrichten:
   - Verwenden Sie die SQL-Skripte im `config`-Verzeichnis, um die Datenbankstruktur zu erstellen:
     - `schema_mysql.sql` für MySQL
     - `schema_mssql.sql` für MS SQL Server

Ausführlichere Installationsanweisungen finden Sie in der [Installationsanleitung](INSTALLATION.md).

## Verwendung

1. Starten Sie die Anwendung:
   ```
   python main.py
   ```

2. Konfigurieren Sie Datenbankverbindungen im Einstellungsdialog.

3. Die Anwendung führt die konfigurierten Abfragen automatisch zur angegebenen Zeit jeden Tag aus.

4. Verwenden Sie die Berichtsansicht, um Bestandsänderungen und Artikelstatus zu analysieren.

### Befehlszeilenoptionen

- `--no-gui`: Startet die Anwendung im Headless-Modus (ohne GUI)
- `--run-now`: Führt die geplante Aufgabe sofort aus
- `--config PATH`: Gibt einen alternativen Pfad zur Konfigurationsdatei an

## Konfiguration

Die Anwendung kann über die Datei `config/config.ini` konfiguriert werden:

### Datenbankkonfiguration

```ini
[Database]
type = mysql  # oder mssql
host = localhost
port = 3306
username = benutzer
password = passwort
database = inventar
```

### Scheduler-Konfiguration

```ini
[Scheduler]
query_time = 23:00  # Zeit für die tägliche Abfrage (24-Stunden-Format)
retry_attempts = 3  # Anzahl der Wiederholungsversuche bei Fehlern
retry_interval = 10  # Intervall zwischen Wiederholungen in Minuten
```

### Berichtskonfiguration

```ini
[Report]
highlight_threshold = 10  # Prozentuale Änderung für Hervorhebung in Berichten
history_days = 30  # Anzahl der Tage für historische Daten
```

## Programmstruktur

Die Anwendung ist in mehrere Module unterteilt:

- **core/**: Geschäftslogik
  - `inventory_tracker.py`: Bestandsverfolgung und Änderungserkennung
  - `report_generator.py`: Berichtsgenerierung und -formatierung
- **data/**: Datenzugriff
  - `db_manager.py`: Datenbankverbindungsverwaltung
  - `query_executor.py`: Abfrageausführung und -caching
- **gui/**: Benutzeroberfläche
  - `main_window.py`: Hauptfenster der Anwendung
  - `settings_dialog.py`: Einstellungsdialog
  - `report_view.py`: Berichtsanzeige
- **scheduler/**: Aufgabenplanung
  - `task_scheduler.py`: Zeitplanung und Aufgabenausführung
- **utils/**: Hilfsfunktionen
  - `config_manager.py`: Konfigurationsverwaltung
  - `logger.py`: Logging-Funktionalität
  - `storage.py`: Lokale Datenspeicherung

## Fallback-Mechanismus

Die Anwendung enthält Fallback-Mechanismen für den Umgang mit Abfragefehlern:

1. Wiederholungsmechanismus mit konfigurierbaren Versuchen
2. Lokales Daten-Caching für Offline-Betrieb
3. Historische Datenaggregation bei Abfragefehlern
4. Inkrementelle Synchronisierung bei Wiederverbindung
5. Option zur manuellen Abfrageausführung

## Fehlersuche

Häufige Probleme und Lösungen:

1. **Verbindungsprobleme zur Datenbank**
   - Überprüfen Sie Ihre Firewall-Einstellungen
   - Stellen Sie sicher, dass der Datenbankserver läuft
   - Überprüfen Sie Benutzername und Passwort

2. **Scheduler führt Aufgaben nicht aus**
   - Überprüfen Sie die Systemzeit
   - Stellen Sie sicher, dass die Anwendung nicht im Ruhezustand ist
   - Überprüfen Sie die Scheduler-Protokolle

3. **Fehler bei der Berichtsgenerierung**
   - Überprüfen Sie die Datenbankabfragen auf Richtigkeit
   - Stellen Sie sicher, dass alle erforderlichen Felder in der Datenbank vorhanden sind

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Siehe die LICENSE-Datei für Details.

## Beitrag

Beiträge sind willkommen! Bitte reichen Sie einen Pull Request ein.

1. Forken Sie das Repository
2. Erstellen Sie Ihren Feature-Branch (`git checkout -b feature/tolle-funktion`)
3. Committen Sie Ihre Änderungen (`git commit -m 'Tolle Funktion hinzugefügt'`)
4. Pushen Sie zum Branch (`git push origin feature/tolle-funktion`)
5. Öffnen Sie einen Pull Request

## Support

Bei Fragen oder Problemen öffnen Sie bitte ein Issue im GitHub-Repository oder kontaktieren Sie die Betreuer.
