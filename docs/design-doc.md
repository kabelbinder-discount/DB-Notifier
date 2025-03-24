# Designdokument: Artikel-Tracking-Anwendung

## 1. Übersicht

Die Artikel-Tracking-Anwendung ist eine Python-basierte GUI-Applikation, die täglich automatisierte Abfragen an MySQL- und MSSQL-Datenbanken sendet, um Lagerbestände und Shop-Status verschiedener Artikel zu überwachen. Die Anwendung verfolgt Bestandsänderungen, hebt Artikel hervor, die auf 0 gelaufen sind oder deaktiviert wurden, und bietet eine umfassende Reporting-Funktionalität für die Analyse von Trends und Änderungen.

## 2. Hauptfunktionen

### 2.1 Kernfunktionen
- Tägliche automatisierte Datenbankabfragen zu konfigurierbaren Zeiten
- Unterstützung für MySQL und MSSQL-Datenbanken
- Bestandsverfolgung und Änderungserkennung
- Artikel-Status-Überwachung (aktiv/deaktiviert)
- Vergleich historischer Daten
- Berichterstellung und Visualisierung
- Fallback-Mechanismen für den Umgang mit Abfragefehlern

### 2.2 Benutzeroberfläche
- Dashboard für aktuellen Bestandsstatus
- Berichtsansicht für die Analyse historischer Daten
- Konfigurationsoberfläche für Datenbank- und Zeitplaneinstellungen
- Filter- und Sortierfunktionen
- Exportfunktionalität für Berichte

## 3. Architektur

Die Anwendung folgt einer mehrschichtigen Architektur:

### 3.1 Präsentationsschicht (GUI)
- Aufgebaut mit PyQt5 für plattformübergreifende Kompatibilität
- Responsive Benutzeroberfläche mit dynamischer Datenvisualisierung
- Berichterstellung und Exportfunktionalität

### 3.2 Geschäftslogikschicht
- Kernfunktionalität zur Bestandsverfolgung
- Berichterstellung und Datenanalyse
- Datenvergleich und Änderungserkennung

### 3.3 Datenzugriffsschicht
- Verwaltung von Datenbankverbindungen
- Abfrageausführung und Fehlerbehandlung
- Ergebnisanalyse und Caching

### 3.4 Scheduler-Schicht
- Aufgabenplanung und -ausführung
- Wiederholungsmechanismus für fehlgeschlagene Aufgaben
- Benachrichtigungssystem

### 3.5 Utility-Schicht
- Konfigurationsmanagement
- Logging-Funktionalität
- Lokale Speicherverwaltung

## 4. Datenbankintegration

### 4.1 Unterstützte Datenbanken
- MySQL 5.7+ und 8.0+
- Microsoft SQL Server 2016+

### 4.2 Verbindungsverwaltung
- Connection Pooling für optimale Leistung
- Automatische Wiederverbindung bei Fehlern
- Timeout-Handling und Wiederholungsmechanismus
- Parametrisierte Abfragen für Sicherheit

### 4.3 Abfrageausführung
- Prepared Statements für Performance
- Transaktionsunterstützung für Datenkonsistenz
- Fehlerbehandlung und Protokollierung
- Konfigurierbare Abfrage-Timeouts

## 5. Scheduler

### 5.1 Aufgabenplanung
- Tägliche Ausführung zu konfigurierbaren Zeiten
- Wiederholungsmechanismus mit konfigurierbaren Versuchen
- Aufgabenpriorisierung
- Fehlerbenachrichtigung

### 5.2 Fallback-Mechanismus
- Lokales Daten-Caching für Offline-Betrieb
- Historische Datenaggregation bei Abfragefehlern
- Inkrementelle Synchronisierung bei Wiederverbindung
- Option zur manuellen Abfrageausführung

## 6. Datenverarbeitung und Analyse

### 6.1 Bestandsverfolgung
- Tägliche Momentaufnahme der Bestände
- Änderungserkennung zwischen aufeinanderfolgenden Tagen
- Hervorhebung von Artikeln, die Bestand 0 erreichen
- Verfolgung von Artikelstatusänderungen (aktiv/deaktiviert)

### 6.2 Berichterstellung
- Tägliche Zusammenfassungsberichte
- Trendanalyse für bestimmte Zeiträume
- Anpassbare Berichtsparameter
- Export in verschiedene Formate (CSV, Excel, PDF)

## 7. Benutzeroberflächen-Design

### 7.1 Hauptfenster
- Navigationsmenü
- Status-Dashboard
- Schnellzugriff auf häufig verwendete Funktionen
- Benachrichtigungsbereich

