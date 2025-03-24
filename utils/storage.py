#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Storage-Klasse für die Artikel-Tracking-Anwendung.
Verantwortlich für die lokale Speicherung und Verwaltung von Anwendungsdaten.
"""

import os
import json
import shutil
from datetime import datetime, timedelta


class Storage:
    """Klasse zur lokalen Speicherung und Verwaltung von Anwendungsdaten."""
    
    def __init__(self, base_path="./data/storage", logger=None):
        """Initialisiert den Storage.
        
        Args:
            base_path (str): Basispfad für die Datenspeicherung
            logger (Logger, optional): Logger-Instanz
        """
        self.base_path = base_path
        self.logger = logger
        
        # Standardverzeichnisse
        self.dirs = {
            'articles': os.path.join(base_path, 'articles'),
            'reports': os.path.join(base_path, 'reports'),
            'temp': os.path.join(base_path, 'temp')
        }
        
        # Verzeichnisse erstellen
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        
        self._log("Storage initialisiert")
    
    def save_data(self, data, category, identifier, timestamp=None):
        """Speichert Daten.
        
        Args:
            data (dict): Zu speichernde Daten
            category (str): Datenkategorie (z.B. 'articles', 'reports')
            identifier (str): Eindeutiger Bezeichner für die Daten
            timestamp (datetime, optional): Zeitstempel (Standard: aktuelles Datum/Zeit)
            
        Returns:
            str: Pfad zur gespeicherten Datei oder None bei Fehler
        """
        try:
            # Kategorieverzeichnis überprüfen/erstellen
            if category not in self.dirs:
                self.dirs[category] = os.path.join(self.base_path, category)
                os.makedirs(self.dirs[category], exist_ok=True)
            
            # Zeitstempel setzen, falls nicht angegeben
            if timestamp is None:
                timestamp = datetime.now()
            
            # Dateinamen generieren
            timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
            filename = f"{identifier}_{timestamp_str}.json"
            file_path = os.path.join(self.dirs[category], filename)
            
            # Daten mit Metadaten anreichern
            data_with_meta = {
                'timestamp': timestamp.isoformat(),
                'identifier': identifier,
                'category': category,
                'data': data
            }
            
            # Daten speichern
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_with_meta, f, ensure_ascii=False, indent=2)
            
            self._log(f"Daten gespeichert: {file_path}")
            return file_path
            
        except Exception as e:
            self._log(f"Fehler beim Speichern der Daten: {str(e)}", level='error')
            return None
    
    def load_data(self, file_path):
        """Lädt Daten aus einer Datei.
        
        Args:
            file_path (str): Pfad zur Datendatei
            
        Returns:
            dict: Geladene Daten oder None bei Fehler
        """
        try:
            if not os.path.exists(file_path):
                self._log(f"Datei nicht gefunden: {file_path}", level='warning')
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._log(f"Daten geladen: {file_path}")
            return data
            
        except Exception as e:
            self._log(f"Fehler beim Laden der Daten: {str(e)}", level='error')
            return None
    
    def delete_data(self, file_path):
        """Löscht eine Datendatei.
        
        Args:
            file_path (str): Pfad zur zu löschenden Datei
            
        Returns:
            bool: True bei Erfolg, sonst False
        """
        try:
            if not os.path.exists(file_path):
                self._log(f"Datei nicht gefunden: {file_path}", level='warning')
                return False
            
            os.remove(file_path)
            self._log(f"Datei gelöscht: {file_path}")
            return True
            
        except Exception as e:
            self._log(f"Fehler beim Löschen der Datei: {str(e)}", level='error')
            return False
    
    def get_data_by_date(self, category, date, exact_match=False):
        """Holt Daten nach Datum.
        
        Args:
            category (str): Datenkategorie
            date (datetime): Datum, für das Daten abgerufen werden sollen
            exact_match (bool): Ob nur Daten mit exaktem Datum zurückgegeben werden
            
        Returns:
            list: Liste von Datendateien oder leere Liste bei Fehler
        """
        try:
            if category not in self.dirs:
                self._log(f"Kategorie nicht gefunden: {category}", level='warning')
                return []
            
            date_str = date.strftime('%Y%m%d')
            result_files = []
            
            # Alle Dateien in der Kategorie durchsuchen
            for filename in os.listdir(self.dirs[category]):
                if not filename.endswith('.json'):
                    continue
                
                # Datum aus Dateinamen extrahieren
                try:
                    file_date_str = filename.split('_')[1][:8]  # YYYYMMDD
                    
                    if exact_match and file_date_str == date_str:
                        result_files.append(os.path.join(self.dirs[category], filename))
                    elif not exact_match and file_date_str <= date_str:
                        result_files.append(os.path.join(self.dirs[category], filename))
                except:
                    # Bei Fehlern in der Datumsverarbeitung überspringen
                    continue
            
            self._log(f"{len(result_files)} Datendateien für Datum {date_str} gefunden")
            return sorted(result_files)  # Nach Dateinamen (also Datum) sortieren
            
        except Exception as e:
            self._log(f"Fehler beim Abrufen von Daten nach Datum: {str(e)}", level='error')
            return []
    
    def get_data_by_article(self, article_id, category='articles', max_age=None):
        """Holt Daten nach Artikel.
        
        Args:
            article_id (str): Artikel-ID
            category (str): Datenkategorie (Standard: 'articles')
            max_age (int, optional): Maximales Alter der Daten in Tagen
            
        Returns:
            list: Liste von Datendateien oder leere Liste bei Fehler
        """
        try:
            if category not in self.dirs:
                self._log(f"Kategorie nicht gefunden: {category}", level='warning')
                return []
            
            result_files = []
            
            # Cutoff-Datum berechnen, falls max_age angegeben
            cutoff_date = None
            if max_age is not None:
                cutoff_date = datetime.now() - timedelta(days=max_age)
            
            # Alle Dateien in der Kategorie durchsuchen
            for filename in os.listdir(self.dirs[category]):
                if not filename.endswith('.json') or not filename.startswith(f"{article_id}_"):
                    continue
                
                file_path = os.path.join(self.dirs[category], filename)
                
                # Prüfe Alter, falls cutoff_date gesetzt
                if cutoff_date:
                    try:
                        # Datum aus Dateinamen extrahieren
                        date_str = filename.split('_')[1][:8]  # YYYYMMDD
                        file_date = datetime.strptime(date_str, '%Y%m%d')
                        
                        if file_date < cutoff_date:
                            continue
                    except:
                        # Bei Fehlern in der Datumsverarbeitung überspringen
                        continue
                
                result_files.append(file_path)
            
            self._log(f"{len(result_files)} Datendateien für Artikel {article_id} gefunden")
            return sorted(result_files)  # Nach Dateinamen (also Datum) sortieren
            
        except Exception as e:
            self._log(f"Fehler beim Abrufen von Daten nach Artikel: {str(e)}", level='error')
            return []
    
    def clean_old_data(self, category=None, days=90):
        """Bereinigt alte Daten.
        
        Args:
            category (str, optional): Zu bereinigende Kategorie (None für alle)
            days (int): Maximales Alter der Daten in Tagen
            
        Returns:
            int: Anzahl der gelöschten Dateien
        """
        try:
            self._log(f"Bereinige alte Daten (älter als {days} Tage)")
            
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            # Zu durchsuchende Kategorien bestimmen
            categories = [category] if category else self.dirs.keys()
            
            for cat in categories:
                if cat not in self.dirs or not os.path.exists(self.dirs[cat]):
                    continue
                
                for filename in os.listdir(self.dirs[cat]):
                    if not filename.endswith('.json'):
                        continue
                    
                    file_path = os.path.join(self.dirs[cat], filename)
                    
                    try:
                        # Versuche, Erstellungsdatum aus Dateinamen zu extrahieren
                        date_part = filename.split('_')[1][:8]  # YYYYMMDD
                        file_date = datetime.strptime(date_part, '%Y%m%d')
                        
                        if file_date < cutoff_date:
                            os.remove(file_path)
                            deleted_count += 1
                    except:
                        # Wenn kein Datum aus dem Dateinamen extrahiert werden kann,
                        # versuche es mit dem Dateisystem-Datum
                        try:
                            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_mtime < cutoff_date:
                                os.remove(file_path)
                                deleted_count += 1
                        except:
                            # Bei Fehlern überspringen
                            continue
            
            self._log(f"{deleted_count} alte Datendateien gelöscht")
            return deleted_count
            
        except Exception as e:
            self._log(f"Fehler bei der Bereinigung alter Daten: {str(e)}", level='error')
            return 0
    
    def _log(self, message, level='info'):
        """Hilfsmethode für Logging.
        
        Args:
            message (str): Log-Nachricht
            level (str): Log-Level ('info', 'warning', 'error', 'debug')
        """
        if not self.logger:
            print(f"[Storage] {level.upper()}: {message}")
            return
        
        if level == 'info':
            self.logger.log_info(message)
        elif level == 'warning':
            self.logger.log_warning(message)
        elif level == 'error':
            self.logger.log_error(message)
        elif level == 'debug':
            self.logger.log_debug(message)
