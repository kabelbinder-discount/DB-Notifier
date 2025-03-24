-- Abfrage für Artikel mit Nullbestand
-- Für beide Datenbanktypen identisch

SELECT 
    a.artikel_id,
    a.artikelnummer,
    a.bezeichnung,
    a.hersteller,
    a.kategorie,
    a.status,
    l.lager_id,
    l.lager_name,
    l.bestand
FROM 
    artikel a
JOIN 
    lagerbestand l ON a.artikel_id = l.artikel_id
WHERE 
    l.bestand = 0
    AND a.status = 'aktiv'
ORDER BY 
    a.artikelnummer
