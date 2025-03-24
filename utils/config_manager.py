#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Konfigurationsmanager für die Artikel-Tracking-Anwendung.
Verantwortlich für das Laden, Speichern und Verwalten von Anwendungseinstellungen.
"""

import os
import configparser


class ConfigManager:
    """Klasse zur Verwaltung der Anwendungskonfiguration."""
    
    def __init__(self, config_path):
        """Initialisiert den ConfigManager.
        
        Args:
            config_path (str): Pfad zur Konfigurationsdatei
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
    
    def load_config(self):
        """Lädt die Konfiguration aus der Datei.
        
        Returns:
            bool: True, wenn die Konfiguration erfolgreich geladen wurde, sonst False
        """
        try:
            if os.path.exists(self.config_path):
                self.config.read(self.config_path, encoding='utf-8')
                return True
            else:
                return False
        except Exception as e:
            print(f"Fehler beim Laden der Konfiguration: {str(e)}")
            return False
    
    def save_config(self):
        """Speichert die Konfiguration in die Datei.
        
        Returns:
            bool: True, wenn die Konfiguration erfolgreich gespeichert wurde, sonst False
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as config_file:
                self.config.write(config_file)
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Konfiguration: {str(e)}")
            return False
    
    def get_value(self, section, key, default=None):
        """Holt einen Konfigurationswert.
        
        Args:
            section (str): Konfigurationssektion
            key (str): Konfigurationsschlüssel
            default (any, optional): Standardwert, falls der Schlüssel nicht existiert
            
        Returns:
            str: Konfigurationswert oder Standardwert
        """
        try:
            if section in self.config and key in self.config[section]:
                return self.config[section][key]
            else:
                return default
        except Exception as e:
            print(f"Fehler beim Abrufen des Konfigurationswerts: {str(e)}")
            return default
    
    def set_value(self, section, key, value):
        """Setzt einen Konfigurationswert.
        
        Args:
            section (str): Konfigurationssektion
            key (str): Konfigurationsschlüssel
            value (str): Zu setzender Wert
            
        Returns:
            bool: True, wenn der Wert erfolgreich gesetzt wurde, sonst False
        """
        try:
            if section not in self.config:
                self.config[section] = {}
            
            self.config[section][key] = str(value)
            return True
        except Exception as e:
            print(f"Fehler beim Setzen des Konfigurationswerts: {str(e)}")
            return False
    
    def create_default_config(self):
        """Erstellt eine Standardkonfiguration.
        
        Returns:
            bool: True, wenn die Standardkonfiguration erfolgreich erstellt wurde, sonst False
        """
        try:
            # Datenbankeinstellungen
            self.config['Database'] = {
                'type': 'mysql',
                'host': 'localhost',
                'port': '3306',
                'username': 'benutzer',
                'password': 'passwort',
                'database': 'inventar',
                'connection_timeout': '30',
                'max_connections': '5'
            }
            
            # Scheduler-Einstellungen
            self.config['Scheduler'] = {
                'query_time': '23:00',
                'retry_attempts': '3',
                'retry_interval': '10',
                'max_data_age': '90'
            }
            
            # Berichtseinstellungen
            self.config['Report'] = {
                'highlight_threshold': '10',
                'history_days': '30',
                'default_export_format': 'excel',
                'export_path': './reports'
            }
            
            # Logging-Einstellungen
            self.config['Logging'] = {
                'level': 'INFO',
                'log_path': './logs',
                'max_log_size': '10485760',
                'backup_count': '5'
            }
            
            # UI-Einstellungen
            self.config['UI'] = {
                'theme': 'system',
                'language': 'de',
                'refresh_interval': '300'
            }
            
            return self.save_config()
        except Exception as e:
            print(f"Fehler beim Erstellen der Standardkonfiguration: {str(e)}")
            return False
    
    def validate_config(self):
        """Validiert die Konfiguration auf notwendige Werte.
        
        Returns:
            bool: True, wenn die Konfiguration gültig ist, sonst False
        """
        try:
            # Prüfen auf notwendige Sektionen
            required_sections = ['Database', 'Scheduler', 'Logging']
            for section in required_sections:
                if section not in self.config:
                    print(f"Fehlende Konfigurationssektion: {section}")
                    return False
            
            # Datenbankeinstellungen prüfen
            db_section = self.config['Database']
            required_db_keys = ['type', 'host', 'port', 'username', 'database']
            for key in required_db_keys:
                if key not in db_section:
                    print(f"Fehlender Datenbank-Konfigurationsschlüssel: {key}")
                    return False
            
            # Scheduler-Einstellungen prüfen
            scheduler_section = self.config['Scheduler']
            if 'query_time' not in scheduler_section:
                print("Fehlender Scheduler-Konfigurationsschlüssel: query_time")
                return False
            
            # Logging-Einstellungen prüfen
            logging_section = self.config['Logging']
            if 'level' not in logging_section or 'log_path' not in logging_section:
                print("Fehlende Logging-Konfigurationsschlüssel")
                return False
            
            return True
        except Exception as e:
            print(f"Fehler bei der Konfigurationsvalidierung: {str(e)}")
            return False
