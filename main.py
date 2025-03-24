#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Haupteinstiegspunkt für die Artikel-Tracking-Anwendung.
Initialisiert die Anwendungskomponenten und startet die GUI.
"""

import sys
import os
import argparse
from datetime import datetime

# GUI-Imports
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings

# Anwendungsimports
from gui.main_window import MainWindow
from utils.logger import Logger
from utils.config_manager import ConfigManager
from scheduler.task_scheduler import TaskScheduler
from data.db_manager import DatabaseManager
from core.inventory_tracker import InventoryTracker


def setup_logging(config):
    """Richtet das Logging-System ein.
    
    Args:
        config (ConfigManager): Konfigurationsmanager-Instanz
    
    Returns:
        Logger: Konfigurierte Logger-Instanz
    """
    log_level = config.get_value('Logging', 'level', 'INFO')
    log_path = config.get_value('Logging', 'log_path', './logs')
    max_log_size = int(config.get_value('Logging', 'max_log_size', '10485760'))
    backup_count = int(config.get_value('Logging', 'backup_count', '5'))
    
    # Stellen Sie sicher, dass das Log-Verzeichnis existiert
    os.makedirs(log_path, exist_ok=True)
    
    logger = Logger(log_level, log_path, max_log_size, backup_count)
    logger.setup_logging()
    
    return logger


def load_config():
    """Lädt die Anwendungskonfiguration.
    
    Returns:
        ConfigManager: Konfigurierte ConfigManager-Instanz
    """
    config_path = os.path.join('config', 'config.ini')
    config = ConfigManager(config_path)
    
    # Erstelle Standard-Config, wenn keine existiert
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        config.create_default_config()
    
    config.load_config()
    return config


def initialize_app(logger, config):
    """Initialisiert die Anwendungskomponenten.
    
    Args:
        logger (Logger): Logger-Instanz
        config (ConfigManager): Konfigurationsmanager-Instanz
    
    Returns:
        tuple: Initialisierte Anwendungskomponenten
    """
    logger.log_info("Initialisiere Anwendungskomponenten...")
    
    # Datenbank-Manager initialisieren
    db_manager = DatabaseManager(config, logger)
    
    # Inventory Tracker initialisieren
    inventory_tracker = InventoryTracker(db_manager, config, logger)
    
    # Task-Scheduler initialisieren
    task_scheduler = TaskScheduler(inventory_tracker, config, logger)
    
    # Tägliche Aufgabe planen
    query_time = config.get_value('Scheduler', 'query_time', '23:00')
    task_scheduler.schedule_daily_task(query_time)
    
    logger.log_info("Anwendungskomponenten erfolgreich initialisiert.")
    return db_manager, inventory_tracker, task_scheduler


def start_gui(db_manager, inventory_tracker, task_scheduler, config, logger):
    """Startet die grafische Benutzeroberfläche.
    
    Args:
        db_manager (DatabaseManager): Datenbank-Manager-Instanz
        inventory_tracker (InventoryTracker): Inventory-Tracker-Instanz
        task_scheduler (TaskScheduler): Task-Scheduler-Instanz
        config (ConfigManager): Konfigurationsmanager-Instanz
        logger (Logger): Logger-Instanz
    
    Returns:
        int: Anwendungs-Exit-Code
    """
    logger.log_info("Starte GUI...")
    
    app = QApplication(sys.argv)
    app.setApplicationName("Artikel-Tracker")
    app.setOrganizationName("IhreOrganisation")
    
    # GUI-Thema basierend auf Konfiguration setzen
    theme = config.get_value('UI', 'theme', 'system')
    if theme == 'dark':
        app.setStyle("Fusion")
        # Hier könnte ein dunkles Theme angewendet werden
    
    # Sprache basierend auf Konfiguration setzen
    language = config.get_value('UI', 'language', 'de')
    # Hier könnte die Anwendungssprache gesetzt werden
    
    # Hauptfenster erstellen und anzeigen
    main_window = MainWindow(db_manager, inventory_tracker, task_scheduler, config, logger)
    main_window.show()
    
    # Anwendung ausführen
    return_code = app.exec_()
    
    # Scheduler stoppen, wenn Anwendung beendet wird
    task_scheduler.stop_scheduler()
    
    logger.log_info(f"Anwendung beendet mit Exit-Code: {return_code}")
    return return_code


def handle_command_line():
    """Verarbeitet Befehlszeilenargumente.
    
    Returns:
        argparse.Namespace: Geparste Befehlszeilenargumente
    """
    parser = argparse.ArgumentParser(description='Artikel-Tracking-Anwendung')
    parser.add_argument('--no-gui', action='store_true', help='Startet die Anwendung ohne GUI (für geplante Ausführungen)')
    parser.add_argument('--run-now', action='store_true', help='Führt die geplante Aufgabe sofort aus')
    parser.add_argument('--config', type=str, help='Pfad zur Konfigurationsdatei')
    
    return parser.parse_args()


def main():
    """Haupteinstiegspunkt der Anwendung."""
    # Befehlszeilenargumente verarbeiten
    args = handle_command_line()
    
    # Konfiguration laden
    config = load_config()
    
    # Logging einrichten
    logger = setup_logging(config)
    logger.log_info(f"Artikel-Tracker gestartet am {datetime.now()}")
    
    try:
        # Anwendungskomponenten initialisieren
        db_manager, inventory_tracker, task_scheduler = initialize_app(logger, config)
        
        # Bei Bedarf sofortige Ausführung der Aufgabe
        if args.run_now:
            logger.log_info("Führe geplante Aufgabe sofort aus...")
            task_scheduler.execute_task()
        
        # GUI starten, wenn nicht deaktiviert
        if not args.no_gui:
            exit_code = start_gui(db_manager, inventory_tracker, task_scheduler, config, logger)
            sys.exit(exit_code)
        else:
            # Im Headless-Modus einfach warten, bis der Scheduler die Aufgabe ausführt
            logger.log_info("Anwendung läuft im Headless-Modus. Drücken Sie Strg+C zum Beenden.")
            try:
                # Blockieren, bis der Benutzer die Anwendung beendet
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.log_info("Anwendung durch Benutzer beendet.")
                task_scheduler.stop_scheduler()
    
    except Exception as e:
        logger.log_error(f"Fehler bei der Anwendungsinitialisierung: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
