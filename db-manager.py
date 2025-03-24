#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Datenbankverbindungsmanager für die Artikel-Tracking-Anwendung.
Verwaltet Verbindungen zu MySQL und MSSQL Datenbanken.
"""

import time
from datetime import datetime
from sqlalchemy import create_engine, exc
from sqlalchemy.pool import QueuePool


class DatabaseManager:
    """Klasse zur Verwaltung von Datenbankverbindungen."""
    
    def __init__(self, config, logger):
        """Initialisiert den DatabaseManager.
        
        Args:
            config (ConfigManager): Konfigurationsmanager-Instanz
            logger (Logger): Logger-Instanz
        """
        self.config = config
        self.logger = logger
        self.engine = None
        self.connection_type = self.config.get_value('Database', 'type', 'mysql')
        self.max_retries = int(self.config.get_value('Scheduler', 'retry_attempts', '3'))
        self.retry_interval = int(self.config.get_value('Scheduler', 'retry_interval', '10'))
        
        # Beim Initialisieren gleich die Verbindung herstellen
        self.connect()
    
    def connect(self):
        """Stellt eine Verbindung zur konfigurierten Datenbank her."""
        self.logger.log_info(f"Verbindung zur {self.connection_type}-Datenbank wird hergestellt...")
        
        try:
            if self.connection_type.lower() == 'mysql':
                self.connect_mysql()
            elif self.connection_type.lower() == 'mssql':
                self.connect_mssql()
            else:
                self.logger.log_error(f"Unbekannter Datenbanktyp: {self.connection_type}")
                raise ValueError(f"Unbekannter Datenbanktyp: {self.connection_type}")
                
            self.logger.log_info("Datenbankverbindung erfolgreich hergestellt.")
        except Exception as e:
            self.logger.log_error(f"Fehler beim Verbinden zur Datenbank: {str(e)}")
            self.handle_connection_error(e)
    
    def connect_mysql(self):
        """Stellt eine Verbindung zu einer MySQL-Datenbank her."""
        host = self.config.get_value('Database', 'host', 'localhost')
        port = self.config.get_value('Database', 'port', '3306')
        username = self.config.get_value('Database', 'username', '')
        password = self.config.get_value('Database', 'password', '')
        database = self.config.get_value('Database', 'database', '')
        max_connections = int(self.config.get_value('Database', 'max_connections', '5'))
        
        connection_string = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        
        self.engine = create_engine(
            connection_string,
            pool_size=max_connections,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,  # Recycelt Verbindungen nach 1 Stunde
            pool_pre_ping=True  # Prüft Verbindungen vor Benutzung
        )
    
    def connect_mssql(self):
        """Stellt eine Verbindung zu einer MSSQL-Datenbank her."""
        host = self.config.get_value('Database', 'host', 'localhost')
        port = self.config.get_value('Database', 'port', '1433')
        username = self.config.get_value('Database', 'username', '')
        password = self.config.get_value('Database', 'password', '')
        database = self.config.get_value('Database', 'database', '')
        max_connections = int(self.config.get_value('Database', 'max_connections', '5'))
        
        # pyodbc für MSSQL verwenden
        connection_string = f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver=ODBC+Driver+17+for+SQL+Server"
        
        self.engine = create_engine(
            connection_string,
            pool_size=max_connections,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True
        )
    
    def get_connection(self):
        """Gibt eine Datenbankverbindung zurück.
        
        Returns:
            Connection: Aktive Datenbankverbindung
            
        Raises:
            Exception: Wenn keine Verbindung hergestellt werden kann
        """
        if not self.engine:
            self.connect()
        
        try:
            return self.engine.connect()
        except exc.DBAPIError as e:
            self.logger.log_error(f"Datenbankverbindungsfehler: {str(e)}")
            self.handle_connection_error(e)
            return self.engine.connect()  # Noch einmal versuchen nach Reconnect
    
    def close_connection(self, connection):
        """Schließt eine Datenbankverbindung.
        
        Args:
            connection (Connection): Die zu schließende Verbindung
        """
        if connection:
            connection.close()
    
    def test_connection(self):
        """Testet die Datenbankverbindung.
        
        Returns:
            bool: True, wenn die Verbindung erfolgreich ist, sonst False
        """
        try:
            connection = self.get_connection()
            connection.execute("SELECT 1")
            self.close_connection(connection)
            return True
        except Exception as e:
            self.logger.log_error(f"Verbindungstest fehlgeschlagen: {str(e)}")
            return False
    
    def handle_connection_error(self, error):
        """Behandelt Datenbankverbindungsfehler mit Wiederholungslogik.
        
        Args:
            error (Exception): Der aufgetretene Fehler
            
        Raises:
            Exception: Wenn nach allen Wiederholungsversuchen keine Verbindung hergestellt werden kann
        """
        retry_count = 0
        
        while retry_count < self.max_retries:
            retry_count += 1
            wait_time = self.retry_interval * retry_count
            
            self.logger.log_warning(
                f"Datenbankverbindungsfehler. Wiederholungsversuch {retry_count}/{self.max_retries} "
                f"in {wait_time} Sekunden..."
            )
            
            time.sleep(wait_time)
            
            try:
                if self.connection_type.lower() == 'mysql':
                    self.connect_mysql()
                else:
                    self.connect_mssql()
                
                # Verbindung testen
                if self.test_connection():
                    self.logger.log_info("Datenbankverbindung wiederhergestellt.")
                    return
            except Exception as e:
                self.logger.log_error(f"Wiederholungsversuch {retry_count} fehlgeschlagen: {str(e)}")
        
        self.logger.log_error(f"Alle Wiederholungsversuche fehlgeschlagen. Ursprünglicher Fehler: {str(error)}")
        raise error
    
    def execute_query(self, query, params=None):
        """Führt eine SQL-Abfrage aus und gibt die Ergebnisse zurück.
        
        Diese Methode ist ein Wrapper für den QueryExecutor, um einfache Abfragen
        direkt über den DatabaseManager ausführen zu können.
        
        Args:
            query (str): Die auszuführende SQL-Abfrage
            params (dict, optional): Parameter für die Abfrage
            
        Returns:
            list: Liste von Ergebniszeilen
        """
        connection = None
        try:
            connection = self.get_connection()
            if params:
                result = connection.execute(query, params)
            else:
                result = connection.execute(query)
            
            # Ergebnisse in eine Liste konvertieren, bevor die Verbindung geschlossen wird
            rows = [dict(row) for row in result]
            return rows
        except Exception as e:
            self.logger.log_error(f"Fehler bei der Abfrageausführung: {str(e)}")
            raise
        finally:
            if connection:
                self.close_connection(connection)
