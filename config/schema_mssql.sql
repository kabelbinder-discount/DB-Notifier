-- MSSQL-Beispielschema für die Artikel-Tracking-Anwendung
-- Dieses Schema kann als Referenz oder zum Erstellen einer Testdatenbank verwendet werden

-- Datenbank erstellen
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'inventar')
BEGIN
    CREATE DATABASE inventar;
END
GO

USE inventar;
GO

-- Artikel-Tabelle
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[artikel]') AND type in (N'U'))
BEGIN
    CREATE TABLE artikel (
        artikel_id INT IDENTITY(1,1) PRIMARY KEY,
        artikelnummer NVARCHAR(50) NOT NULL UNIQUE,
        bezeichnung NVARCHAR(255) NOT NULL,
        hersteller NVARCHAR(100),
        kategorie NVARCHAR(100),
        status NVARCHAR(10) NOT NULL DEFAULT 'aktiv' CHECK (status IN ('aktiv', 'inaktiv')),
        erstellt_am DATETIME NOT NULL DEFAULT GETDATE(),
        aktualisiert_am DATETIME NOT NULL DEFAULT GETDATE()
    );
    
    CREATE INDEX idx_artikelnummer ON artikel(artikelnummer);
    CREATE INDEX idx_kategorie ON artikel(kategorie);
    CREATE INDEX idx_status ON artikel(status);
END
GO

-- Lager-Tabelle
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[lager]') AND type in (N'U'))
BEGIN
    CREATE TABLE lager (
        lager_id INT IDENTITY(1,1) PRIMARY KEY,
        lager_name NVARCHAR(100) NOT NULL,
        standort NVARCHAR(255),
        erstellt_am DATETIME NOT NULL DEFAULT GETDATE(),
        aktualisiert_am DATETIME NOT NULL DEFAULT GETDATE()
    );
END
GO

-- Lagerbestand-Tabelle
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[lagerbestand]') AND type in (N'U'))
BEGIN
    CREATE TABLE lagerbestand (
        lagerbestand_id INT IDENTITY(1,1) PRIMARY KEY,
        artikel_id INT NOT NULL,
        lager_id INT NOT NULL,
        bestand INT NOT NULL DEFAULT 0,
        lager_name NVARCHAR(100),
        erstellt_am DATETIME NOT NULL DEFAULT GETDATE(),
        aktualisiert_am DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT FK_lagerbestand_artikel FOREIGN KEY (artikel_id) REFERENCES artikel(artikel_id),
        CONSTRAINT FK_lagerbestand_lager FOREIGN KEY (lager_id) REFERENCES lager(lager_id),
        CONSTRAINT UK_artikel_lager UNIQUE (artikel_id, lager_id)
    );
    
    CREATE INDEX idx_bestand ON lagerbestand(bestand);
END
GO

-- Bestandshistorie-Tabelle
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[bestandshistorie]') AND type in (N'U'))
BEGIN
    CREATE TABLE bestandshistorie (
        historie_id INT IDENTITY(1,1) PRIMARY KEY,
        artikel_id INT NOT NULL,
        lager_id INT NOT NULL,
        bestand INT NOT NULL,
        erfasst_am DATE NOT NULL,
        erstellungszeit DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT FK_historie_artikel FOREIGN KEY (artikel_id) REFERENCES artikel(artikel_id),
        CONSTRAINT FK_historie_lager FOREIGN KEY (lager_id) REFERENCES lager(lager_id),
        CONSTRAINT UK_artikel_lager_datum UNIQUE (artikel_id, lager_id, erfasst_am)
    );
    
    CREATE INDEX idx_erfasst_am ON bestandshistorie(erfasst_am);
END
GO

-- Beispieldaten einfügen
-- Lager
IF NOT EXISTS (SELECT TOP 1 lager_id FROM lager)
BEGIN
    INSERT INTO lager (lager_name, standort) VALUES
    ('Hauptlager', 'Stuttgart'),
    ('Filiale Nord', 'Hamburg'),
    ('Filiale Süd', 'München');
END
GO

-- Artikel
IF NOT EXISTS (SELECT TOP 1 artikel_id FROM artikel)
BEGIN
    INSERT INTO artikel (artikelnummer, bezeichnung, hersteller, kategorie, status) VALUES
    ('A0001', 'Notebook Pro 15', 'TechBrand', 'Computer', 'aktiv'),
    ('A0002', 'Wireless Mouse', 'PeripheralTech', 'Zubehör', 'aktiv'),
    ('A0003', 'Monitor 24 Zoll', 'DisplayTech', 'Monitore', 'aktiv'),
    ('A0004', 'USB-Kabel 2m', 'CablePro', 'Zubehör', 'aktiv'),
    ('A0005', 'Webcam HD', 'VisionTech', 'Zubehör', 'aktiv'),
    ('A0006', 'Tablet Mini', 'TechBrand', 'Tablets', 'aktiv'),
    ('A0007', 'Lautsprecher Bluetooth', 'SoundPro', 'Audio', 'aktiv'),
    ('A0008', 'Tastatur Ergonomisch', 'PeripheralTech', 'Zubehör', 'aktiv'),
    ('A0009', 'Externe Festplatte 1TB', 'StorageTech', 'Speicher', 'aktiv'),
    ('A0010', 'HDMI-Kabel 3m', 'CablePro', 'Zubehör', 'inaktiv');
