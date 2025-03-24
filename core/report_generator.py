#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Report-Generator für die Artikel-Tracking-Anwendung.
Verantwortlich für die Erstellung und Formatierung von Berichten und Analysen.
"""

import os
import csv
import json
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class ReportGenerator:
    """Klasse zur Erstellung und Formatierung von Berichten und Analysen."""
    
    def __init__(self, inventory_tracker, config, logger):
        """Initialisiert den ReportGenerator.
        
        Args:
            inventory_tracker (InventoryTracker): Inventory-Tracker-Instanz
            config (ConfigManager): Konfigurationsmanager-Instanz
            logger (Logger): Logger-Instanz
        """
        self.inventory_tracker = inventory_tracker
        self.config = config
        self.logger = logger
        
        # Konfigurationswerte laden
        self.history_days = int(self.config.get_value('Report', 'history_days', '30'))
        self.highlight_threshold = int(self.config.get_value('Report', 'highlight_threshold', '10'))
        self.export_path = self.config.get_value('Report', 'export_path', './reports')
        self.default_export_format = self.config.get_value('Report', 'default_export_format', 'excel')
        
        # Exportpfad erstellen, falls nicht vorhanden
        os.makedirs(self.export_path, exist_ok=True)
        
        # Matplotlib-Stil setzen
        plt.style.use('seaborn-v0_8-darkgrid')
        
        self.logger.log_info("Report-Generator initialisiert")
    
    def generate_daily_report(self, report_date=None):
        """Generiert einen täglichen Bericht.
        
        Args:
            report_date (datetime, optional): Berichtsdatum (Standard: aktuelles Datum)
            
        Returns:
            dict: Berichtsdaten
        """
        self.logger.log_info("Generiere täglichen Bericht...")
        
        if report_date is None:
            report_date = datetime.now()
        
        try:
            # Daten für den angegebenen Tag abrufen
            current_data = self.inventory_tracker.retrieve_historical_data(report_date)
            
            if not current_data:
                self.logger.log_warning(f"Keine Daten für {report_date.strftime('%Y-%m-%d')} gefunden")
                return None
            
            # Daten für den Vortag abrufen
            previous_date = report_date - timedelta(days=1)
            previous_data = self.inventory_tracker.retrieve_historical_data(previous_date)
            
            # Basisdaten für den Bericht
            report = {
                'date': report_date.strftime('%Y-%m-%d'),
                'generated_at': datetime.now().isoformat(),
                'total_articles': len(current_data),
                'active_articles': sum(1 for item in current_data if item.get('status') == 'aktiv'),
                'zero_inventory': []
            }
            
            # Nullbestände identifizieren
            for item in current_data:
                if item.get('bestand', 0) == 0 and item.get('status') == 'aktiv':
                    report['zero_inventory'].append({
                        'artikel_id': item.get('artikel_id'),
                        'artikelnummer': item.get('artikelnummer'),
                        'bezeichnung': item.get('bezeichnung'),
                        'lager_id': item.get('lager_id'),
                        'lager_name': item.get('lager_name')
                    })
            
            # Änderungen berechnen, wenn Vortragsdaten vorhanden
            if previous_data:
                report['changes'] = self._calculate_changes(current_data, previous_data)
                report['deactivations'] = self._detect_deactivations(current_data, previous_data)
            
            # Bericht speichern
            report_file = os.path.join(
                self.export_path, 
                f"daily_report_{report_date.strftime('%Y-%m-%d')}.json"
            )
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.logger.log_info(f"Täglicher Bericht generiert: {report_file}")
            return report
            
        except Exception as e:
            self.logger.log_error(f"Fehler bei der Generierung des täglichen Berichts: {str(e)}", exc_info=True)
            return None
    
    def generate_trend_report(self, start_date=None, end_date=None, category=None):
        """Generiert einen Trendbericht für einen Zeitraum.
        
        Args:
            start_date (datetime, optional): Startdatum
            end_date (datetime, optional): Enddatum
            category (str, optional): Artikelkategorie für Filterung
            
        Returns:
            dict: Trendbericht
        """
        self.logger.log_info("Generiere Trendbericht...")
        
        if end_date is None:
            end_date = datetime.now()
        
        if start_date is None:
            start_date = end_date - timedelta(days=self.history_days)
        
        try:
            # Datendateien für den Zeitraum abrufen
            date_range = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                          for i in range((end_date - start_date).days + 1)]
            
            inventory_data = {}
            for date_str in date_range:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    data = self.inventory_tracker.retrieve_historical_data(date_obj)
                    if data:
                        inventory_data[date_str] = data
                except:
                    continue
            
            if not inventory_data:
                self.logger.log_warning("Keine Daten für den angegebenen Zeitraum gefunden")
                return None
            
            # Trend-Analysen durchführen
            trend_report = {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'generated_at': datetime.now().isoformat(),
                'summary': self._generate_trend_summary(inventory_data),
                'charts': []
            }
            
            # Kategorie-Filter anwenden
            if category:
                trend_report['category'] = category
                for date_str in inventory_data:
                    inventory_data[date_str] = [
                        item for item in inventory_data[date_str]
                        if item.get('kategorie') == category
                    ]
            
            # Charts generieren und speichern
            chart_files = self._generate_trend_charts(inventory_data)
            trend_report['charts'] = chart_files
            
            # Bericht speichern
            report_file = os.path.join(
                self.export_path, 
                f"trend_report_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.json"
            )
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(trend_report, f, ensure_ascii=False, indent=2)
            
            self.logger.log_info(f"Trendbericht generiert: {report_file}")
            return trend_report
            
        except Exception as e:
            self.logger.log_error(f"Fehler bei der Generierung des Trendberichts: {str(e)}", exc_info=True)
            return None
    
    def format_report_data(self, report_data, format_type='table'):
        """Formatiert Berichtsdaten für die Darstellung.
        
        Args:
            report_data (dict): Berichtsdaten
            format_type (str): Formattyp ('table', 'summary', 'detailed')
            
        Returns:
            dict: Formatierte Daten
        """
        if not report_data:
            return None
        
        try:
            if format_type == 'table':
                return self._format_as_table(report_data)
            elif format_type == 'summary':
                return self._format_as_summary(report_data)
            elif format_type == 'detailed':
                return self._format_as_detailed(report_data)
            else:
                return report_data
                
        except Exception as e:
            self.logger.log_error(f"Fehler bei der Formatierung der Berichtsdaten: {str(e)}")
            return report_data
    
    def export_to_csv(self, data, filename=None):
        """Exportiert Daten als CSV.
        
        Args:
            data (list): Zu exportierende Daten
            filename (str, optional): Dateiname
            
        Returns:
            str: Pfad zur exportierten Datei
        """
        if not data:
            self.logger.log_warning("Keine Daten für CSV-Export")
            return None
        
        try:
            if not filename:
                filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            file_path = os.path.join(self.export_path, filename)
            
            # Datenstruktur prüfen
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
            
            # Mit Pandas nach CSV exportieren
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            self.logger.log_info(f"Daten als CSV exportiert: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim CSV-Export: {str(e)}")
            return None
    
    def export_to_excel(self, data, filename=None):
        """Exportiert Daten als Excel.
        
        Args:
            data (dict/list): Zu exportierende Daten
            filename (str, optional): Dateiname
            
        Returns:
            str: Pfad zur exportierten Datei
        """
        if not data:
            self.logger.log_warning("Keine Daten für Excel-Export")
            return None
        
        try:
            if not filename:
                filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            file_path = os.path.join(self.export_path, filename)
            
            # Mit Pandas nach Excel exportieren
            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                # Verschiedene Sheets basierend auf Datenstruktur erstellen
                if isinstance(data, dict):
                    # Wenn es ein Bericht mit verschiedenen Abschnitten ist
                    for key, value in data.items():
                        if isinstance(value, list) and value and isinstance(value[0], dict):
                            df = pd.DataFrame(value)
                            sheet_name = key[:31]  # Excel-Beschränkung: max. 31 Zeichen
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Zusätzliches Zusammenfassungsblatt
                    summary = {}
                    for key, value in data.items():
                        if isinstance(value, list):
                            summary[key] = len(value)
                        elif not isinstance(value, dict) and not isinstance(value, list):
                            summary[key] = value
                    
                    summary_df = pd.DataFrame([summary])
                    summary_df.to_excel(writer, sheet_name='Zusammenfassung', index=False)
                
                # Wenn es eine einfache Liste ist
                elif isinstance(data, list) and data and isinstance(data[0], dict):
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name='Daten', index=False)
            
            self.logger.log_info(f"Daten als Excel exportiert: {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Excel-Export: {str(e)}")
            return None
    
    def export_to_pdf(self, data, filename=None):
        """Exportiert Daten als PDF.
        
        Hinweis: Diese Methode benötigt zusätzliche Bibliotheken wie
        reportlab, matplotlib oder andere PDF-Generierungsbibliotheken.
        
        Args:
            data (dict/list): Zu exportierende Daten
            filename (str, optional): Dateiname
            
        Returns:
            str: Pfad zur exportierten Datei
        """
        self.logger.log_warning("PDF-Export ist noch nicht implementiert")
        return None
    
    def _calculate_changes(self, current_data, previous_data):
        """Berechnet Änderungen zwischen zwei Datensätzen.
        
        Args:
            current_data (list): Aktuelle Daten
            previous_data (list): Vorherige Daten
            
        Returns:
            dict: Änderungsbericht
        """
        # Daten in DataFrames konvertieren für einfacheren Vergleich
        current_df = pd.DataFrame(current_data)
        previous_df = pd.DataFrame(previous_data)
        
        # Eindeutigen Schlüssel für den Vergleich erstellen
        current_df['key'] = current_df['artikel_id'].astype(str) + '_' + current_df['lager_id'].astype(str)
        previous_df['key'] = previous_df['artikel_id'].astype(str) + '_' + previous_df['lager_id'].astype(str)
        
        # Daten zusammenführen
        merged = pd.merge(
            current_df[['key', 'artikelnummer', 'bezeichnung', 'bestand', 'status']],
            previous_df[['key', 'bestand', 'status']],
            on='key',
            how='outer',
            suffixes=('_current', '_previous')
        )
        
        # NaN-Werte ersetzen
        merged['bestand_current'] = merged['bestand_current'].fillna(0)
        merged['bestand_previous'] = merged['bestand_previous'].fillna(0)
        
        # Änderungen berechnen
        merged['change'] = merged['bestand_current'] - merged['bestand_previous']
        merged['change_percent'] = (merged['change'] / merged['bestand_previous'].replace(0, 1)) * 100
        
        # Signifikante Änderungen
        significant_changes = merged[abs(merged['change_percent']) >= self.highlight_threshold]
        
        return {
            'total_items': len(merged),
            'increased': len(merged[merged['change'] > 0]),
            'decreased': len(merged[merged['change'] < 0]),
            'unchanged': len(merged[merged['change'] == 0]),
            'significant_changes': significant_changes.to_dict('records')
        }
    
    def _detect_deactivations(self, current_data, previous_data):
        """Erkennt deaktivierte Artikel.
        
        Args:
            current_data (list): Aktuelle Daten
            previous_data (list): Vorherige Daten
            
        Returns:
            list: Liste deaktivierter Artikel
        """
        current_df = pd.DataFrame(current_data)
        previous_df = pd.DataFrame(previous_data)
        
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
        
        return deactivated.to_dict('records')
    
    def _generate_trend_summary(self, inventory_data):
        """Generiert eine Zusammenfassung für den Trendbericht.
        
        Args:
            inventory_data (dict): Inventardaten (Datum -> Datenliste)
            
        Returns:
            dict: Trendzusammenfassung
        """
        summary = {
            'dates': list(inventory_data.keys()),
            'total_articles': {},
            'active_articles': {},
            'zero_inventory': {},
            'avg_articles_per_day': 0,
            'trend': 'stable'
        }
        
        # Tägliche Statistiken berechnen
        for date_str, data in inventory_data.items():
            summary['total_articles'][date_str] = len(data)
            summary['active_articles'][date_str] = sum(1 for item in data if item.get('status') == 'aktiv')
            summary['zero_inventory'][date_str] = sum(1 for item in data 
                                               if item.get('bestand', 0) == 0 and item.get('status') == 'aktiv')
        
        # Durchschnittswerte berechnen
        if summary['total_articles']:
            summary['avg_articles_per_day'] = sum(summary['total_articles'].values()) / len(summary['total_articles'])
        
        # Trend bestimmen
        if len(summary['dates']) > 1:
            # Trend für aktive Artikel
            active_first = summary['active_articles'][summary['dates'][0]]
            active_last = summary['active_articles'][summary['dates'][-1]]
            
            if active_last > active_first * 1.05:  # 5% Zunahme
                summary['trend'] = 'increasing'
            elif active_last < active_first * 0.95:  # 5% Abnahme
                summary['trend'] = 'decreasing'
        
        return summary
    
    def _generate_trend_charts(self, inventory_data):
        """Generiert Diagramme für den Trendbericht.
        
        Args:
            inventory_data (dict): Inventardaten (Datum -> Datenliste)
            
        Returns:
            list: Liste der generierten Diagrammdateien
        """
        chart_files = []
        
        try:
            # Verzeichnis für Diagramme
            charts_dir = os.path.join(self.export_path, 'charts')
            os.makedirs(charts_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Aktive Artikel pro Tag
            active_articles = {}
            zero_inventory = {}
            
            for date_str, data in inventory_data.items():
                active_articles[date_str] = sum(1 for item in data if item.get('status') == 'aktiv')
                zero_inventory[date_str] = sum(1 for item in data 
                                       if item.get('bestand', 0) == 0 and item.get('status') == 'aktiv')
            
            # Aktive-Artikel-Diagramm
            plt.figure(figsize=(10, 6))
            plt.plot(list(active_articles.keys()), list(active_articles.values()), 'b-', marker='o')
            plt.title('Aktive Artikel pro Tag')
            plt.xlabel('Datum')
            plt.ylabel('Anzahl aktiver Artikel')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            active_chart_file = os.path.join(charts_dir, f"active_articles_{timestamp}.png")
            plt.savefig(active_chart_file)
            plt.close()
            
            chart_files.append(active_chart_file)
            
            # Nullbestand-Diagramm
            plt.figure(figsize=(10, 6))
            plt.plot(list(zero_inventory.keys()), list(zero_inventory.values()), 'r-', marker='o')
            plt.title('Artikel mit Nullbestand pro Tag')
            plt.xlabel('Datum')
            plt.ylabel('Anzahl Artikel mit Nullbestand')
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            zero_chart_file = os.path.join(charts_dir, f"zero_inventory_{timestamp}.png")
            plt.savefig(zero_chart_file)
            plt.close()
            
            chart_files.append(zero_chart_file)
            
            # Weitere potenzielle Diagramme:
            # - Bestandsänderungen für Top-Artikel
            # - Kategorie-Verteilung
            # - Lager-Verteilung
            # etc.
            
            return chart_files
            
        except Exception as e:
            self.logger.log_error(f"Fehler bei der Generierung von Trend-Diagrammen: {str(e)}")
            return chart_files
    
    def _format_as_table(self, report_data):
        """Formatiert Berichtsdaten als Tabelle.
        
        Args:
            report_data (dict): Berichtsdaten
            
        Returns:
            dict: Daten im Tabellenformat
        """
        formatted_data = {
            'metadata': {
                'date': report_data.get('date', ''),
                'generated_at': report_data.get('generated_at', '')
            },
            'tables': {}
        }
        
        # Nullbestand-Tabelle
        if 'zero_inventory' in report_data:
            formatted_data['tables']['zero_inventory'] = {
                'title': 'Artikel mit Nullbestand',
                'headers': ['Artikel-ID', 'Artikelnummer', 'Bezeichnung', 'Lager'],
                'data': [
                    [
                        item.get('artikel_id', ''),
                        item.get('artikelnummer', ''),
                        item.get('bezeichnung', ''),
                        item.get('lager_name', '')
                    ]
                    for item in report_data['zero_inventory']
                ]
            }
        
        # Änderungstabelle
        if 'changes' in report_data and 'significant_changes' in report_data['changes']:
            formatted_data['tables']['changes'] = {
                'title': 'Signifikante Bestandsänderungen',
                'headers': ['Artikelnummer', 'Bezeichnung', 'Alt', 'Neu', 'Änderung', 'Änderung (%)'],
                'data': [
                    [
                        item.get('artikelnummer', ''),
                        item.get('bezeichnung', ''),
                        item.get('bestand_previous', 0),
                        item.get('bestand_current', 0),
                        item.get('change', 0),
                        f"{item.get('change_percent', 0):.2f}%"
                    ]
                    for item in report_data['changes']['significant_changes']
                ]
            }
        
        # Deaktivierungstabelle
        if 'deactivations' in report_data:
            formatted_data['tables']['deactivations'] = {
                'title': 'Deaktivierte Artikel',
                'headers': ['Artikel-ID', 'Artikelnummer', 'Bezeichnung'],
                'data': [
                    [
                        item.get('artikel_id', ''),
                        item.get('artikelnummer', ''),
                        item.get('bezeichnung', '')
                    ]
                    for item in report_data['deactivations']
                ]
            }
        
        return formatted_data
    
    def _format_as_summary(self, report_data):
        """Formatiert Berichtsdaten als Zusammenfassung.
        
        Args:
            report_data (dict): Berichtsdaten
            
        Returns:
            dict: Daten im Zusammenfassungsformat
        """
        formatted_data = {
            'date': report_data.get('date', ''),
            'generated_at': report_data.get('generated_at', ''),
            'summary': {
                'total_articles': report_data.get('total_articles', 0),
                'active_articles': report_data.get('active_articles', 0),
                'zero_inventory_count': len(report_data.get('zero_inventory', [])),
            }
        }
        
        if 'changes' in report_data:
            formatted_data['summary'].update({
                'increased_inventory': report_data['changes'].get('increased', 0),
                'decreased_inventory': report_data['changes'].get('decreased', 0),
                'unchanged_inventory': report_data['changes'].get('unchanged', 0),
                'significant_changes_count': len(report_data['changes'].get('significant_changes', []))
            })
        
        if 'deactivations' in report_data:
            formatted_data['summary']['deactivated_articles'] = len(report_data.get('deactivations', []))
        
        return formatted_data
    
    def _format_as_detailed(self, report_data):
        """Formatiert Berichtsdaten im Detailformat.
        
        Args:
            report_data (dict): Berichtsdaten
            
        Returns:
            dict: Daten im Detailformat
        """
        # Für detaillierte Berichte einfach die Originaldaten zurückgeben,
        # da diese bereits alle Details enthalten
        return report_data
