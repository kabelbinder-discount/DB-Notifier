#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Einstellungsdialog für die Artikel-Tracking-Anwendung.
Ermöglicht die Konfiguration von Datenbankverbindungen, Scheduler und Anwendungseinstellungen.
"""

import os
from PyQt5.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTabWidget, QLabel, QLineEdit, QPushButton, 
                           QComboBox, QSpinBox, QTimeEdit, QCheckBox,
                           QFormLayout, QGroupBox, QMessageBox, QFileDialog,
                           QDialogButtonBox, QSizePolicy)
from PyQt5.QtCore import Qt, QTime, QRegExp
from PyQt5.QtGui import QRegExpValidator


class SettingsDialog(QDialog):
    """Einstellungsdialogsklasse."""
    
    def __init__(self, config, db_manager, logger, parent=None):
        """Initialisiert den Dialog.
        
        Args:
            config (ConfigManager): Konfigurationsmanager-Instanz
            db_manager (DatabaseManager): Datenbank-Manager-Instanz
            logger (Logger): Logger-Instanz
            parent (QWidget, optional): Übergeordnetes Widget
        """
        super().__init__(parent)
        
        self.config = config
        self.db_manager = db_manager
        self.logger = logger
        
        # UI einrichten
        self.setup_ui()
        
        # Aktuelle Einstellungen laden
        self.load_current_settings()
        
        self.logger.log_info("Einstellungsdialog initialisiert")
    
    def setup_ui(self):
        """Richtet UI-Komponenten ein."""
        self.setWindowTitle("Einstellungen")
        self.setMinimumWidth(500)
        
        # Hauptlayout
        main_layout = QVBoxLayout(self)
        
        # Tabs für verschiedene Einstellungskategorien
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Datenbankeinstellungen-Tab
        db_tab = QWidget()
        self.tabs.addTab(db_tab, "Datenbank")
        self.setup_database_tab(db_tab)
        
        # Scheduler-Einstellungen-Tab
        scheduler_tab = QWidget()
        self.tabs.addTab(scheduler_tab, "Scheduler")
        self.setup_scheduler_tab(scheduler_tab)
        
        # Berichtseinstellungen-Tab
        report_tab = QWidget()
        self.tabs.addTab(report_tab, "Berichte")
        self.setup_report_tab(report_tab)
        
        # UI-Einstellungen-Tab
        ui_tab = QWidget()
        self.tabs.addTab(ui_tab, "Benutzeroberfläche")
        self.setup_ui_tab(ui_tab)
        
        # Logging-Einstellungen-Tab
        logging_tab = QWidget()
        self.tabs.addTab(logging_tab, "Logging")
        self.setup_logging_tab(logging_tab)
        
        # Buttons am unteren Rand
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply | QDialogButtonBox.Reset)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        button_box.button(QDialogButtonBox.Reset).clicked.connect(self.reset_defaults)
        
        main_layout.addWidget(button_box)
    
    def setup_database_tab(self, tab):
        """Richtet die UI-Komponenten für den Datenbank-Tab ein.
        
        Args:
            tab (QWidget): Tab-Widget
        """
        layout = QVBoxLayout(tab)
        
        # Datenbanktyp
        db_type_group = QGroupBox("Datenbanktyp")
        db_type_layout = QFormLayout(db_type_group)
        
        self.db_type_combo = QComboBox()
        self.db_type_combo.addItems(["MySQL", "MSSQL"])
        db_type_layout.addRow("Typ:", self.db_type_combo)
        
        layout.addWidget(db_type_group)
        
        # Verbindungsdetails
        connection_group = QGroupBox("Verbindungsdetails")
        connection_layout = QFormLayout(connection_group)
        
        self.host_edit = QLineEdit()
        connection_layout.addRow("Host:", self.host_edit)
        
        # Port muss eine Zahl sein
        self.port_edit = QLineEdit()
        self.port_edit.setValidator(QRegExpValidator(QRegExp("\\d+")))
        connection_layout.addRow("Port:", self.port_edit)
        
        self.username_edit = QLineEdit()
        connection_layout.addRow("Benutzername:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        connection_layout.addRow("Passwort:", self.password_edit)
        
        self.database_edit = QLineEdit()
        connection_layout.addRow("Datenbank:", self.database_edit)
        
        layout.addWidget(connection_group)
        
        # Erweiterte Einstellungen
        advanced_group = QGroupBox("Erweiterte Einstellungen")
        advanced_layout = QFormLayout(advanced_group)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setSuffix(" Sekunden")
        advanced_layout.addRow("Verbindungs-Timeout:", self.timeout_spin)
        
        self.max_connections_spin = QSpinBox()
        self.max_connections_spin.setRange(1, 50)
        advanced_layout.addRow("Max. Verbindungen:", self.max_connections_spin)
        
        layout.addWidget(advanced_group)
        
        # Test-Button
        test_button = QPushButton("Verbindung testen")
        test_button.clicked.connect(self.test_connection)
        layout.addWidget(test_button)
        
        layout.addStretch()
    
    def setup_scheduler_tab(self, tab):
        """Richtet die UI-Komponenten für den Scheduler-Tab ein.
        
        Args:
            tab (QWidget): Tab-Widget
        """
        layout = QVBoxLayout(tab)
        
        # Zeitplaneinstellungen
        time_group = QGroupBox("Zeitplaneinstellungen")
        time_layout = QFormLayout(time_group)
        
        self.query_time_edit = QTimeEdit()
        self.query_time_edit.setDisplayFormat("HH:mm")
        time_layout.addRow("Tägliche Abfragezeit:", self.query_time_edit)
        
        layout.addWidget(time_group)
        
        # Fehlerbehandlung
        error_group = QGroupBox("Fehlerbehandlung")
        error_layout = QFormLayout(error_group)
        
        self.retry_attempts_spin = QSpinBox()
        self.retry_attempts_spin.setRange(0, 10)
        error_layout.addRow("Wiederholungsversuche:", self.retry_attempts_spin)
        
        self.retry_interval_spin = QSpinBox()
        self.retry_interval_spin.setRange(1, 120)
        self.retry_interval_spin.setSuffix(" Minuten")
        error_layout.addRow("Wiederholungsintervall:", self.retry_interval_spin)
        
        layout.addWidget(error_group)
        
        # Datenaufbewahrung
        data_group = QGroupBox("Datenaufbewahrung")
        data_layout = QFormLayout(data_group)
        
        self.max_data_age_spin = QSpinBox()
        self.max_data_age_spin.setRange(7, 365)
        self.max_data_age_spin.setSuffix(" Tage")
        data_layout.addRow("Maximales Datenalter:", self.max_data_age_spin)
        
        layout.addWidget(data_group)
        
        layout.addStretch()
    
    def setup_report_tab(self, tab):
        """Richtet die UI-Komponenten für den Bericht-Tab ein.
        
        Args:
            tab (QWidget): Tab-Widget
        """
        layout = QVBoxLayout(tab)
        
        # Berichtseinstellungen
        report_group = QGroupBox("Berichtseinstellungen")
        report_layout = QFormLayout(report_group)
        
        self.highlight_threshold_spin = QSpinBox()
        self.highlight_threshold_spin.setRange(1, 100)
        self.highlight_threshold_spin.setSuffix(" %")
        report_layout.addRow("Hervorhebungsschwelle:", self.highlight_threshold_spin)
        
        self.history_days_spin = QSpinBox()
        self.history_days_spin.setRange(1, 365)
        self.history_days_spin.setSuffix(" Tage")
        report_layout.addRow("Historische Daten:", self.history_days_spin)
        
        layout.addWidget(report_group)
        
        # Exporteinstellungen
        export_group = QGroupBox("Exporteinstellungen")
        export_layout = QFormLayout(export_group)
        
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["CSV", "Excel", "PDF"])
        export_layout.addRow("Standard-Exportformat:", self.export_format_combo)
        
        self.export_path_edit = QLineEdit()
        self.export_path_edit.setReadOnly(True)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.export_path_edit)
        
        browse_button = QPushButton("...")
        browse_button.setMaximumWidth(30)
        browse_button.clicked.connect(self.browse_export_path)
        path_layout.addWidget(browse_button)
        
        export_layout.addRow("Exportpfad:", path_layout)
        
        layout.addWidget(export_group)
        
        layout.addStretch()
    
    def setup_ui_tab(self, tab):
        """Richtet die UI-Komponenten für den UI-Tab ein.
        
        Args:
            tab (QWidget): Tab-Widget
        """
        layout = QVBoxLayout(tab)
        
        # Thema
        theme_group = QGroupBox("Aussehen")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Hell", "Dunkel"])
        theme_layout.addRow("Thema:", self.theme_combo)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Deutsch", "Englisch"])
        theme_layout.addRow("Sprache:", self.language_combo)
        
        layout.addWidget(theme_group)
        
        # Verhalten
        behavior_group = QGroupBox("Verhalten")
        behavior_layout = QFormLayout(behavior_group)
        
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(0, 3600)
        self.refresh_interval_spin.setSuffix(" Sekunden")
        self.refresh_interval_spin.setSpecialValueText("Nie")
        behavior_layout.addRow("Aktualisierungsintervall:", self.refresh_interval_spin)
        
        layout.addWidget(behavior_group)
        
        layout.addStretch()
    
    def setup_logging_tab(self, tab):
        """Richtet die UI-Komponenten für den Logging-Tab ein.
        
        Args:
            tab (QWidget): Tab-Widget
        """
        layout = QVBoxLayout(tab)
        
        # Logging-Einstellungen
        log_group = QGroupBox("Logging-Einstellungen")
        log_layout = QFormLayout(log_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        log_layout.addRow("Log-Level:", self.log_level_combo)
        
        self.log_path_edit = QLineEdit()
        self.log_path_edit.setReadOnly(True)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.log_path_edit)
        
        browse_button = QPushButton("...")
        browse_button.setMaximumWidth(30)
        browse_button.clicked.connect(self.browse_log_path)
        path_layout.addWidget(browse_button)
        
        log_layout.addRow("Log-Pfad:", path_layout)
        
        layout.addWidget(log_group)
        
        # Rotation
        rotation_group = QGroupBox("Log-Rotation")
        rotation_layout = QFormLayout(rotation_group)
        
        self.max_log_size_spin = QSpinBox()
        self.max_log_size_spin.setRange(1, 100)
        self.max_log_size_spin.setSuffix(" MB")
        rotation_layout.addRow("Maximale Log-Größe:", self.max_log_size_spin)
        
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setRange(1, 20)
        rotation_layout.addRow("Anzahl Backups:", self.backup_count_spin)
        
        layout.addWidget(rotation_group)
        
        # Öffnen-Button
        open_log_button = QPushButton("Log-Dateien öffnen")
        open_log_button.clicked.connect(self.open_log_directory)
        layout.addWidget(open_log_button)
        
        layout.addStretch()
    
    def load_current_settings(self):
        """Lädt aktuelle Einstellungen."""
        try:
            # Datenbankeinstellungen
            db_type = self.config.get_value('Database', 'type', 'mysql').lower()
            if db_type == 'mysql':
                self.db_type_combo.setCurrentIndex(0)
            else:
                self.db_type_combo.setCurrentIndex(1)
            
            self.host_edit.setText(self.config.get_value('Database', 'host', 'localhost'))
            self.port_edit.setText(self.config.get_value('Database', 'port', '3306'))
            self.username_edit.setText(self.config.get_value('Database', 'username', ''))
            self.password_edit.setText(self.config.get_value('Database', 'password', ''))
            self.database_edit.setText(self.config.get_value('Database', 'database', ''))
            
            self.timeout_spin.setValue(int(self.config.get_value('Database', 'connection_timeout', '30')))
            self.max_connections_spin.setValue(int(self.config.get_value('Database', 'max_connections', '5')))
            
            # Scheduler-Einstellungen
            query_time_str = self.config.get_value('Scheduler', 'query_time', '23:00')
            hour, minute = map(int, query_time_str.split(':'))
            self.query_time_edit.setTime(QTime(hour, minute))
            
            self.retry_attempts_spin.setValue(int(self.config.get_value('Scheduler', 'retry_attempts', '3')))
            self.retry_interval_spin.setValue(int(self.config.get_value('Scheduler', 'retry_interval', '10')))
            self.max_data_age_spin.setValue(int(self.config.get_value('Scheduler', 'max_data_age', '90')))
            
            # Berichtseinstellungen
            self.highlight_threshold_spin.setValue(int(self.config.get_value('Report', 'highlight_threshold', '10')))
            self.history_days_spin.setValue(int(self.config.get_value('Report', 'history_days', '30')))
            
            export_format = self.config.get_value('Report', 'default_export_format', 'excel').lower()
            if export_format == 'csv':
                self.export_format_combo.setCurrentIndex(0)
            elif export_format == 'excel':
                self.export_format_combo.setCurrentIndex(1)
            else:
                self.export_format_combo.setCurrentIndex(2)
            
            self.export_path_edit.setText(self.config.get_value('Report', 'export_path', './reports'))
            
            # UI-Einstellungen
            theme = self.config.get_value('UI', 'theme', 'system').lower()
            if theme == 'light':
                self.theme_combo.setCurrentIndex(1)
            elif theme == 'dark':
                self.theme_combo.setCurrentIndex(2)
            else:
                self.theme_combo.setCurrentIndex(0)
            
            language = self.config.get_value('UI', 'language', 'de').lower()
            if language == 'en':
                self.language_combo.setCurrentIndex(1)
            else:
                self.language_combo.setCurrentIndex(0)
            
            self.refresh_interval_spin.setValue(int(self.config.get_value('UI', 'refresh_interval', '300')))
            
            # Logging-Einstellungen
            log_level = self.config.get_value('Logging', 'level', 'INFO').upper()
            log_level_index = self.log_level_combo.findText(log_level)
            if log_level_index >= 0:
                self.log_level_combo.setCurrentIndex(log_level_index)
            
            self.log_path_edit.setText(self.config.get_value('Logging', 'log_path', './logs'))
            
            max_log_size = int(self.config.get_value('Logging', 'max_log_size', '10485760'))
            self.max_log_size_spin.setValue(max_log_size // 1048576)  # Von Bytes in MB
            
            self.backup_count_spin.setValue(int(self.config.get_value('Logging', 'backup_count', '5')))
            
        except Exception as e:
            self.logger.log_error(f"Fehler beim Laden der Einstellungen: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Einstellungen:\n{str(e)}")
    
    def save_settings(self):
        """Speichert Einstellungen.
        
        Returns:
            bool: True bei Erfolg, sonst False
        """
        try:
            # Datenbankeinstellungen
            db_type = 'mysql' if self.db_type_combo.currentIndex() == 0 else 'mssql'
            self.config.set_value('Database', 'type', db_type)
            self.config.set_value('Database', 'host', self.host_edit.text())
            self.config.set_value('Database', 'port', self.port_edit.text())
            self.config.set_value('Database', 'username', self.username_edit.text())
            self.config.set_value('Database', 'password', self.password_edit.text())
            self.config.set_value('Database', 'database', self.database_edit.text())
            self.config.set_value('Database', 'connection_timeout', str(self.timeout_spin.value()))
            self.config.set_value('Database', 'max_connections', str(self.max_connections_spin.value()))
            
            # Scheduler-Einstellungen
            query_time = self.query_time_edit.time().toString('HH:mm')
            self.config.set_value('Scheduler', 'query_time', query_time)
            self.config.set_value('Scheduler', 'retry_attempts', str(self.retry_attempts_spin.value()))
            self.config.set_value('Scheduler', 'retry_interval', str(self.retry_interval_spin.value()))
            self.config.set_value('Scheduler', 'max_data_age', str(self.max_data_age_spin.value()))
            
            # Berichtseinstellungen
            self.config.set_value('Report', 'highlight_threshold', str(self.highlight_threshold_spin.value()))
            self.config.set_value('Report', 'history_days', str(self.history_days_spin.value()))
            
            export_format_index = self.export_format_combo.currentIndex()
            export_format = 'csv' if export_format_index == 0 else 'excel' if export_format_index == 1 else 'pdf'
            self.config.set_value('Report', 'default_export_format', export_format)
            
            self.config.set_value('Report', 'export_path', self.export_path_edit.text())
            
            # UI-Einstellungen
            theme_index = self.theme_combo.currentIndex()
            theme = 'system' if theme_index == 0 else 'light' if theme_index == 1 else 'dark'
            self.config.set_value('UI', 'theme', theme)
            
            language = 'de' if self.language_combo.currentIndex() == 0 else 'en'
            self.config.set_value('UI', 'language', language)
            
            self.config.set_value('UI', 'refresh_interval', str(self.refresh_interval_spin.value()))
            
            # Logging-Einstellungen
            self.config.set_value('Logging', 'level', self.log_level_combo.currentText())
            self.config.set_value('Logging', 'log_path', self.log_path_edit.text())
            
            max_log_size_bytes = self.max_log_size_spin.value() * 1048576  # Von MB in Bytes
            self.config.set_value('Logging', 'max_log_size', str(max_log_size_bytes))
            
            self.config.set_value('Logging', 'backup_count', str(self.backup_count_spin.value()))
            
            # Konfiguration speichern
            if self.config.save_config():
                self.logger.log_info("Einstellungen erfolgreich gespeichert")
                return True
            else:
                self.logger.log_error("Fehler beim Speichern der Einstellungen")
                QMessageBox.critical(self, "Fehler", "Die Einstellungen konnten nicht gespeichert werden.")
                return False
                
        except Exception as e:
            self.logger.log_error(f"Fehler beim Speichern der Einstellungen: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern der Einstellungen:\n{str(e)}")
            return False
    
    def apply_settings(self):
        """Wendet Einstellungen an ohne den Dialog zu schließen."""
        if self.save_settings():
            QMessageBox.information(self, "Einstellungen", "Die Einstellungen wurden erfolgreich angewendet.")
    
    def test_connection(self):
        """Testet die Datenbankverbindung."""
        # Temporäre Einstellungen übernehmen
        original_type = self.config.get_value('Database', 'type')
        original_host = self.config.get_value('Database', 'host')
        original_port = self.config.get_value('Database', 'port')
        original_username = self.config.get_value('Database', 'username')
        original_password = self.config.get_value('Database', 'password')
        original_database = self.config.get_value('Database', 'database')
        
        try:
            # Temporäre Einstellungen setzen
            self.config.set_value('Database', 'type', 'mysql' if self.db_type_combo.currentIndex() == 0 else 'mssql')
            self.config.set_value('Database', 'host', self.host_edit.text())
            self.config.set_value('Database', 'port', self.port_edit.text())
            self.config.set_value('Database', 'username', self.username_edit.text())
            self.config.set_value('Database', 'password', self.password_edit.text())
            self.config.set_value('Database', 'database', self.database_edit.text())
            
            # Verbindung neu initialisieren
            if self.db_type_combo.currentIndex() == 0:
                self.db_manager.connect_mysql()
            else:
                self.db_manager.connect_mssql()
            
            # Verbindung testen
            if self.db_manager.test_connection():
                QMessageBox.information(self, "Verbindungstest", "Die Verbindung zur Datenbank war erfolgreich.")
            else:
                QMessageBox.warning(self, "Verbindungstest", "Die Verbindung zur Datenbank konnte nicht hergestellt werden.")
                
        except Exception as e:
            self.logger.log_error(f"Fehler beim Testen der Datenbankverbindung: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Fehler beim Testen der Datenbankverbindung:\n{str(e)}")
            
        finally:
            # Ursprüngliche Einstellungen wiederherstellen
            self.config.set_value('Database', 'type', original_type)
            self.config.set_value('Database', 'host', original_host)
            self.config.set_value('Database', 'port', original_port)
            self.config.set_value('Database', 'username', original_username)
            self.config.set_value('Database', 'password', original_password)
            self.config.set_value('Database', 'database', original_database)
            
            # Verbindung wiederherstellen
            if original_type.lower() == 'mysql':
                self.db_manager.connect_mysql()
            else:
                self.db_manager.connect_mssql()
    
    def reset_defaults(self):
        """Setzt auf Standardeinstellungen zurück."""
        reply = QMessageBox.question(
            self, 
            "Standardeinstellungen", 
            "Möchten Sie wirklich alle Einstellungen auf die Standardwerte zurücksetzen?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.config.create_default_config()
                self.load_current_settings()
                QMessageBox.information(self, "Standardeinstellungen", "Die Einstellungen wurden auf die Standardwerte zurückgesetzt.")
            except Exception as e:
                self.logger.log_error(f"Fehler beim Zurücksetzen der Einstellungen: {str(e)}", exc_info=True)
                QMessageBox.critical(self, "Fehler", f"Fehler beim Zurücksetzen der Einstellungen:\n{str(e)}")
    
    def browse_export_path(self):
        """Öffnet einen Dialog zum Auswählen des Exportpfads."""
        current_path = self.export_path_edit.text()
        directory = QFileDialog.getExistingDirectory(self, "Exportpfad auswählen", current_path)
        
        if directory:
            self.export_path_edit.setText(directory)
    
    def browse_log_path(self):
        """Öffnet einen Dialog zum Auswählen des Log-Pfads."""
        current_path = self.log_path_edit.text()
        directory = QFileDialog.getExistingDirectory(self, "Log-Pfad auswählen", current_path)
        
        if directory:
            self.log_path_edit.setText(directory)
    
    def open_log_directory(self):
        """Öffnet das Log-Verzeichnis im Dateimanager."""
        import subprocess
        import platform
        
        log_path = self.log_path_edit.text()
        
        if not os.path.exists(log_path):
            QMessageBox.warning(self, "Log-Verzeichnis", "Das Log-Verzeichnis existiert noch nicht.")
            return
        
        try:
            if platform.system() == 'Windows':
                os.startfile(log_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', log_path])
            else:  # Linux und andere
                subprocess.Popen(['xdg-open', log_path])
        except Exception as e:
            self.logger.log_error(f"Fehler beim Öffnen des Log-Verzeichnisses: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Das Log-Verzeichnis konnte nicht geöffnet werden:\n{str(e)}")
    
    def accept(self):
        """Überschreibt die accept-Methode, um Einstellungen zu speichern."""
        if self.save_settings():
            super().accept()
    
    def reject(self):
        """Überschreibt die reject-Methode."""
        super().reject()
