#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Query-Executor für die Artikel-Tracking-Anwendung.
Verantwortlich für die Ausführung und Verwaltung von Datenbankabfragen.
"""

import os
import json
import time
from datetime import datetime


class QueryExecutor:
    """Klasse zur Ausführung und Verwaltung von Datenbankabfragen."""
    
    def __init__(self, db_manager, config, logger):
        """Initialisiert den QueryExecutor.
        
        Args:
            db_manager (DatabaseManager): Datenbank-Manager-Instanz
            config (ConfigManager): Konfigurationsmanager-Instanz
            logger (Logger): Logger-Instanz
        """
        self.db_manager = db_manager
        self.config = config
        self.logger = logger
        
        # Cache-Verzeichnis
        self.cache_dir = os.path.join('data', 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Query-Vorlagen-Verzeichnis
        self.query_dir = os.path.join('config', 'queries')
        os.makedirs(self.query_dir, exist_ok=True)
        
        self.logger.log_info("Query-Executor initialisiert")
    
    def execute_query(self, query, params=None, query_name=None, use_cache=False, cache_ttl=3600):
        """Führt eine SQL-Abfrage aus.
        
        Args:
            query (str): SQL-Abfrage oder Name der Abfragevorlage
            params (dict, optional): Parameter für die Abfrage
            query_name (str, optional): Name der Abfrage für Caching/Logging
            use_cache (bool): Ob das Caching verwendet werden soll
            cache_ttl (int): Cache-Gültigkeitsdauer in Sekunden
            
        Returns:
            list: Liste von Ergebniszeilen oder None bei Fehler
        """
        try:
            # Wenn query_name, aber keine query angegeben ist, versuche Vorlage zu laden
            if query_name and not query:
                query = self.load_query_template(query_name)
                if not query:
                    return None
            
            # Generiere query_name, falls nicht angegeben
            if not query_name:
                query_name = f"query_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Prüfe Cache, falls aktiviert
            if use_cache:
                cached_results = self.get_cached_results(query_name, params, cache_ttl)
                if cached_results is not None:
                    self.logger.log_info(f"Verwende Cache-Ergebnisse für Abfrage '{query_name}'")
                    return cached_results
            
            # Messung der Ausführungszeit starten
            start_time = time.time()
            
            # Abfrage ausführen
            self.logger.log_info(f"Führe Abfrage '{query_name}' aus")
            results = self.db_manager.execute_query(query, params)
            
            # Ausführungszeit berechnen
            execution_time = time.time() - start_time
            self.logger.log_info(f"Abfrage '{query_name}' in {execution_time:.2f} Sekunden abgeschlossen")
            
            # Ergebnisse verarbeiten und cachen
            parsed_results = self.parse_results(results)
            
            if use_cache and parsed_results:
                self.cache_results(query_name, params, parsed_results)
            
            return parsed_results
            
        except Exception as e:
            self.logger.log_error(f"Fehler bei der Ausführung der Abfrage '{query_name}': {str(e)}", exc_info=True)
            return self.handle_query_error(query_name, params, e)
    
    def parse_results(self, results):
        """Analysiert und verarbeitet Abfrageergebnisse.
        
        Args:
            results (list): Rohe Abfrageergebnisse
            
        Returns:
            list: Verarbeitete Ergebnisse
        """
        # Hier können spezifische Verarbeitungsschritte implementiert werden
        # Im einfachsten Fall werden die Ergebnisse direkt zurückgegeben
        return results
    
    def cache_results(self, query_name, params=None, results=None):
        """Speichert Abfrageergebnisse im Cache.
        
        Args:
            query_name (str): Name der Abfrage
            params (dict, optional): Abfrageparameter
            results (list): Abfrageergebnisse
            
        Returns:
            bool: True bei Erfolg, sonst False
        """
        try:
            if not results:
                return False
            
            # Cache-Dateinamen generieren
            cache_key = self._generate_cache_key(query_name, params)
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            
            # Cache-Daten mit Metadaten
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'query_name': query_name,
                'params': params,
                'results': results
            }
            
            # In Datei speichern
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            self.logger.log_debug(f"Abfrageergebnisse gecached: {cache_file}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Cachen der Ergebnisse: {str(e)}")
            return False
    
    def get_cached_results(self, query_name, params=None, ttl=3600):
        """Holt zwischengespeicherte Abfrageergebnisse.
        
        Args:
            query_name (str): Name der Abfrage
            params (dict, optional): Abfrageparameter
            ttl (int): Gültigkeitsdauer in Sekunden
            
        Returns:
            list: Zwischengespeicherte Ergebnisse oder None
        """
        try:
            # Cache-Dateinamen generieren
            cache_key = self._generate_cache_key(query_name, params)
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            
            # Prüfen, ob Cache-Datei existiert
            if not os.path.exists(cache_file):
                return None
            
            # Cache-Daten laden
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Zeitstempel prüfen
            timestamp = datetime.fromisoformat(cache_data['timestamp'])
            age = (datetime.now() - timestamp).total_seconds()
            
            # Prüfen, ob Cache noch gültig ist
            if age > ttl:
                self.logger.log_debug(f"Cache abgelaufen für {query_name} (Alter: {age:.2f}s, TTL: {ttl}s)")
                return None
            
            self.logger.log_debug(f"Cache-Treffer für {query_name} (Alter: {age:.2f}s)")
            return cache_data['results']
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Abrufen gecachter Ergebnisse: {str(e)}")
            return None
    
    def handle_query_error(self, query_name, params=None, error=None):
        """Behandelt Abfragefehler.
        
        Implementiert einen Fallback-Mechanismus für Abfragefehler.
        
        Args:
            query_name (str): Name der Abfrage
            params (dict, optional): Abfrageparameter
            error (Exception): Aufgetretener Fehler
            
        Returns:
            list: Fallback-Ergebnisse oder None
        """
        self.logger.log_warning(f"Versuche Fallback für fehlgeschlagene Abfrage '{query_name}'")
        
        # Versuche, den letzten gültigen Cache unabhängig vom Alter zu verwenden
        try:
            cache_key = self._generate_cache_key(query_name, params)
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                timestamp = datetime.fromisoformat(cache_data['timestamp'])
                age = (datetime.now() - timestamp).total_seconds()
                
                self.logger.log_info(
                    f"Verwende Fallback-Daten aus Cache für '{query_name}' (Alter: {age:.2f}s)"
                )
                
                # Markieren der Daten als Fallback
                for item in cache_data['results']:
                    if isinstance(item, dict):
                        item['_is_fallback'] = True
                
                return cache_data['results']
        
        except Exception as e:
            self.logger.log_error(f"Fallback fehlgeschlagen: {str(e)}")
        
        # Wenn kein Cache verfügbar ist, None zurückgeben
        return None
    
    def load_query_template(self, template_name):
        """Lädt eine Abfragevorlage aus einer Datei.
        
        Args:
            template_name (str): Name der Vorlage
            
        Returns:
            str: SQL-Abfrage oder None bei Fehler
        """
        try:
            # Pfad zur Vorlagendatei
            template_file = os.path.join(self.query_dir, f"{template_name}.sql")
            
            # Prüfen, ob Datei existiert
            if not os.path.exists(template_file):
                self.logger.log_error(f"Abfragevorlage nicht gefunden: {template_file}")
                return None
            
            # Vorlage laden
            with open(template_file, 'r', encoding='utf-8') as f:
                query = f.read()
            
            self.logger.log_debug(f"Abfragevorlage geladen: {template_name}")
            return query
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Laden der Abfragevorlage '{template_name}': {str(e)}")
            return None
    
    def _generate_cache_key(self, query_name, params=None):
        """Generiert einen eindeutigen Cache-Schlüssel.
        
        Args:
            query_name (str): Name der Abfrage
            params (dict, optional): Abfrageparameter
            
        Returns:
            str: Cache-Schlüssel
        """
        # Basisschlüssel ist der Abfragename
        cache_key = query_name
        
        # Wenn Parameter vorhanden sind, diese in den Schlüssel einbeziehen
        if params:
            # Parameter sortieren für konsistente Schlüssel
            param_str = "_".join([f"{k}_{v}" for k, v in sorted(params.items())])
            cache_key = f"{cache_key}_{param_str}"
        
        # Ungültige Dateinamenzeichen entfernen
        cache_key = "".join(c if c.isalnum() or c in "_-" else "_" for c in cache_key)
        
        return cache_key
