-- Hauptinventar-Abfrage für MSSQL
-- Diese Abfrage ruft alle Artikel mit ihren aktuellen Beständen und Standorten ab

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
