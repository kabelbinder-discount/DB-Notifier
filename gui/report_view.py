#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Berichtsansicht für die Artikel-Tracking-Anwendung.
Ermöglicht die Anzeige und Analyse von Berichts- und Trenddaten.
"""

import os
import json
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                           QComboBox, QDateEdit, QLineEdit, QGroupBox, 
                           QFormLayout, QHeaderView, QSplitter, QMessageBox,
                           QAction, QMenu, QToolBar, QCheckBox, QFileDialog,
                           QTabWidget, QFrame, QSizePolicy, QSpinBox, QDialog)
from PyQt5.QtCore import Qt, QDate, QDateTime
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class ReportView(QMainWindow):
    """Klasse für die Berichtsvisualisierung."""
    
    def __init__(self, report_generator, config, logger, parent=None):
        """Initialisiert die Berichtsansicht.
        
        Args:
            report_generator (ReportGenerator): Report-Generator-Instanz
            config (ConfigManager): Konfigurationsmanager-Instanz
            logger (Logger): Logger-Instanz
            parent (QWidget, optional): Übergeordnetes Widget
        """
        super().__init__(parent)
        
        self.report_generator = report_generator
        self.config = config
        self.logger = logger
        
        # Current report data
        self.current_data = None
        self.trend_data = None
        
        # UI einrichten
        self.setup_ui()
        
        # Initialen Bericht laden
        self.load_report_data()
        
        self.logger.log_info("Berichtsansicht geöffnet")
    
    def setup_ui(self):
        """Richtet UI-Komponenten ein."""
        self.setWindowTitle("Berichtsansicht")
        self.setMinimumSize(900, 600)
        
        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Hauptlayout
        main_layout = QVBoxLayout(central_widget)
        
        # Filter- und Steuerungsbereich
        control_frame = QFrame()
        control_frame.setFrameShape(QFrame.StyledPanel)
        control_layout = QHBoxLayout(control_frame)
        
        # Datumswähler
        date_group = QGroupBox("Berichtsdatum")
        date_layout = QFormLayout(date_group)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        date_layout.addRow("Datum:", self.date_edit)
        
        self.load_button = QPushButton("Bericht laden")
        self.load_button.clicked.connect(self.load_report_data)
        date_layout.addRow(self.load_button)
        
        control_layout.addWidget(date_group)
        
        # Filtereinstellungen
        filter_group = QGroupBox("Filter")
        filter_layout = QFormLayout(filter_group)
        
        self.highlight_threshold_spin = QSpinBox()
        self.highlight_threshold_spin.setRange(1, 100)
        self.highlight_threshold_spin.setSuffix(" %")
        self.highlight_threshold_spin.setValue(int(self.config.get_value('Report', 'highlight_threshold', '10')))
        filter_layout.addRow("Hervorhebungsschwelle:", self.highlight_threshold_spin)
        
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Artikelsuche...")
        self.filter_edit.textChanged.connect(self.apply_filters)
        filter_layout.addRow("Artikelfilter:", self.filter_edit)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("Alle Kategorien")
        # Kategorien werden später geladen
        self.category_combo.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addRow("Kategorie:", self.category_combo)
        
        self.show_zero_check = QCheckBox("Nur Nullbestand anzeigen")
        self.show_zero_check.stateChanged.connect(self.apply_filters)
        filter_layout.addRow(self.show_zero_check)
        
        control_layout.addWidget(filter_group)
        
        # Export
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout(export_group)
        
        self.export_csv_button = QPushButton("Als CSV exportieren")
        self.export_csv_button.clicked.connect(lambda: self.export_report('csv'))
        export_layout.addWidget(self.export_csv_button)
        
        self.export_excel_button = QPushButton("Als Excel exportieren")
        self.export_excel_button.clicked.connect(lambda: self.export_report('excel'))
        export_layout.addWidget(self.export_excel_button)
        
        self.generate_trend_button = QPushButton("Trendbericht erstellen")
        self.generate_trend_button.clicked.connect(self.show_trend_report)
        export_layout.addWidget(self.generate_trend_button)
        
        control_layout.addWidget(export_group)
        
        main_layout.addWidget(control_frame)
        
        # Tabs für Berichte
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tabelle-Tab
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        
        self.report_table = QTableWidget()
        self.report_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.report_table)
        
        self.tabs.addTab(table_widget, "Tabelle")
        
        # Änderungen-Tab
        changes_widget = QWidget()
        changes_layout = QVBoxLayout(changes_widget)
        
        self.changes_table = QTableWidget()
        self.changes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.changes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        changes_layout.addWidget(self.changes_table)
        
        self.tabs.addTab(changes_widget, "Bestandsänderungen")
        
        # Deaktivierungen-Tab
        deactivations_widget = QWidget()
        deactivations_layout = QVBoxLayout(deactivations_widget)
        
        self.deactivations_table = QTableWidget()
        self.deactivations_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.deactivations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        deactivations_layout.addWidget(self.deactivations_table)
        
        self.tabs.addTab(deactivations_widget, "Deaktivierungen")
        
        # Diagramm-Tab
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        chart_layout.addWidget(self.toolbar)
        chart_layout.addWidget(self.canvas)
        
        self.tabs.addTab(chart_widget, "Diagramm")
        
        # Menü erstellen
        self.create_menu()
        
        # Statusleiste
        self.statusBar().showMessage("Bereit")
    
    def create_menu(self):
        """Erstellt die Menüstruktur."""
        # Datei-Menü
        file_menu = self.menuBar().addMenu("Datei")
        
        load_action = QAction("Bericht laden", self)
        load_action.triggered.connect(self.load_report_data)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        export_csv_action = QAction("Als CSV exportieren", self)
        export_csv_action.triggered.connect(lambda: self.export_report('csv'))
        file_menu.addAction(export_csv_action)
        
        export_excel_action = QAction("Als Excel exportieren", self)
        export_excel_action.triggered.connect(lambda: self.export_report('excel'))
        file_menu.addAction(export_excel_action)
        
        file_menu.addSeparator()
        
        close_action = QAction("Schließen", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        # Ansicht-Menü
        view_menu = self.menuBar().addMenu("Ansicht")
        
        refresh_action = QAction("Aktualisieren", self)
        refresh_action.triggered.connect(self.load_report_data)
        view_menu.addAction(refresh_action)
        
        apply_filters_action = QAction("Filter anwenden", self)
        apply_filters_action.triggered.connect(self.apply_filters)
        view_menu.addAction(apply_filters_action)
        
        view_menu.addSeparator()
        
        reset_filters_action = QAction("Filter zurücksetzen", self)
        reset_filters_action.triggered.connect(self.reset_filters)
        view_menu.addAction(reset_filters_action)
        
        # Berichte-Menü
        reports_menu = self.menuBar().addMenu("Berichte")
        
        daily_report_action = QAction("Tagesbericht", self)
        daily_report_action.triggered.connect(self.load_report_data)
        reports_menu.addAction(daily_report_action)
        
        trend_report_action = QAction("Trendbericht anzeigen", self)
        trend_report_action.triggered.connect(self.show_trend_report)
        reports_menu.addAction(trend_report_action)
    
    def load_report_data(self):
        """Lädt Berichtsdaten."""
        self.logger.log_info("Lade Berichtsdaten...")
        
        try:
            # Ausgewähltes Datum holen
            selected_date = self.date_edit.date().toPyDate()
            
            # Prüfen, ob bereits ein Bericht existiert oder einen generieren
            report = self.report_generator.generate_daily_report(selected_date)
            
            if not report:
                self.statusBar().showMessage(f"Keine Daten für {selected_date.strftime('%d.%m.%Y')} gefunden")
                return
            
            self.current_data = report
            
            # Kategorien für Filter laden
            self.load_categories()
            
            # Tabellen aktualisieren
            self.update_tables()
            
            # Diagramm aktualisieren
            self.update_chart()
            
            self.statusBar().showMessage(f"Bericht für {selected_date.strftime('%d.%m.%Y')} geladen")
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Laden der Berichtsdaten: {str(e)}", exc_info=True)
            self.statusBar().showMessage(f"Fehler: {str(e)}")
    
    def load_categories(self):
        """Lädt Kategorien für Filter."""
        if not self.current_data:
            return
        
        try:
            # Daten für den aktuellen Tag abrufen
            today = datetime.now()
            inventory_data = self.report_generator.inventory_tracker.retrieve_historical_data(today)
            
            if not inventory_data:
                return
            
            # Alle Kategorien sammeln
            categories = set()
            for item in inventory_data:
                category = item.get('kategorie')
                if category:
                    categories.add(category)
            
            # ComboBox aktualisieren
            current_text = self.category_combo.currentText()
            self.category_combo.clear()
            self.category_combo.addItem("Alle Kategorien")
            
            for category in sorted(categories):
                self.category_combo.addItem(category)
            
            # Text wiederherstellen, falls vorhanden
            index = self.category_combo.findText(current_text)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
                
        except Exception as e:
            self.logger.log_error(f"Fehler beim Laden der Kategorien: {str(e)}", exc_info=True)
    
    def update_tables(self):
        """Aktualisiert alle Tabellen mit den aktuellen Berichtsdaten."""
        if not self.current_data:
            return
        
        try:
            # Haupttabelle aktualisieren
            self.update_main_table()
            
            # Änderungstabelle aktualisieren
            self.update_changes_table()
            
            # Deaktivierungstabelle aktualisieren
            self.update_deactivations_table()
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Aktualisieren der Tabellen: {str(e)}", exc_info=True)
    
    def update_main_table(self):
        """Aktualisiert die Haupttabelle mit Artikeldaten."""
        if not self.current_data or 'zero_inventory' not in self.current_data:
            return
        
        # Filter anwenden
        filtered_data = self.apply_filters_to_data(self.current_data['zero_inventory'])
        
        # Tabelle vorbereiten
        self.report_table.clear()
        self.report_table.setRowCount(0)
        self.report_table.setColumnCount(5)
        self.report_table.setHorizontalHeaderLabels(
            ["Artikel-ID", "Artikelnummer", "Bezeichnung", "Lager", "Bestand"]
        )
        
        # Daten einfügen
        for row, item in enumerate(filtered_data):
            self.report_table.insertRow(row)
            
            self.report_table.setItem(row, 0, QTableWidgetItem(str(item.get('artikel_id', ''))))
            self.report_table.setItem(row, 1, QTableWidgetItem(str(item.get('artikelnummer', ''))))
            self.report_table.setItem(row, 2, QTableWidgetItem(str(item.get('bezeichnung', ''))))
            self.report_table.setItem(row, 3, QTableWidgetItem(str(item.get('lager_name', ''))))
            
            # Bestandszelle mit Nullbestand rot einfärben
            bestand_item = QTableWidgetItem(str(item.get('bestand', 0)))
            if item.get('bestand', 0) == 0:
                bestand_item.setBackground(QColor(255, 200, 200))
            
            self.report_table.setItem(row, 4, bestand_item)
    
    def update_changes_table(self):
        """Aktualisiert die Änderungstabelle."""
        if not self.current_data or 'changes' not in self.current_data or 'significant_changes' not in self.current_data['changes']:
            # Tab deaktivieren, wenn keine Daten vorhanden
            self.tabs.setTabEnabled(1, False)
            return
        
        self.tabs.setTabEnabled(1, True)
        
        # Filter anwenden
        filtered_data = self.apply_filters_to_data(self.current_data['changes']['significant_changes'])
        
        # Tabelle vorbereiten
        self.changes_table.clear()
        self.changes_table.setRowCount(0)
        self.changes_table.setColumnCount(6)
        self.changes_table.setHorizontalHeaderLabels(
            ["Artikelnummer", "Bezeichnung", "Alter Bestand", "Neuer Bestand", "Änderung", "Änderung (%)"]
        )
        
        # Daten einfügen
        for row, item in enumerate(filtered_data):
            self.changes_table.insertRow(row)
            
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
    
    def update_deactivations_table(self):
        """Aktualisiert die Deaktivierungstabelle."""
        if not self.current_data or 'deactivations' not in self.current_data or not self.current_data['deactivations']:
            # Tab deaktivieren, wenn keine Daten vorhanden
            self.tabs.setTabEnabled(2, False)
            return
        
        self.tabs.setTabEnabled(2, True)
        
        # Filter anwenden
        filtered_data = self.apply_filters_to_data(self.current_data['deactivations'])
        
        # Tabelle vorbereiten
        self.deactivations_table.clear()
        self.deactivations_table.setRowCount(0)
        self.deactivations_table.setColumnCount(3)
        self.deactivations_table.setHorizontalHeaderLabels(
            ["Artikel-ID", "Artikelnummer", "Bezeichnung"]
        )
        
        # Daten einfügen
        for row, item in enumerate(filtered_data):
            self.deactivations_table.insertRow(row)
            
            self.deactivations_table.setItem(row, 0, QTableWidgetItem(str(item.get('artikel_id', ''))))
            self.deactivations_table.setItem(row, 1, QTableWidgetItem(str(item.get('artikelnummer', ''))))
            self.deactivations_table.setItem(row, 2, QTableWidgetItem(str(item.get('bezeichnung', ''))))
            
            # Alle Zellen rot einfärben
            for col in range(3):
                cell = self.deactivations_table.item(row, col)
                if cell:
                    cell.setBackground(QColor(255, 200, 200))
    
    def update_chart(self):
        """Aktualisiert das Diagramm."""
        if not self.current_data:
            return
        
        try:
            # Figur leeren
            self.figure.clear()
            
            # Verteilung der Lagerbestände
            if 'zero_inventory' in self.current_data:
                # Aktuelle Bestandsdaten laden
                today = datetime.now()
                inventory_data = self.report_generator.inventory_tracker.retrieve_historical_data(today)
                
                if inventory_data:
                    ax = self.figure.add_subplot(111)
                    
                    # Bestand nach Kategorien gruppieren
                    categories = {}
                    
                    for item in inventory_data:
                        category = item.get('kategorie', 'Unbekannt')
                        if category not in categories:
                            categories[category] = []
                        categories[category].append(item.get('bestand', 0))
                    
                    # Boxplot für jede Kategorie
                    data = []
                    labels = []
                    for category, stocks in categories.items():
                        if stocks:  # Nur hinzufügen, wenn Daten vorhanden
                            data.append(stocks)
                            labels.append(category)
                    
                    # Boxplot erstellen
                    if data:
                        ax.boxplot(data, labels=labels)
                        ax.set_title('Bestandsverteilung nach Kategorie')
                        ax.set_ylabel('Bestand')
                        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                        self.figure.tight_layout()
            
            # Canvas aktualisieren
            self.canvas.draw()
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Aktualisieren des Diagramms: {str(e)}", exc_info=True)
    
    def apply_filters(self):
        """Wendet Filter auf Berichtsdaten an."""
        if not self.current_data:
            return
        
        try:
            # Threshold aktualisieren
            threshold = self.highlight_threshold_spin.value()
            
            # Alle Tabellen aktualisieren
            self.update_tables()
            
            # Benachrichtigung
            self.statusBar().showMessage("Filter angewendet", 3000)
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Anwenden der Filter: {str(e)}", exc_info=True)
    
    def apply_filters_to_data(self, data):
        """Wendet Filter auf Datensatz an.
        
        Args:
            data (list): Zu filternde Daten
            
        Returns:
            list: Gefilterte Daten
        """
        if not data:
            return []
        
        filtered_data = data.copy()
        
        # Textfilter
        filter_text = self.filter_edit.text().lower()
        if filter_text:
            filtered_data = [
                item for item in filtered_data
                if (filter_text in str(item.get('artikelnummer', '')).lower() or
                    filter_text in str(item.get('bezeichnung', '')).lower())
            ]
        
        # Kategoriefilter
        selected_category = self.category_combo.currentText()
        if selected_category != "Alle Kategorien":
            filtered_data = [
                item for item in filtered_data
                if item.get('kategorie') == selected_category
            ]
        
        # Nullbestand-Filter
        if self.show_zero_check.isChecked():
            filtered_data = [
                item for item in filtered_data
                if item.get('bestand', 0) == 0
            ]
        
        return filtered_data
    
    def reset_filters(self):
        """Setzt alle Filter zurück."""
        self.filter_edit.clear()
        self.category_combo.setCurrentIndex(0)
        self.show_zero_check.setChecked(False)
        self.highlight_threshold_spin.setValue(int(self.config.get_value('Report', 'highlight_threshold', '10')))
        
        # Filter anwenden
        self.apply_filters()
    
    def highlight_changes(self):
        """Hebt signifikante Änderungen hervor."""
        # Diese Methode passt die Schwellwerte für Hervorhebungen an
        threshold = self.highlight_threshold_spin.value()
        
        # Änderungen in den Tabellen hervorheben
        self.update_tables()
    
    def export_report(self, format_type):
        """Exportiert Bericht in Datei.
        
        Args:
            format_type (str): Exportformat ("csv", "excel", "pdf")
        """
        if not self.current_data:
            QMessageBox.warning(self, "Export", "Keine Daten zum Exportieren vorhanden")
            return
        
        try:
            # Dateinamen generieren
            date_str = self.date_edit.date().toString('yyyyMMdd')
            filename = f"bericht_{date_str}"
            
            # Daten exportieren
            if format_type == 'csv':
                filepath = self.report_generator.export_to_csv(self.current_data, f"{filename}.csv")
            elif format_type == 'excel':
                filepath = self.report_generator.export_to_excel(self.current_data, f"{filename}.xlsx")
            elif format_type == 'pdf':
                filepath = self.report_generator.export_to_pdf(self.current_data, f"{filename}.pdf")
            else:
                self.statusBar().showMessage(f"Unbekanntes Exportformat: {format_type}")
                return
            
            if filepath:
                self.statusBar().showMessage(f"Bericht exportiert nach: {filepath}")
                QMessageBox.information(self, "Export", f"Bericht wurde exportiert nach:\n{filepath}")
            else:
                self.statusBar().showMessage("Export fehlgeschlagen")
                QMessageBox.warning(self, "Export", "Der Export ist fehlgeschlagen")
                
        except Exception as e:
            self.logger.log_error(f"Fehler beim Exportieren des Berichts: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler beim Exportieren des Berichts:\n{str(e)}")
    
    def show_trend_report(self):
        """Zeigt den Trendbericht an."""
        try:
            # Dialog zur Auswahl des Zeitraums anzeigen
            dialog = TrendReportDialog(self)
            if dialog.exec_() != QDialog.Accepted:
                return
            
            start_date = dialog.start_date_edit.date().toPyDate()
            end_date = dialog.end_date_edit.date().toPyDate()
            selected_category = dialog.category_combo.currentText()
            
            category = None if selected_category == "Alle Kategorien" else selected_category
            
            # Trendbericht generieren
            self.statusBar().showMessage("Generiere Trendbericht...")
            trend_report = self.report_generator.generate_trend_report(start_date, end_date, category)
            
            if not trend_report:
                self.statusBar().showMessage("Keine Daten für Trendbericht gefunden")
                QMessageBox.warning(self, "Trendbericht", "Es konnten keine Daten für den Trendbericht gefunden werden.")
                return
            
            self.trend_data = trend_report
            
            # Trendbericht in neuem Fenster anzeigen
            trend_view = TrendReportView(trend_report, self.logger, self)
            trend_view.show()
            
            self.statusBar().showMessage("Trendbericht generiert")
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Anzeigen des Trendberichts: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler beim Anzeigen des Trendberichts:\n{str(e)}")


class TrendReportDialog(QDialog):
    """Dialog zur Auswahl des Zeitraums für den Trendbericht."""
    
    def __init__(self, parent=None):
        """Initialisiert den Dialog.
        
        Args:
            parent (QWidget, optional): Übergeordnetes Widget
        """
        super().__init__(parent)
        
        self.setWindowTitle("Trendbericht erstellen")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Zeitraum-Gruppe
        period_group = QGroupBox("Zeitraum")
        period_layout = QFormLayout(period_group)
        
        # Startdatum - standardmäßig 30 Tage zurück
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        period_layout.addRow("Startdatum:", self.start_date_edit)
        
        # Enddatum - standardmäßig heute
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        period_layout.addRow("Enddatum:", self.end_date_edit)
        
        layout.addWidget(period_group)
        
        # Filter-Gruppe
        filter_group = QGroupBox("Filter")
        filter_layout = QFormLayout(filter_group)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("Alle Kategorien")
        # Hier könnten Kategorien hinzugefügt werden
        filter_layout.addRow("Kategorie:", self.category_combo)
        
        layout.addWidget(filter_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)


class TrendReportView(QMainWindow):
    """Fenster zur Anzeige des Trendberichts."""
    
    def __init__(self, trend_data, logger, parent=None):
        """Initialisiert das Fenster.
        
        Args:
            trend_data (dict): Trenddaten
            logger (Logger): Logger-Instanz
            parent (QWidget, optional): Übergeordnetes Widget
        """
        super().__init__(parent)
        
        self.trend_data = trend_data
        self.logger = logger
        
        # UI einrichten
        self.setup_ui()
        
        # Daten anzeigen
        self.display_trend_data()
        
        self.logger.log_info("Trendbericht-Ansicht geöffnet")
    
    def setup_ui(self):
        """Richtet UI-Komponenten ein."""
        self.setWindowTitle("Trendbericht")
        self.setMinimumSize(800, 600)
        
        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Hauptlayout
        main_layout = QVBoxLayout(central_widget)
        
        # Info-Bereich
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_layout = QFormLayout(info_frame)
        
        self.period_label = QLabel()
        info_layout.addRow("Zeitraum:", self.period_label)
        
        self.summary_label = QLabel()
        info_layout.addRow("Zusammenfassung:", self.summary_label)
        
        main_layout.addWidget(info_frame)
        
        # Tabs für verschiedene Ansichten
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Zusammenfassung-Tab
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        
        self.summary_table = QTableWidget()
        self.summary_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        summary_layout.addWidget(self.summary_table)
        
        self.tabs.addTab(summary_widget, "Zusammenfassung")
        
        # Diagramm-Tab
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        chart_layout.addWidget(self.toolbar)
        chart_layout.addWidget(self.canvas)
        
        self.tabs.addTab(chart_widget, "Diagramm")
        
        # Export-Button
        export_button = QPushButton("Exportieren")
        export_button.clicked.connect(self.export_trend_report)
        main_layout.addWidget(export_button)
    
    def display_trend_data(self):
        """Zeigt Trenddaten an."""
        if not self.trend_data:
            return
        
        try:
            # Info-Bereich aktualisieren
            self.period_label.setText(
                f"{self.trend_data.get('start_date', '')} bis {self.trend_data.get('end_date', '')}"
            )
            
            summary = self.trend_data.get('summary', {})
            trend = summary.get('trend', 'stable')
            
            trend_text = "Stabil"
            if trend == 'increasing':
                trend_text = "Steigend"
            elif trend == 'decreasing':
                trend_text = "Fallend"
            
            self.summary_label.setText(
                f"Trend: {trend_text}, Ø Artikel pro Tag: {summary.get('avg_articles_per_day', 0):.2f}"
            )
            
            # Zusammenfassungstabelle aktualisieren
            self.update_summary_table()
            
            # Diagramm aktualisieren
            self.update_trend_chart()
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Anzeigen der Trenddaten: {str(e)}", exc_info=True)
    
    def update_summary_table(self):
        """Aktualisiert die Zusammenfassungstabelle."""
        if not self.trend_data or 'summary' not in self.trend_data:
            return
        
        summary = self.trend_data.get('summary', {})
        dates = summary.get('dates', [])
        
        if not dates:
            return
        
        # Tabelle vorbereiten
        self.summary_table.clear()
        self.summary_table.setRowCount(len(dates))
        self.summary_table.setColumnCount(3)
        self.summary_table.setHorizontalHeaderLabels(
            ["Datum", "Aktive Artikel", "Nullbestand"]
        )
        
        # Daten einfügen
        active_articles = summary.get('active_articles', {})
        zero_inventory = summary.get('zero_inventory', {})
        
        for row, date in enumerate(dates):
            self.summary_table.setItem(row, 0, QTableWidgetItem(date))
            
            active_item = QTableWidgetItem(str(active_articles.get(date, 0)))
            self.summary_table.setItem(row, 1, active_item)
            
            zero_item = QTableWidgetItem(str(zero_inventory.get(date, 0)))
            self.summary_table.setItem(row, 2, zero_item)
    
    def update_trend_chart(self):
        """Aktualisiert das Trenddiagramm."""
        if not self.trend_data or 'summary' not in self.trend_data:
            return
        
        try:
            # Figur leeren
            self.figure.clear()
            
            summary = self.trend_data.get('summary', {})
            dates = summary.get('dates', [])
            
            if not dates:
                return
            
            # Aktive Artikel und Nullbestand plotten
            active_articles = summary.get('active_articles', {})
            zero_inventory = summary.get('zero_inventory', {})
            
            ax = self.figure.add_subplot(111)
            
            # Daten in Listen umwandeln
            x = range(len(dates))
            y1 = [active_articles.get(date, 0) for date in dates]
            y2 = [zero_inventory.get(date, 0) for date in dates]
            
            # Plots erstellen
            ax.plot(x, y1, 'b-', label='Aktive Artikel')
            ax.plot(x, y2, 'r-', label='Nullbestand')
            
            # Achsenbeschriftungen
            ax.set_xlabel('Datum')
            ax.set_ylabel('Anzahl')
            ax.set_title('Artikeländerungen im Zeitverlauf')
            
            # X-Achsen-Labels anpassen
            ax.set_xticks(x)
            ax.set_xticklabels(dates, rotation=45, ha='right')
            
            # Legende
            ax.legend()
            
            # Layout anpassen
            self.figure.tight_layout()
            
            # Canvas aktualisieren
            self.canvas.draw()
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Aktualisieren des Trenddiagramms: {str(e)}", exc_info=True)
    
    def export_trend_report(self):
        """Exportiert den Trendbericht."""
        if not self.trend_data:
            return
        
        try:
            # Exportformat auswählen
            format_dialog = QDialog(self)
            format_dialog.setWindowTitle("Exportformat wählen")
            format_layout = QVBoxLayout(format_dialog)
            
            format_label = QLabel("Wählen Sie das Exportformat:")
            format_layout.addWidget(format_label)
            
            csv_button = QPushButton("CSV")
            csv_button.clicked.connect(lambda: self.do_export("csv", format_dialog))
            format_layout.addWidget(csv_button)
            
            excel_button = QPushButton("Excel")
            excel_button.clicked.connect(lambda: self.do_export("excel", format_dialog))
            format_layout.addWidget(excel_button)
            
            cancel_button = QPushButton("Abbrechen")
            cancel_button.clicked.connect(format_dialog.reject)
            format_layout.addWidget(cancel_button)
            
            format_dialog.exec_()
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Exportieren des Trendberichts: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler beim Exportieren des Trendberichts:\n{str(e)}")
    
    def do_export(self, format_type, dialog):
        """Führt den Export durch.
        
        Args:
            format_type (str): Exportformat
            dialog (QDialog): Formatdialog zum Schließen
        """
        try:
            dialog.accept()
            
            # Dateinamen generieren
            filename = f"trendbericht_{self.trend_data.get('start_date', '')}_bis_{self.trend_data.get('end_date', '')}"
            
            # Zieldatei auswählen
            if format_type == "csv":
                filepath, _ = QFileDialog.getSaveFileName(
                    self, "CSV-Datei speichern", filename, "CSV-Dateien (*.csv)"
                )
                if not filepath:
                    return
                
                # Daten in CSV exportieren
                with open(filepath, 'w', encoding='utf-8') as f:
                    # Header
                    f.write("Datum,Aktive Artikel,Nullbestand\n")
                    
                    # Daten
                    summary = self.trend_data.get('summary', {})
                    dates = summary.get('dates', [])
                    active_articles = summary.get('active_articles', {})
                    zero_inventory = summary.get('zero_inventory', {})
                    
                    for date in dates:
                        f.write(f"{date},{active_articles.get(date, 0)},{zero_inventory.get(date, 0)}\n")
            
            elif format_type == "excel":
                filepath, _ = QFileDialog.getSaveFileName(
                    self, "Excel-Datei speichern", filename, "Excel-Dateien (*.xlsx)"
                )
                if not filepath:
                    return
                
                # Daten in Excel exportieren
                try:
                    import pandas as pd
                    
                    # Daten vorbereiten
                    summary = self.trend_data.get('summary', {})
                    dates = summary.get('dates', [])
                    active_articles = summary.get('active_articles', {})
                    zero_inventory = summary.get('zero_inventory', {})
                    
                    data = []
                    for date in dates:
                        data.append({
                            'Datum': date,
                            'Aktive Artikel': active_articles.get(date, 0),
                            'Nullbestand': zero_inventory.get(date, 0)
                        })
                    
                    df = pd.DataFrame(data)
                    df.to_excel(filepath, index=False)
                    
                except ImportError:
                    QMessageBox.warning(self, "Export", "Pandas ist nicht installiert. Excel-Export nicht möglich.")
                    return
            
            QMessageBox.information(self, "Export", f"Trendbericht wurde exportiert nach:\n{filepath}")
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Exportieren: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler beim Exportieren:\n{str(e)}")
