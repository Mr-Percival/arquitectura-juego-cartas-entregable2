-- Catálogo de cartas (52 + 2 comodines) y variantes de referencia.
INSERT INTO carta (carta_codigo, rango, pinta)
SELECT CASE r WHEN 1 THEN 'A' WHEN 11 THEN 'J' WHEN 12 THEN 'Q' WHEN 13 THEN 'K' ELSE r::text END || p, r, p
FROM generate_series(1, 13) AS r CROSS JOIN unnest(ARRAY['H', 'D', 'C', 'S']) AS p;
INSERT INTO carta (carta_codigo, rango, pinta) VALUES ('JK1', NULL, NULL), ('JK2', NULL, NULL);

-- PostgresRepositoryAdapter hace este UPSERT al arrancar con la lista que descubrió PluginRegistry.
INSERT INTO variante (variante_codigo, nombre, version_plugin, version_contrato) VALUES
    ('CLASICA_433',  'Clásica 4-3-3', '1.0.0', '1.0'),
    ('APUNTADO_101', 'Apuntado a 101', '1.0.0', '1.0')
ON CONFLICT (variante_codigo) DO UPDATE
    SET version_plugin = EXCLUDED.version_plugin, version_contrato = EXCLUDED.version_contrato, activa = TRUE;
