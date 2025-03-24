#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logger für die Artikel-Tracking-Anwendung.
Stellt Logging-Funktionalität für alle Anwendungskomponenten bereit.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import traceback


class Logger:
    """Klasse zur Verwaltung der Logging-Funktionalität."""
    
    def __init__(self, log_level="INFO", log_path="./logs", max_log_size=10485760, backup_count=5):
        """Initialisiert den Logger.
        
        Args:
            log_level (str): Logging-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_path (str): Pfad für Logdateien
            max_log_size (int): Maximale Größe einer Logdatei in Bytes
            backup_count (int): Anzahl der zu behaltenden Logdateien
        """
        self.log_level = log_level.upper()
        self.log_path = log_path
        self.max_log_size = max_log_size
        self.backup_count = backup_count
        self.logger = None
    
    def setup_logging(self):
        """Richtet das Logging-System ein.
        
        Returns:
            logging.Logger: Konfigurierter Logger
        """
        try:
            # Stellen Sie sicher, dass das Log-Verzeichnis existiert
            os.makedirs(self.log_path, exist_ok=True)
            
            # Logger erstellen
            self.logger = logging.getLogger('artikel_tracker')
            self.logger.setLevel(getattr(logging, self.log_level))
            
            # Bestehende Handler entfernen, um Doppel-Logging zu verhindern
            if self.logger.handlers:
                self.logger.handlers.clear()
            
            # Log-Dateiname basierend auf aktuellem Datum
            log_filename = os.path.join(self.log_path, f"artikel_tracker_{datetime.now().strftime('%Y-%m-%d')}.log")
            
            # Datei-Handler mit Rotation
            file_handler = RotatingFileHandler(
                log_filename,
                maxBytes=self.max_log_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            
            # Konsolen-Handler
            console_handler = logging.StreamHandler()
            
            # Formatierung
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # Handler hinzufügen
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            
            self.log_info("Logging erfolgreich eingerichtet")
            return self.logger
        
        except Exception as e:
            print(f"Fehler beim Einrichten des Loggers: {str(e)}")
            # Minimal-Logger für Fehlerfälle
            default_logger = logging.getLogger('default')
            default_logger.setLevel(logging.INFO)
            default_handler = logging.StreamHandler()
            default_logger.addHandler(default_handler)
            self.logger = default_logger
            return default_logger
    
    def log_info(self, message):
        """Protokolliert eine Information.
        
        Args:
            message (str): Zu protokollierende Nachricht
        """
        if self.logger:
            self.logger.info(message)
        else:
            print(f"INFO: {message}")
    
    def log_warning(self, message):
        """Protokolliert eine Warnung.
        
        Args:
            message (str): Zu protokollierende Warnung
        """
        if self.logger:
            self.logger.warning(message)
        else:
            print(f"WARNING: {message}")
    
    def log_error(self, message, exc_info=False):
        """Protokolliert einen Fehler.
        
        Args:
            message (str): Zu protokollierender Fehler
            exc_info (bool): Ob Exception-Information hinzugefügt werden soll
        """
        if self.logger:
            self.logger.error(message, exc_info=exc_info)
            if exc_info:
                self.logger.error(traceback.format_exc())
        else:
            print(f"ERROR: {message}")
            if exc_info:
                print(traceback.format_exc())
    
    def log_debug(self, message):
        """Protokolliert eine Debug-Information.
        
        Args:
            message (str): Zu protokollierende Debug-Information
        """
        if self.logger:
            self.logger.debug(message)
        else:
            print(f"DEBUG: {message}")
    
    def get_log_file_path(self):
        """Gibt den Pfad zur aktuellen Logdatei zurück.
        
        Returns:
            str: Pfad zur aktuellen Logdatei
        """
        log_filename = os.path.join(self.log_path, f"artikel_tracker_{datetime.now().strftime('%Y-%m-%d')}.log")
        return log_filename
    
    def rotate_logs(self):
        """Erzwingt eine Rotation der Logdateien."""
        for handler in self.logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                handler.doRollover()
                self.log_info("Logdatei-Rotation durchgeführt")