END
GO

-- Lagerbestand
IF NOT EXISTS (SELECT TOP 1 lagerbestand_id FROM lagerbestand)
BEGIN
    INSERT INTO lagerbestand (artikel_id, lager_id, bestand, lager_name) VALUES
    (1, 1, 15, 'Hauptlager'),
    (1, 2, 5, 'Filiale Nord'),
    (1, 3, 7, 'Filiale Süd'),
    (2, 1, 30, 'Hauptlager'),
    (2, 2, 10, 'Filiale Nord'),
    (3, 1, 8, 'Hauptlager'),
    (3, 3, 3, 'Filiale Süd'),
    (4, 1, 50, 'Hauptlager'),
    (4, 2, 20, 'Filiale Nord'),
    (4, 3, 15, 'Filiale Süd'),
    (5, 1, 0, 'Hauptlager'),
    (6, 1, 12, 'Hauptlager'),
    (6, 3, 5, 'Filiale Süd'),
    (7, 1, 7, 'Hauptlager'),
    (8, 1, 10, 'Hauptlager'),
    (9, 1, 4, 'Hauptlager'),
    (10, 1, 0, 'Hauptlager');
END
GO

-- Bestandshistorie (für die letzten 3 Tage)
IF NOT EXISTS (SELECT TOP 1 historie_id FROM bestandshistorie)
BEGIN
    DECLARE @yesterday DATE = DATEADD(DAY, -1, CAST(GETDATE() AS DATE));
    DECLARE @day_before_yesterday DATE = DATEADD(DAY, -2, CAST(GETDATE() AS DATE));
    DECLARE @three_days_ago DATE = DATEADD(DAY, -3, CAST(GETDATE() AS DATE));

    -- Gestern
    INSERT INTO bestandshistorie (artikel_id, lager_id, bestand, erfasst_am) VALUES
    (1, 1, 12, @yesterday),
    (1, 2, 5, @yesterday),
    (1, 3, 8, @yesterday),
    (2, 1, 35, @yesterday),
    (2, 2, 12, @yesterday),
    (3, 1, 10, @yesterday),
    (3, 3, 4, @yesterday),
    (4, 1, 45, @yesterday),
    (4, 2, 20, @yesterday),
    (4, 3, 15, @yesterday),
    (5, 1, 2, @yesterday),
    (6, 1, 15, @yesterday),
    (6, 3, 6, @yesterday),
    (7, 1, 10, @yesterday),
    (8, 1, 8, @yesterday),
    (9, 1, 5, @yesterday),
    (10, 1, 3, @yesterday);

    -- Vorgestern
    INSERT INTO bestandshistorie (artikel_id, lager_id, bestand, erfasst_am) VALUES
    (1, 1, 15, @day_before_yesterday),
    (1, 2, 7, @day_before_yesterday),
    (1, 3, 9, @day_before_yesterday),
    (2, 1, 40, @day_before_yesterday),
    (2, 2, 15, @day_before_yesterday),
    (3, 1, 12, @day_before_yesterday),
    (3, 3, 5, @day_before_yesterday),
    (4, 1, 40, @day_before_yesterday),
    (4, 2, 18, @day_before_yesterday),
    (4, 3, 12, @day_before_yesterday),
    (5, 1, 5, @day_before_yesterday),
    (6, 1, 18, @day_before_yesterday),
    (6, 3, 8, @day_before_yesterday),
    (7, 1, 12, @day_before_yesterday),
    (8, 1, 10, @day_before_yesterday),
    (9, 1, 7, @day_before_yesterday),
    (10, 1, 5, @day_before_yesterday);

    -- Vor drei Tagen
    INSERT INTO bestandshistorie (artikel_id, lager_id, bestand, erfasst_am) VALUES
    (1, 1, 18, @three_days_ago),
    (1, 2, 8, @three_days_ago),
    (1, 3, 10, @three_days_ago),
    (2, 1, 45, @three_days_ago),
    (2, 2, 18, @three_days_ago),
    (3, 1, 15, @three_days_ago),
    (3, 3, 6, @three_days_ago),
    (4, 1, 35, @three_days_ago),
    (4, 2, 15, @three_days_ago),
    (4, 3, 10, @three_days_ago),
    (5, 1, 8, @three_days_ago),
    (6, 1, 20, @three_days_ago),
    (6, 3, 10, @three_days_ago),
    (7, 1, 15, @three_days_ago),
    (8, 1, 12, @three_days_ago),
    (9, 1, 10, @three_days_ago),
    (10, 1, 8, @three_days_ago);
END
GO
