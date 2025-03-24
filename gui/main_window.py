#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hauptfenster für die Artikel-Tracking-Anwendung.
Zentrale GUI-Komponente für die Benutzerinteraktion.
"""

import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QProgressBar, QTableWidget, 
                           QTableWidgetItem, QHeaderView, QMessageBox, 
                           QAction, QMenu, QStatusBar, QToolBar, QComboBox,
                           QTabWidget, QFrame, QSplitter, QApplication)
from PyQt5.QtCore import Qt, QTimer, QSize, QSettings, pyqtSlot, QDateTime
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap

# Anwendungsimporte
from gui.settings_dialog import SettingsDialog
from gui.report_view import ReportView
from core.report_generator import ReportGenerator


class MainWindow(QMainWindow):
    """Hauptfensterklasse der Anwendung."""
    
    def __init__(self, db_manager, inventory_tracker, task_scheduler, config, logger):
        """Initialisiert das Hauptfenster.
        
        Args:
            db_manager (DatabaseManager): Datenbank-Manager-Instanz
            inventory_tracker (InventoryTracker): Inventory-Tracker-Instanz
            task_scheduler (TaskScheduler): Task-Scheduler-Instanz
            config (ConfigManager): Konfigurationsmanager-Instanz
            logger (Logger): Logger-Instanz
        """
        super().__init__()
        
        self.db_manager = db_manager
        self.inventory_tracker = inventory_tracker
        self.task_scheduler = task_scheduler
        self.config = config
        self.logger = logger
        
        # Report-Generator initialisieren
        self.report_generator = ReportGenerator(inventory_tracker, config, logger)
        
        # Einstellungen laden
        self.settings = QSettings("IhreOrganisation", "Artikel-Tracker")
        
        # Aktualisierungsintervall für das Dashboard (in Sekunden)
        self.refresh_interval = int(self.config.get_value('UI', 'refresh_interval', '300'))
        
        # Timer für die automatische Aktualisierung
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_dashboard)
        
        # UI einrichten
        self.setup_ui()
        
        # Signale verbinden
        self.connect_signals()
        
        # Initialen Status aktualisieren
        self.update_status()
        
        # Dashboard initial aktualisieren
        self.update_dashboard()
        
        # Timer starten
        if self.refresh_interval > 0:
            self.refresh_timer.start(self.refresh_interval * 1000)
        
        self.logger.log_info("Hauptfenster initialisiert")
    
    def setup_ui(self):
        """Richtet die UI-Komponenten ein."""
        self.setWindowTitle("Artikel-Tracker")
        self.setMinimumSize(800, 600)
        
        # Fenstergröße aus Einstellungen wiederherstellen
        if self.settings.contains("mainwindow/size"):
            self.resize(self.settings.value("mainwindow/size"))
        if self.settings.contains("mainwindow/pos"):
            self.move(self.settings.value("mainwindow/pos"))
        
        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Hauptlayout
        main_layout = QVBoxLayout(central_widget)
        
        # Tabs für verschiedene Ansichten
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Dashboard-Tab
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        
        # Übersichtsbereich
        overview_frame = QFrame()
        overview_frame.setFrameShape(QFrame.StyledPanel)
        overview_layout = QHBoxLayout(overview_frame)
        
        # Statistik-Labels
        self.total_articles_label = QLabel("Gesamtartikel: -")
        self.total_articles_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.active_articles_label = QLabel("Aktive Artikel: -")
        self.active_articles_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.zero_inventory_label = QLabel("Nullbestand: -")
        self.zero_inventory_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.last_update_label = QLabel("Letzte Aktualisierung: -")
        
        overview_layout.addWidget(self.total_articles_label)
        overview_layout.addWidget(self.active_articles_label)
        overview_layout.addWidget(self.zero_inventory_label)
        overview_layout.addWidget(self.last_update_label)
        
        dashboard_layout.addWidget(overview_frame)
        
        # Tabellen-Splitter
        tables_splitter = QSplitter(Qt.Vertical)
        
        # Nullbestand-Tabelle
        zero_inventory_frame = QFrame()
        zero_inventory_frame.setFrameShape(QFrame.StyledPanel)
        zero_inventory_layout = QVBoxLayout(zero_inventory_frame)
        
        zero_inventory_header = QLabel("Artikel mit Nullbestand")
        zero_inventory_header.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.zero_inventory_table = QTableWidget()
        self.zero_inventory_table.setColumnCount(4)
        self.zero_inventory_table.setHorizontalHeaderLabels(["Artikel-ID", "Artikelnummer", "Bezeichnung", "Lager"])
        self.zero_inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        zero_inventory_layout.addWidget(zero_inventory_header)
        zero_inventory_layout.addWidget(self.zero_inventory_table)
        
        # Letzte Änderungen Tabelle
        changes_frame = QFrame()
        changes_frame.setFrameShape(QFrame.StyledPanel)
        changes_layout = QVBoxLayout(changes_frame)
        
        changes_header = QLabel("Letzte signifikante Änderungen")
        changes_header.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.changes_table = QTableWidget()
        self.changes_table.setColumnCount(6)
        self.changes_table.setHorizontalHeaderLabels(
            ["Artikelnummer", "Bezeichnung", "Alter Bestand", "Neuer Bestand", "Änderung", "Änderung (%)"]
        )
        self.changes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        changes_layout.addWidget(changes_header)
        changes_layout.addWidget(self.changes_table)
        
        tables_splitter.addWidget(zero_inventory_frame)
        tables_splitter.addWidget(changes_frame)
        
        dashboard_layout.addWidget(tables_splitter)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Aktualisieren")
        self.refresh_button.setIcon(QIcon.fromTheme("view-refresh"))
        
        self.reports_button = QPushButton("Berichte öffnen")
        self.reports_button.setIcon(QIcon.fromTheme("x-office-spreadsheet"))
        
        self.execute_now_button = QPushButton("Jetzt abfragen")
        self.execute_now_button.setIcon(QIcon.fromTheme("system-run"))
        
        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addWidget(self.reports_button)
        buttons_layout.addWidget(self.execute_now_button)
        buttons_layout.addStretch()
        
        dashboard_layout.addLayout(buttons_layout)
        
        # Tab hinzufügen
        self.tabs.addTab(dashboard_widget, "Dashboard")
        
        # Menü erstellen
        self.create_menu()
        
        # Statusleiste
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # Verbindungsstatus
        self.connection_label = QLabel()
        self.statusBar.addPermanentWidget(self.connection_label)
        
        # Progress Bar für Operationen
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(150)
        self.progress_bar.setVisible(False)
        self.statusBar.addPermanentWidget(self.progress_bar)
    
    def create_menu(self):
        """Erstellt die Menüstruktur der Anwendung."""
        # Hauptmenü
        main_menu = self.menuBar()
        
        # Datei-Menü
        file_menu = main_menu.addMenu("Datei")
        
        # Einstellungen-Aktion
        settings_action = QAction(QIcon.fromTheme("preferences-system"), "Einstellungen", self)
        settings_action.setShortcut("Ctrl+P")
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Beenden-Aktion
        exit_action = QAction(QIcon.fromTheme("application-exit"), "Beenden", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.handle_exit)
        file_menu.addAction(exit_action)
        
        # Aktionen-Menü
        actions_menu = main_menu.addMenu("Aktionen")
        
        # Aktualisieren-Aktion
        refresh_action = QAction(QIcon.fromTheme("view-refresh"), "Dashboard aktualisieren", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.update_dashboard)
        actions_menu.addAction(refresh_action)
        
        # Jetzt abfragen Aktion
        execute_action = QAction(QIcon.fromTheme("system-run"), "Jetzt abfragen", self)
        execute_action.triggered.connect(self.execute_task_now)
        actions_menu.addAction(execute_action)
        
        actions_menu.addSeparator()
        
        # Export-Untermenü
        export_menu = actions_menu.addMenu("Exportieren")
        
        export_csv_action = QAction("Als CSV exportieren", self)
        export_csv_action.triggered.connect(lambda: self.export_data("csv"))
        export_menu.addAction(export_csv_action)
        
        export_excel_action = QAction("Als Excel exportieren", self)
        export_excel_action.triggered.connect(lambda: self.export_data("excel"))
        export_menu.addAction(export_excel_action)
        
        # Berichte-Menü
        reports_menu = main_menu.addMenu("Berichte")
        
        # Berichtsansicht öffnen
        open_reports_action = QAction("Berichtsansicht öffnen", self)
        open_reports_action.triggered.connect(self.open_report_view)
        reports_menu.addAction(open_reports_action)
        
        reports_menu.addSeparator()
        
        # Tagesbericht erstellen
        daily_report_action = QAction("Tagesbericht erstellen", self)
        daily_report_action.triggered.connect(self.generate_daily_report)
        reports_menu.addAction(daily_report_action)
        
        # Trendbericht erstellen
        trend_report_action = QAction("Trendbericht erstellen", self)
        trend_report_action.triggered.connect(self.generate_trend_report)
        reports_menu.addAction(trend_report_action)
        
        # Hilfe-Menü
        help_menu = main_menu.addMenu("Hilfe")
        
        # Über-Aktion
        about_action = QAction(QIcon.fromTheme("help-about"), "Über", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def connect_signals(self):
        """Verbindet Signal-Handler."""
        # Button-Signale
        self.refresh_button.clicked.connect(self.update_dashboard)
        self.reports_button.clicked.connect(self.open_report_view)
        self.execute_now_button.clicked.connect(self.execute_task_now)
    
    def update_dashboard(self):
        """Aktualisiert die Dashboard-Anzeige."""
        self.logger.log_info("Aktualisiere Dashboard...")
        
        try:
            # Fortschrittsanzeige anzeigen
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(20)
            QApplication.processEvents()
            
            # Aktuelle Bestandsdaten abrufen
            today = datetime.now()
            current_data = self.inventory_tracker.retrieve_historical_data(today)
            
            self.progress_bar.setValue(40)
            QApplication.processEvents()
            
            if not current_data:
                self.statusBar.showMessage("Keine aktuellen Daten gefunden. Bitte führen Sie eine Abfrage durch.")
                self.progress_bar.setVisible(False)
                return
            
            # Statistik aktualisieren
            total_articles = len(current_data)
            active_articles = sum(1 for item in current_data if item.get('status') == 'aktiv')
            
            # Nullbestände identifizieren
            zero_inventory = []
            for item in current_data:
                if item.get('bestand', 0) == 0 and item.get('status') == 'aktiv':
                    zero_inventory.append(item)
            
            # Labels aktualisieren
            self.total_articles_label.setText(f"Gesamtartikel: {total_articles}")
            self.active_articles_label.setText(f"Aktive Artikel: {active_articles}")
            self.zero_inventory_label.setText(f"Nullbestand: {len(zero_inventory)}")
            self.last_update_label.setText(f"Letzte Aktualisierung: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
            
            self.progress_bar.setValue(60)
            QApplication.processEvents()
            
            # Nullbestand-Tabelle aktualisieren
            self.update_zero_inventory_table(zero_inventory)
            
            self.progress_bar.setValue(80)
            QApplication.processEvents()
            
            # Letzte Änderungen laden und anzeigen
            self.update_changes_table()
            
            self.progress_bar.setValue(100)
            
            # Status aktualisieren
            self.update_status()
            
            self.statusBar.showMessage("Dashboard erfolgreich aktualisiert", 3000)
            
        except Exception as e:
            self.logger.log_error(f"Fehler bei der Dashboard-Aktualisierung: {str(e)}", exc_info=True)
            self.statusBar.showMessage(f"Fehler bei der Aktualisierung: {str(e)}", 5000)
        
        finally:
            self.progress_bar.setVisible(False)
    
    def update_zero_inventory_table(self, zero_inventory):
        """Aktualisiert die Nullbestand-Tabelle.
        
        Args:
            zero_inventory (list): Liste von Artikeln mit Nullbestand
        """
        # Tabelle leeren
        self.zero_inventory_table.setRowCount(0)
        
        # Neue Daten hinzufügen
        for row, item in enumerate(zero_inventory):
            self.zero_inventory_table.insertRow(row)
            
            # Zellen füllen
            self.zero_inventory_table.setItem(row, 0, QTableWidgetItem(str(item.get('artikel_id', ''))))
            self.zero_inventory_table.setItem(row, 1, QTableWidgetItem(str(item.get('artikelnummer', ''))))
            self.zero_inventory_table.setItem(row, 2, QTableWidgetItem(str(item.get('bezeichnung', ''))))
            self.zero_inventory_table.setItem(row, 3, QTableWidgetItem(str(item.get('lager_name', ''))))
            
            # Zeile rot einfärben
            for col in range(4):
                cell = self.zero_inventory_table.item(row, col)
                if cell:
                    cell.setBackground(QColor(255, 200, 200))
    
    def update_changes_table(self):
        """Aktualisiert die Änderungstabelle mit den letzten Änderungen."""
        try:
            # Aktuelle Daten und Vortag laden
            today = datetime.now()
            yesterday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday = yesterday.replace(day=yesterday.day - 1)
            
            current_data = self.inventory_tracker.retrieve_historical_data(today)
            previous_data = self.inventory_tracker.retrieve_historical_data(yesterday)
            
            # Tabelle leeren
            self.changes_table.setRowCount(0)
            
            if not current_data or not previous_data:
                return
            
            # Änderungen berechnen
            changes = self.report_generator._calculate_changes(current_data, previous_data)
            
            if not changes or 'significant_changes' not in changes:
                return
            
            # Daten hinzufügen
            for row, item in enumerate(changes['significant_changes']):
                self.changes_table.insertRow(row)
                
                # Zellen füllen
                self.changes_table.setItem(row, 0, QTableWidgetItem(str(item.get('artikelnummer', ''))))
                self.changes_table.setItem(row, 1, QTableWidgetItem(str(item.get('bezeichnung', ''))))
                self.changes_table.setItem(row, 2, QTableWidgetItem(str(item.get('bestand_previous', 0))))
                self.changes_table.setItem(row, 3, QTableWidgetItem(str(item.get('bestand_current', 0))))
                
                change = item.get('change', 0)
                change_item = QTableWidgetItem(str(change))
                
                # Farbe basierend auf Änderung
                if change > 0:
                    change_item.setBackground(QColor(200, 255, 200))  # Grün für Zunahme
                elif change < 0:
                    change_item.setBackground(QColor(255, 200, 200))  # Rot für Abnahme
                
                self.changes_table.setItem(row, 4, change_item)
                
                # Prozentuale Änderung
                change_percent = item.get('change_percent', 0)
                percent_item = QTableWidgetItem(f"{change_percent:.2f}%")
                
                if change_percent > 0:
                    percent_item.setBackground(QColor(200, 255, 200))
                elif change_percent < 0:
                    percent_item.setBackground(QColor(255, 200, 200))
                
                self.changes_table.setItem(row, 5, percent_item)
                
        except Exception as e:
            self.logger.log_error(f"Fehler beim Aktualisieren der Änderungstabelle: {str(e)}", exc_info=True)
    
    def update_status(self):
        """Aktualisiert die Statusanzeige."""
        # Datenbankverbindungsstatus prüfen
        connection_ok = self.db_manager.test_connection()
        
        if connection_ok:
            self.connection_label.setText("Datenbankverbindung: Aktiv")
            self.connection_label.setStyleSheet("color: green;")
        else:
            self.connection_label.setText("Datenbankverbindung: Inaktiv")
            self.connection_label.setStyleSheet("color: red;")
    
    def open_report_view(self):
        """Öffnet die Berichtsansicht."""
        try:
            report_view = ReportView(self.report_generator, self.config, self.logger, self)
            report_view.show()
            self.logger.log_info("Berichtsansicht geöffnet")
        except Exception as e:
            self.logger.log_error(f"Fehler beim Öffnen der Berichtsansicht: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler beim Öffnen der Berichtsansicht:\n{str(e)}")
    
    def open_settings(self):
        """Öffnet den Einstellungsdialog."""
        try:
            settings_dialog = SettingsDialog(self.config, self.db_manager, self.logger, self)
            if settings_dialog.exec_():
                # Konfiguration neu laden, wenn Änderungen gespeichert wurden
                self.config.load_config()
                
                # Aktualisierungsintervall aktualisieren
                new_interval = int(self.config.get_value('UI', 'refresh_interval', '300'))
                if new_interval != self.refresh_interval:
                    self.refresh_interval = new_interval
                    
                    if self.refresh_timer.isActive():
                        self.refresh_timer.stop()
                    
                    if self.refresh_interval > 0:
                        self.refresh_timer.start(self.refresh_interval * 1000)
                
                # Dashboard aktualisieren
                self.update_dashboard()
                
                self.logger.log_info("Einstellungen wurden aktualisiert")
        except Exception as e:
            self.logger.log_error(f"Fehler beim Öffnen der Einstellungen: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler beim Öffnen der Einstellungen:\n{str(e)}")
    
    def execute_task_now(self):
        """Führt die geplante Aufgabe sofort aus."""
        reply = QMessageBox.question(
            self, 
            "Aufgabe ausführen", 
            "Möchten Sie die Aufgabe jetzt ausführen?\n\nDies führt eine vollständige Datenbankabfrage durch.",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.statusBar.showMessage("Führe Aufgabe aus...")
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(10)
                QApplication.processEvents()
                
                # Ausführung in separatem Thread implementieren
                # Hier vereinfacht direkt ausgeführt
                success = self.task_scheduler.execute_task()
                
                self.progress_bar.setValue(100)
                
                if success:
                    self.statusBar.showMessage("Aufgabe erfolgreich ausgeführt", 3000)
                    self.update_dashboard()
                else:
                    self.statusBar.showMessage("Aufgabe konnte nicht erfolgreich ausgeführt werden", 5000)
                
            except Exception as e:
                self.logger.log_error(f"Fehler bei der Aufgabenausführung: {str(e)}", exc_info=True)
                self.statusBar.showMessage(f"Fehler bei der Aufgabenausführung: {str(e)}", 5000)
            
            finally:
                self.progress_bar.setVisible(False)
    
    def generate_daily_report(self):
        """Generiert einen täglichen Bericht."""
        try:
            report = self.report_generator.generate_daily_report()
            
            if report:
                QMessageBox.information(
                    self, 
                    "Bericht erstellt", 
                    f"Tagesbericht wurde erfolgreich erstellt:\n{self.config.get_value('Report', 'export_path', './reports')}"
                )
            else:
                QMessageBox.warning(self, "Bericht erstellen", "Es konnten keine Daten für den Bericht gefunden werden.")
        except Exception as e:
            self.logger.log_error(f"Fehler bei der Berichterstellung: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler bei der Berichterstellung:\n{str(e)}")
    
    def generate_trend_report(self):
        """Generiert einen Trendbericht."""
        try:
            report = self.report_generator.generate_trend_report()
            
            if report:
                QMessageBox.information(
                    self, 
                    "Bericht erstellt", 
                    f"Trendbericht wurde erfolgreich erstellt:\n{self.config.get_value('Report', 'export_path', './reports')}"
                )
            else:
                QMessageBox.warning(self, "Bericht erstellen", "Es konnten keine Daten für den Bericht gefunden werden.")
        except Exception as e:
            self.logger.log_error(f"Fehler bei der Berichterstellung: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler bei der Berichterstellung:\n{str(e)}")
    
    def export_data(self, format_type):
        """Exportiert die aktuellen Daten.
        
        Args:
            format_type (str): Exportformat ("csv", "excel", "pdf")
        """
        try:
            today = datetime.now()
            current_data = self.inventory_tracker.retrieve_historical_data(today)
            
            if not current_data:
                QMessageBox.warning(self, "Export", "Keine Daten zum Exportieren vorhanden.")
                return
            
            # Dateinamen generieren
            timestamp = today.strftime('%Y%m%d_%H%M%S')
            filename = f"export_{timestamp}"
            
            if format_type == "csv":
                filepath = self.report_generator.export_to_csv(current_data, f"{filename}.csv")
            elif format_type == "excel":
                filepath = self.report_generator.export_to_excel(current_data, f"{filename}.xlsx")
            elif format_type == "pdf":
                filepath = self.report_generator.export_to_pdf(current_data, f"{filename}.pdf")
            else:
                return
            
            if filepath:
                QMessageBox.information(
                    self, 
                    "Export erfolgreich", 
                    f"Daten wurden erfolgreich exportiert nach:\n{filepath}"
                )
            else:
                QMessageBox.warning(self, "Export", f"Export im Format {format_type} fehlgeschlagen.")
        
        except Exception as e:
            self.logger.log_error(f"Fehler beim Datenexport: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler beim Datenexport:\n{str(e)}")
    
    def show_about(self):
        """Zeigt den Über-Dialog an."""
        QMessageBox.about(
            self,
            "Über Artikel-Tracker",
            f"<h3>Artikel-Tracker</h3>"
            f"<p>Version 1.0</p>"
            f"<p>Eine Anwendung zur Verfolgung von Lagerbeständen und "
            f"Artikelstatusänderungen durch automatisierte Datenbankabfragen.</p>"
            f"<p>© 2023 Ihre Organisation</p>"
        )
    
    def handle_exit(self):
        """Behandelt das Beenden der Anwendung."""
        reply = QMessageBox.question(
            self, 
            "Beenden", 
            "Möchten Sie die Anwendung wirklich beenden?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Einstellungen speichern
            self.settings.setValue("mainwindow/size", self.size())
            self.settings.setValue("mainwindow/pos", self.pos())
            
            # Scheduler stoppen
            self.task_scheduler.stop_scheduler()
            
            self.logger.log_info("Anwendung wird beendet.")
            
            # Anwendung beenden
            QApplication.quit()
    
    def closeEvent(self, event):
        """Behandelt das Schließen des Fensters.
        
        Args:
            event (QCloseEvent): Schließereignis
        """
        # Einstellungen speichern
        self.settings.setValue("mainwindow/size", self.size())
        self.settings.setValue("mainwindow/pos", self.pos())
        
        # Scheduler stoppen
        self.task_scheduler.stop_scheduler()
        
        self.logger.log_info("Anwendung wird geschlossen.")
        
        # Event akzeptieren und Fenster schließen
        event.accept()
