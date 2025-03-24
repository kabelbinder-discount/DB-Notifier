#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Task-Scheduler für die Artikel-Tracking-Anwendung.
Verantwortlich für die Planung und Ausführung von zeitgesteuerten Aufgaben.
"""

import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED


class TaskScheduler:
    """Klasse zur Planung und Ausführung von Aufgaben."""
    
    def __init__(self, inventory_tracker, config, logger):
        """Initialisiert den TaskScheduler.
        
        Args:
            inventory_tracker (InventoryTracker): Inventory-Tracker-Instanz
            config (ConfigManager): Konfigurationsmanager-Instanz
            logger (Logger): Logger-Instanz
        """
        self.inventory_tracker = inventory_tracker
        self.config = config
        self.logger = logger
        
        # Wiederholungseinstellungen aus Konfiguration laden
        self.retry_attempts = int(self.config.get_value('Scheduler', 'retry_attempts', '3'))
        self.retry_interval = int(self.config.get_value('Scheduler', 'retry_interval', '10'))
        
        # Scheduler initialisieren
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_listener(self._handle_job_event, 
                                   EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)
        self.scheduler.start()
        
        # Aufgaben-Status
        self.current_task_id = None
        self.task_failures = {}
        
        self.logger.log_info("Task-Scheduler initialisiert")
    
    def schedule_daily_task(self, time_str):
        """Plant eine tägliche Aufgabe.
        
        Args:
            time_str (str): Ausführungszeit im Format 'HH:MM'
            
        Returns:
            str: Aufgaben-ID
        """
        try:
            # Zeit parsen
            hour, minute = map(int, time_str.split(':'))
            
            # Aufgabe mit Cron-Trigger planen
            job = self.scheduler.add_job(
                self.execute_task,
                CronTrigger(hour=hour, minute=minute),
                id='daily_inventory_task',
                replace_existing=True
            )
            
            self.logger.log_info(f"Tägliche Aufgabe geplant für {time_str} Uhr")
            return job.id
        
        except Exception as e:
            self.logger.log_error(f"Fehler beim Planen der täglichen Aufgabe: {str(e)}", exc_info=True)
            return None
    
    def execute_task(self):
        """Führt die geplante Aufgabe aus.
        
        Returns:
            bool: True bei erfolgreicher Ausführung, sonst False
        """
        self.logger.log_info("Führe geplante Aufgabe aus...")
        task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.current_task_id = task_id
        
        try:
            # Bestandsabfrage ausführen
            result = self.inventory_tracker.track_daily_inventory()
            
            if result:
                self.logger.log_info("Aufgabe erfolgreich ausgeführt")
                self.notify_task_status(task_id, "success")
                return True
            else:
                self.logger.log_warning("Aufgabe wurde nicht erfolgreich ausgeführt")
                self.handle_task_failure(task_id)
                return False
                
        except Exception as e:
            self.logger.log_error(f"Fehler bei der Aufgabenausführung: {str(e)}", exc_info=True)
            self.handle_task_failure(task_id)
            return False
    
    def handle_task_failure(self, task_id):
        """Behandelt den Fehlschlag einer Aufgabe.
        
        Args:
            task_id (str): ID der fehlgeschlagenen Aufgabe
        """
        # Fehlschlag protokollieren
        if task_id not in self.task_failures:
            self.task_failures[task_id] = 0
        
        self.task_failures[task_id] += 1
        current_attempt = self.task_failures[task_id]
        
        self.logger.log_warning(
            f"Aufgabe {task_id} fehlgeschlagen. Versuch {current_attempt}/{self.retry_attempts}"
        )
        
        # Nochmal versuchen, wenn maximale Versuche nicht erreicht
        if current_attempt < self.retry_attempts:
            self.retry_failed_task(task_id)
        else:
            self.logger.log_error(
                f"Aufgabe {task_id} endgültig fehlgeschlagen nach {self.retry_attempts} Versuchen"
            )
            self.notify_task_status(task_id, "failed")
    
    def retry_failed_task(self, task_id):
        """Wiederholt eine fehlgeschlagene Aufgabe.
        
        Args:
            task_id (str): ID der zu wiederholenden Aufgabe
        """
        current_attempt = self.task_failures[task_id]
        wait_time = self.retry_interval * current_attempt  # Progressives Warten
        
        self.logger.log_info(
            f"Plane Wiederholung für Aufgabe {task_id} in {wait_time} Minuten"
        )
        
        # Einmalige Aufgabe für Wiederholung planen
        self.scheduler.add_job(
            self.execute_task,
            IntervalTrigger(minutes=wait_time, start_date=datetime.now()),
            id=f"retry_{task_id}_{current_attempt}",
            replace_existing=True
        )
    
    def _handle_job_event(self, event):
        """Callback-Methode für Scheduler-Ereignisse.
        
        Args:
            event (JobEvent): Ereignisobjekt
        """
        if event.code == EVENT_JOB_ERROR:
            self.logger.log_error(
                f"Fehler bei Job {event.job_id}: {str(event.exception)}"
            )
        elif event.code == EVENT_JOB_EXECUTED:
            self.logger.log_debug(f"Job {event.job_id} ausgeführt")
    
    def notify_task_status(self, task_id, status):
        """Benachrichtigt über Aufgabenstatus.
        
        Args:
            task_id (str): Aufgaben-ID
            status (str): Status ("success", "failed", "retry")
        """
        self.logger.log_info(f"Aufgabenstatus für {task_id}: {status}")
        
        # Hier könnten Benachrichtigungen implementiert werden
        # z.B. E-Mail-Versand, Desktop-Benachrichtigungen etc.
    
    def stop_scheduler(self):
        """Stoppt den Scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.log_info("Scheduler gestoppt")
