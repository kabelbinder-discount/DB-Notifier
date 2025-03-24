-- Abfrage für kürzlich deaktivierte Artikel
-- Diese Abfrage ruft Artikel ab, die kürzlich deaktiviert wurden
-- Für beide Datenbanktypen identisch

SELECT 
    a.artikel_id,
    a.artikelnummer,
    a.bezeichnung,
    a.hersteller,
    a.kategorie,
    a.status,
    a.aktualisiert_am
FROM 
    artikel a
WHERE 
    a.status = 'inaktiv'
    AND a.aktualisiert_am >= :last_check_date
ORDER BY 
    a.aktualisiert_am DESC