### 7.2 Berichtsansicht
- Tabellarische Datendarstellung
- Filter- und Sortiermöglichkeiten
- Hervorhebung signifikanter Änderungen
- Datenvisualisierung (Diagramme, Grafiken)
- Exportfunktionalität

### 7.3 Einstellungs-Dialog
- Datenbankverbindungskonfiguration
- Scheduler-Einstellungen
- Berichtseinstellungen
- Anwendungsverhaltenseinstellungen

## 8. Fehlerbehandlung und Logging

### 8.1 Fehlerbehandlung
- Elegante Fehlerbehandlung
- Benutzerfreundliche Fehlermeldungen
- Automatische Wiederherstellung, wo möglich
- Detaillierte Fehlerprotokollierung

### 8.2 Logging
- Protokollierung von Anwendungsereignissen
- Fehlerprotokollierung mit Kontextinformationen
- Protokollierung von Leistungsmetriken
- Log-Rotation und -Verwaltung

## 9. Sicherheitsaspekte

### 9.1 Datenbanksicherheit
- Sichere Speicherung von Verbindungsdaten
- Parametrisierte Abfragen zur Verhinderung von SQL-Injection
- Minimales Berechtigungsprinzip für Datenbankzugriff
- Optionale Verschlüsselung für sensible Daten

### 9.2 Anwendungssicherheit
- Schutz der Konfigurationsdatei
- Sichere Speicherung von zwischengespeicherten Daten
- Optionale Zugriffssteuerung für Berichte

## 10. Leistungsbetrachtungen

### 10.1 Abfrageoptimierung
- Effizientes Abfragedesign
- Caching von Abfrageergebnissen
- Inkrementelles Laden von Daten

### 10.2 Anwendungsleistung
- Asynchrone Abfrageausführung
- Hintergrundverarbeitung für ressourcenintensive Aufgaben
- Überwachung der Ressourcennutzung

## 11. Implementierungsdetails

Die Anwendung wird in Python 3.8+ mit den folgenden Hauptkomponenten implementiert:

### 11.1 Technologien
- Python 3.8+
- PyQt5 für GUI
- SQLAlchemy für Datenbankabstraktion
- APScheduler für Aufgabenplanung
- Pandas für Datenanalyse
- Matplotlib/Seaborn für Datenvisualisierung
- Logging-Modul für Protokollierung
- ConfigParser für Konfigurationsverwaltung

### 11.2 Entwicklungsansatz
- Modulares Design mit klarer Trennung der Zuständigkeiten
- Testgetriebene Entwicklung mit PyTest
- Umfassende Dokumentation
- Versionskontrolle mit Git

### 11.3 Deployment
- Eigenständiges ausführbares Programm mit PyInstaller
- Konfiguration über externe Dateien
- Optionale stille Installation für Unternehmensbereitstellung

## 12. Dateiorganisation

Der Anwendungscode wird in die folgende Struktur organisiert:

```
artikel_tracker/
├── main.py                  # Einstiegspunkt
├── gui/                     # GUI-Komponenten
│   ├── main_window.py       # Hauptanwendungsfenster
│   ├── report_view.py       # Berichtsvisualisierung
│   └── settings_dialog.py   # Konfigurationsoberfläche
├── core/                    # Geschäftslogik
│   ├── inventory_tracker.py # Bestandsverfolgungslogik
│   └── report_generator.py  # Berichtsgenerierung
├── data/                    # Datenzugriffslayer
│   ├── db_manager.py        # Datenbankverbindungsverwaltung
│   └── query_executor.py    # Abfrageausführung
├── scheduler/               # Planungskomponenten
│   └── task_scheduler.py    # Aufgabenplanung
├── utils/                   # Hilfsfunktionen
│   ├── config_manager.py    # Konfigurationsverwaltung
│   ├── logger.py            # Logging-Funktionalität
│   └── storage.py           # Lokale Speicherverwaltung
├── config/                  # Konfigurationsdateien
│   ├── config.ini           # Anwendungskonfiguration
│   └── queries.sql          # SQL-Abfragevorlagen
├── tests/                   # Testfälle
│   ├── test_core.py         # Tests der Kernfunktionalität
│   ├── test_data.py         # Datenzugriffstests
│   └── test_gui.py          # GUI-Tests
└── docs/                    # Dokumentation
    ├── benutzerhandbuch.md  # Benutzerhandbuch
    └── entwicklerhandbuch.md# Entwicklerhandbuch
```
