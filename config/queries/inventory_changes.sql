-- Abfrage für Bestandsänderungen
-- Diese Abfrage vergleicht die aktuellen Bestände mit den historischen Daten
-- Für beide Datenbanktypen mit kleineren Anpassungen

SELECT
    a.artikel_id,
    a.artikelnummer,
    a.bezeichnung,
    a.kategorie,
    a.status,
    l.lager_id,
    l.lager_name,
    l.bestand AS aktueller_bestand,
    h.bestand AS vorheriger_bestand,
    (l.bestand - h.bestand) AS aenderung,
    CASE 
        WHEN h.bestand = 0 THEN NULL
        ELSE ROUND(((l.bestand - h.bestand) * 100.0 / h.bestand), 2)
    END AS aenderung_prozent
FROM
    artikel a
JOIN
    lagerbestand l ON a.artikel_id = l.artikel_id
JOIN
    bestandshistorie h ON a.artikel_id = h.artikel_id AND l.lager_id = h.lager_id
WHERE
    h.erfasst_am = :previous_date
    AND (ABS(l.bestand - h.bestand) > 0)
ORDER BY
    ABS(CASE 
        WHEN h.bestand = 0 THEN 0
        ELSE ROUND(((l.bestand - h.bestand) * 100.0 / h.bestand), 2)
    END) DESC
