# Datei- und Funktionsübersicht

## main.py
- `main()`: Einstiegspunkt der Anwendung
- `initialize_app()`: Initialisiert die Anwendungskomponenten
- `start_gui()`: Startet die GUI
- `setup_logging()`: Konfiguriert das Logging
- `load_config()`: Lädt die Anwendungskonfiguration

## gui/main_window.py
- `class MainWindow`: Hauptfensterklasse der Anwendung
  - `__init__()`: Initialisiert das Fenster
  - `setup_ui()`: Richtet UI-Komponenten ein
  - `connect_signals()`: Verbindet Signal-Handler
  - `update_dashboard()`: Aktualisiert die Dashboard-Anzeige
  - `open_report_view()`: Öffnet die Berichtsansicht
  - `open_settings()`: Öffnet den Einstellungsdialog
  - `handle_exit()`: Behandelt das Beenden der Anwendung

## gui/report_view.py
- `class ReportView`: Klasse für die Berichtsvisualisierung
  - `__init__()`: Initialisiert die Berichtsansicht
  - `setup_ui()`: Richtet UI-Komponenten ein
  - `load_report_data()`: Lädt Berichtsdaten
  - `apply_filters()`: Wendet Filter auf Berichtsdaten an
  - `highlight_changes()`: Hebt signifikante Änderungen hervor
  - `export_report()`: Exportiert Bericht in Datei
  - `generate_charts()`: Generiert Visualisierungsdiagramme

## gui/settings_dialog.py
- `class SettingsDialog`: Einstellungsdialogsklasse
  - `__init__()`: Initialisiert den Dialog
  - `setup_ui()`: Richtet UI-Komponenten ein
  - `load_current_settings()`: Lädt aktuelle Einstellungen
  - `save_settings()`: Speichert Einstellungen
  - `test_connection()`: Testet Datenbankverbindung
  - `reset_defaults()`: Setzt auf Standardeinstellungen zurück

## core/inventory_tracker.py
- `class InventoryTracker`: Bestandsverfolgungsklasse
  - `__init__()`: Initialisiert den Tracker
  - `track_daily_inventory()`: Führt tägliche Bestandsverfolgung durch
  - `compare_inventory_levels()`: Vergleicht Bestandsmengen
  - `detect_zero_inventory()`: Erkennt Artikel mit Nullbestand
  - `detect_deactivations()`: Erkennt deaktivierte Artikel
  - `store_daily_data()`: Speichert tägliche Bestandsdaten
  - `retrieve_historical_data()`: Ruft historische Daten ab

## core/report_generator.py
- `class ReportGenerator`: Berichtserstellungsklasse
  - `__init__()`: Initialisiert den Generator
  - `generate_daily_report()`: Generiert täglichen Bericht
  - `generate_trend_report()`: Generiert Trendbericht
  - `format_report_data()`: Formatiert Berichtsdaten
  - `export_to_csv()`: Exportiert Bericht als CSV
  - `export_to_excel()`: Exportiert Bericht als Excel
  - `export_to_pdf()`: Exportiert Bericht als PDF

## data/db_manager.py
- `class DatabaseManager`: Datenbankmanagementklasse
  - `__init__()`: Initialisiert den Manager
  - `connect_mysql()`: Verbindet mit MySQL-Datenbank
  - `connect_mssql()`: Verbindet mit MSSQL-Datenbank
  - `get_connection()`: Holt Datenbankverbindung
  - `close_connection()`: Schließt Datenbankverbindung
  - `test_connection()`: Testet Datenbankverbindung
  - `handle_connection_error()`: Behandelt Verbindungsfehler

## data/query_executor.py
- `class QueryExecutor`: Abfrageausführungsklasse
  - `__init__()`: Initialisiert den Executor
  - `execute_query()`: Führt SQL-Abfrage aus
  - `parse_results()`: Analysiert Abfrageergebnisse
  - `cache_results()`: Speichert Ergebnisse im Cache
  - `get_cached_results()`: Holt zwischengespeicherte Ergebnisse
  - `handle_query_error()`: Behandelt Abfragefehler
  - `load_query_template()`: Lädt Abfragevorlage

## scheduler/task_scheduler.py
- `class TaskScheduler`: Aufgabenplanungsklasse
  - `__init__()`: Initialisiert den Scheduler
  - `schedule_daily_task()`: Plant tägliche Aufgabe
  - `execute_task()`: Führt geplante Aufgabe aus
  - `handle_task_failure()`: Behandelt Aufgabenfehler
  - `retry_failed_task()`: Wiederholt fehlgeschlagene Aufgabe
  - `notify_task_status()`: Benachrichtigt über Aufgabenstatus
  - `stop_scheduler()`: Stoppt den Scheduler

## utils/config_manager.py
- `class ConfigManager`: Konfigurationsmanagementklasse
  - `__init__()`: Initialisiert den Manager
  - `load_config()`: Lädt Konfiguration
  - `save_config()`: Speichert Konfiguration
  - `get_value()`: Holt Konfigurationswert
  - `set_value()`: Setzt Konfigurationswert
  - `validate_config()`: Validiert Konfiguration
  - `create_default_config()`: Erstellt Standardkonfiguration

## utils/logger.py
- `class Logger`: Logging-Funktionalitätsklasse
  - `__init__()`: Initialisiert den Logger
  - `setup_logging()`: Richtet Logging ein
  - `log_info()`: Protokolliert Information
  - `log_warning()`: Protokolliert Warnung
  - `log_error()`: Protokolliert Fehler
  - `log_debug()`: Protokolliert Debug-Information
  - `get_log_file_path()`: Ruft Protokolldateipfad ab
  - `rotate_logs()`: Rotiert Protokolldateien

## utils/storage.py
- `class Storage`: Lokale Speicherklasse
  - `__init__()`: Initialisiert den Speicher
  - `save_data()`: Speichert Daten
  - `load_data()`: Lädt Daten
  - `delete_data()`: Löscht Daten
  - `get_data_by_date()`: Holt Daten nach Datum
  - `get_data_by_article()`: Holt Daten nach Artikel
  - `clean_old_data()`: Bereinigt alte Daten
