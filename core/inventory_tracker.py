#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Inventory-Tracker für die Artikel-Tracking-Anwendung.
Verantwortlich für die Verfolgung von Lagerbeständen und Artikelstatusänderungen.
"""

import os
import json
from datetime import datetime, timedelta
import pandas as pd


class InventoryTracker:
    """Klasse zur Verfolgung von Lagerbeständen und Artikelstatusänderungen."""
    
    def __init__(self, db_manager, config, logger):
        """Initialisiert den InventoryTracker.
        
        Args:
            db_manager (DatabaseManager): Datenbank-Manager-Instanz
            config (ConfigManager): Konfigurationsmanager-Instanz
            logger (Logger): Logger-Instanz
        """
        self.db_manager = db_manager
        self.config = config
        self.logger = logger
        
        # Konfigurationswerte laden
        self.history_days = int(self.config.get_value('Report', 'history_days', '30'))
        self.highlight_threshold = int(self.config.get_value('Report', 'highlight_threshold', '10'))
        self.data_path = os.path.join('data', 'inventory')
        
        # Datenverzeichnis erstellen, falls nicht vorhanden
        os.makedirs(self.data_path, exist_ok=True)
        
        self.logger.log_info("Inventory-Tracker initialisiert")
    
    def track_daily_inventory(self):
        """Führt die tägliche Bestandsverfolgung durch.
        
        Returns:
            bool: True bei Erfolg, sonst False
        """
        self.logger.log_info("Führe tägliche Bestandsverfolgung durch...")
        
        try:
            # Aktuelle Bestandsdaten abrufen
            inventory_data = self._query_current_inventory()
            
            if not inventory_data:
                self.logger.log_warning("Keine Bestandsdaten abgerufen")
                return False
            
            # Gestern gespeicherte Bestandsdaten abrufen
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_data = self.retrieve_historical_data(yesterday)
            
            # Änderungsberichte generieren
            if yesterday_data:
                # Bestandsmengen vergleichen
                self.compare_inventory_levels(inventory_data, yesterday_data)
                
                # Deaktivierungen erkennen
                self.detect_deactivations(inventory_data, yesterday_data)
            
            # Nullbestände erkennen
            self.detect_zero_inventory(inventory_data)
            
            # Aktuelle Daten speichern
            self.store_daily_data(inventory_data)
            
            self.logger.log_info("Tägliche Bestandsverfolgung abgeschlossen")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Fehler bei der täglichen Bestandsverfolgung: {str(e)}", exc_info=True)
            return False
    
    def _query_current_inventory(self):
        """Fragt aktuelle Bestandsdaten aus der Datenbank ab.
        
        Returns:
            list: Liste von Artikeldaten-Dictionaries
        """
        try:
            # SQL-Abfrage für MySQL
            if self.db_manager.connection_type.lower() == 'mysql':
                query = """
                SELECT 
                    a.artikel_id,
                    a.artikelnummer,
                    a.bezeichnung,
                    a.hersteller,
                    a.kategorie,
                    a.status,
                    COALESCE(l.bestand, 0) AS bestand,
                    l.lager_id,
                    l.lager_name
                FROM 
                    artikel a
                LEFT JOIN 
                    lagerbestand l ON a.artikel_id = l.artikel_id
                ORDER BY 
                    a.artikelnummer
                """
            # SQL-Abfrage für MSSQL
            else:
                query = """
                SELECT 
                    a.artikel_id,
                    a.artikelnummer,
                    a.bezeichnung,
                    a.hersteller,
                    a.kategorie,
                    a.status,
                    ISNULL(l.bestand, 0) AS bestand,
                    l.lager_id,
                    l.lager_name
                FROM 
                    artikel a
                LEFT JOIN 
                    lagerbestand l ON a.artikel_id = l.artikel_id
                ORDER BY 
                    a.artikelnummer
                """
            
            # Abfrage ausführen
            result = self.db_manager.execute_query(query)
            
            if result:
                self.logger.log_info(f"{len(result)} Artikel abgefragt")
            else:
                self.logger.log_warning("Keine Artikel in der Abfrage gefunden")
            
            return result
            
        except Exception as e:
            self.logger.log_error(f"Fehler bei der Bestandsabfrage: {str(e)}", exc_info=True)
            return []
    
    def compare_inventory_levels(self, current_data, previous_data):
        """Vergleicht aktuelle und vorherige Bestandsmengen.
        
        Args:
            current_data (list): Aktuelle Bestandsdaten
            previous_data (list): Vorherige Bestandsdaten
            
        Returns:
            dict: Änderungsbericht
        """
        self.logger.log_info("Vergleiche Bestandsmengen...")
        
        # Daten in DataFrames konvertieren für einfacheren Vergleich
        current_df = pd.DataFrame(current_data)
        previous_df = pd.DataFrame(previous_data)
        
        # Sicherstellen, dass die notwendigen Spalten existieren
        required_columns = ['artikel_id', 'artikelnummer', 'bestand', 'lager_id']
        if not all(col in current_df.columns for col in required_columns) or \
           not all(col in previous_df.columns for col in required_columns):
            self.logger.log_warning("Erforderliche Spalten fehlen in den Daten")
            return {}
        
        # Eindeutigen Schlüssel für den Vergleich erstellen
        current_df['key'] = current_df['artikel_id'].astype(str) + '_' + current_df['lager_id'].astype(str)
        previous_df['key'] = previous_df['artikel_id'].astype(str) + '_' + previous_df['lager_id'].astype(str)
        
        # Daten zusammenführen
        merged = pd.merge(
            current_df[['key', 'artikelnummer', 'bestand', 'bezeichnung']],
            previous_df[['key', 'bestand']],
            on='key',
            how='outer',
            suffixes=('_current', '_previous')
        )
        
        # NaN-Werte durch 0 ersetzen
        merged['bestand_current'] = merged['bestand_current'].fillna(0)
        merged['bestand_previous'] = merged['bestand_previous'].fillna(0)
        
        # Änderungen berechnen
        merged['change'] = merged['bestand_current'] - merged['bestand_previous']
        merged['change_percent'] = (merged['change'] / merged['bestand_previous'].replace(0, 1)) * 100
        
        # Signifikante Änderungen filtern
        significant_changes = merged[abs(merged['change_percent']) >= self.highlight_threshold]
        
        # Bericht erstellen
        change_report = {
            'timestamp': datetime.now().isoformat(),
            'total_articles': len(current_data),
            'significant_changes': len(significant_changes),
            'details': significant_changes.to_dict('records')
        }
        
        self.logger.log_info(
            f"{change_report['significant_changes']} Artikel mit signifikanten Bestandsänderungen gefunden"
        )
        
        # Bericht speichern
        report_file = os.path.join(
            self.data_path, 
            f"inventory_changes_{datetime.now().strftime('%Y-%m-%d')}.json"
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(change_report, f, ensure_ascii=False, indent=2)
        
        return change_report
    
    def detect_zero_inventory(self, inventory_data):
        """Erkennt Artikel mit Nullbestand.
        
        Args:
            inventory_data (list): Aktuelle Bestandsdaten
            
        Returns:
            list: Liste von Artikeln mit Nullbestand
        """
        self.logger.log_info("Erkenne Artikel mit Nullbestand...")
        
        zero_inventory = []
        
        for item in inventory_data:
            if item.get('bestand', 0) == 0 and item.get('status') == 'aktiv':
                zero_inventory.append(item)
        
        self.logger.log_info(f"{len(zero_inventory)} aktive Artikel mit Nullbestand gefunden")
        
        # Bericht speichern
        report_file = os.path.join(
            self.data_path, 
            f"zero_inventory_{datetime.now().strftime('%Y-%m-%d')}.json"
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'zero_inventory_count': len(zero_inventory),
                'items': zero_inventory
            }, f, ensure_ascii=False, indent=2)
        
        return zero_inventory
    
    def detect_deactivations(self, current_data, previous_data):
        """Erkennt deaktivierte Artikel.
        
        Args:
            current_data (list): Aktuelle Bestandsdaten
            previous_data (list): Vorherige Bestandsdaten
            
        Returns:
            list: Liste von neu deaktivierten Artikeln
        """
        self.logger.log_info("Erkenne deaktivierte Artikel...")
        
        # Daten in DataFrames konvertieren
        current_df = pd.DataFrame(current_data)
        previous_df = pd.DataFrame(previous_data)
        
        # Notwendige Spalten prüfen
        if 'artikel_id' not in current_df.columns or 'status' not in current_df.columns or \
           'artikel_id' not in previous_df.columns or 'status' not in previous_df.columns:
            self.logger.log_warning("Erforderliche Spalten fehlen in den Daten")
            return []
        
        # Status-Änderungen identifizieren
        current_status = current_df[['artikel_id', 'artikelnummer', 'bezeichnung', 'status']]
        previous_status = previous_df[['artikel_id', 'status']]
        
        # Daten zusammenführen
        merged = pd.merge(
            current_status,
            previous_status,
            on='artikel_id',
            how='inner',
            suffixes=('_current', '_previous')
        )
        
        # Deaktivierte Artikel finden
        deactivated = merged[
            (merged['status_previous'] == 'aktiv') & 
            (merged['status_current'] == 'inaktiv')
        ]
        
        deactivated_list = deactivated.to_dict('records')
        
        self.logger.log_info(f"{len(deactivated_list)} neu deaktivierte Artikel gefunden")
        
        # Bericht speichern
        report_file = os.path.join(
            self.data_path, 
            f"deactivations_{datetime.now().strftime('%Y-%m-%d')}.json"
        )
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'deactivated_count': len(deactivated_list),
                'items': deactivated_list
            }, f, ensure_ascii=False, indent=2)
        
        return deactivated_list
    
    def store_daily_data(self, inventory_data):
        """Speichert tägliche Bestandsdaten.
        
        Args:
            inventory_data (list): Zu speichernde Bestandsdaten
            
        Returns:
            bool: True bei Erfolg, sonst False
        """
        try:
            self.logger.log_info("Speichere tägliche Bestandsdaten...")
            
            # Dateiname mit aktuellem Datum
            filename = os.path.join(
                self.data_path, 
                f"inventory_{datetime.now().strftime('%Y-%m-%d')}.json"
            )
            
            # Daten mit Zeitstempel speichern
            data_with_timestamp = {
                'timestamp': datetime.now().isoformat(),
                'data': inventory_data
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_with_timestamp, f, ensure_ascii=False, indent=2)
            
            self.logger.log_info(f"Bestandsdaten gespeichert in {filename}")
            
            # Alte Daten bereinigen
            self._clean_old_data()
            
            return True
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Speichern der Bestandsdaten: {str(e)}", exc_info=True)
            return False
    
    def retrieve_historical_data(self, date):
        """Ruft historische Bestandsdaten ab.
        
        Args:
            date (datetime): Datum, für das Daten abgerufen werden sollen
            
        Returns:
            list: Historische Bestandsdaten
        """
        try:
            self.logger.log_info(f"Rufe historische Daten für {date.strftime('%Y-%m-%d')} ab...")
            
            # Dateiname mit spezifischem Datum
            filename = os.path.join(
                self.data_path, 
                f"inventory_{date.strftime('%Y-%m-%d')}.json"
            )
            
            # Prüfen, ob Datei existiert
            if not os.path.exists(filename):
                self.logger.log_warning(f"Keine historischen Daten für {date.strftime('%Y-%m-%d')} gefunden")
                return []
            
            # Daten laden
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.log_info(f"Historische Daten für {date.strftime('%Y-%m-%d')} geladen")
            return data.get('data', [])
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Abrufen historischer Daten: {str(e)}", exc_info=True)
            return []
    
    def _clean_old_data(self):
        """Bereinigt alte Bestandsdaten.
        
        Returns:
            int: Anzahl der gelöschten Dateien
        """
        try:
            self.logger.log_info("Bereinige alte Bestandsdaten...")
            
            # Maximales Alter der Daten aus Konfiguration
            max_data_age = int(self.config.get_value('Scheduler', 'max_data_age', '90'))
            cutoff_date = datetime.now() - timedelta(days=max_data_age)
            
            deleted_count = 0
            
            # Alle Dateien im Datenverzeichnis durchgehen
            for filename in os.listdir(self.data_path):
                if filename.startswith('inventory_') and filename.endswith('.json'):
                    # Datum aus Dateinamen extrahieren
                    try:
                        date_str = filename.replace('inventory_', '').replace('.json', '')
                        file_date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        # Dateien älter als das Cutoff-Datum löschen
                        if file_date < cutoff_date:
                            os.remove(os.path.join(self.data_path, filename))
                            deleted_count += 1
                    except:
                        # Bei Fehlern in der Datumsverarbeitung überspringen
                        continue
            
            if deleted_count > 0:
                self.logger.log_info(f"{deleted_count} alte Datendateien gelöscht")
            
            return deleted_count
            
        except Exception as e:
            self.logger.log_error(f"Fehler bei der Bereinigung alter Daten: {str(e)}", exc_info=True)
            return 0
