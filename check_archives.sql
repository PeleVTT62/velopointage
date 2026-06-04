-- Script SQL pour vérifier et gérer les archives
-- Usage: sqlite3 data/db.sqlite < check_archives.sql

.mode column
.headers on

-- 1. Vérifier l'existence des tables
.print "=== TABLES EXISTANTES ==="
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
.print ""

-- 2. Statistiques passages actuels
.print "=== PASSAGES ACTUELS (table passages) ==="
SELECT COUNT(*) as total FROM passages;
SELECT equipe, COUNT(*) as count 
FROM passages 
GROUP BY equipe 
ORDER BY count DESC;
.print ""

-- 3. Statistiques archives
.print "=== PASSAGES ARCHIVES ==="
SELECT COUNT(*) as total FROM passages_archives;
.print ""

.print "Répartition par équipe (archives):"
SELECT equipe, COUNT(*) as count 
FROM passages_archives 
GROUP BY equipe 
ORDER BY count DESC;
.print ""

-- 4. Période couverte par les archives
.print "=== PERIODE DES ARCHIVES ==="
SELECT 
    MIN(timestamp) as premiere_date,
    MAX(timestamp) as derniere_date,
    COUNT(*) as total_passages
FROM passages_archives;
.print ""

-- 5. Archives par jour
.print "=== ARCHIVES PAR JOUR ==="
SELECT 
    DATE(timestamp) as jour,
    COUNT(*) as passages
FROM passages_archives
GROUP BY DATE(timestamp)
ORDER BY jour DESC
LIMIT 10;
.print ""

-- 6. Derniers passages archivés
.print "=== DERNIERS PASSAGES ARCHIVES (10) ==="
SELECT 
    equipe,
    ville,
    timestamp,
    observateur
FROM passages_archives
ORDER BY timestamp DESC
LIMIT 10;
.print ""

-- 7. Taille approximative des tables
.print "=== TAILLE APPROXIMATIVE ==="
SELECT 
    'passages' as table_name,
    COUNT(*) * 200 / 1024.0 as size_kb
FROM passages
UNION ALL
SELECT 
    'passages_archives' as table_name,
    COUNT(*) * 200 / 1024.0 as size_kb
FROM passages_archives;
.print ""

-- 8. Passages du jour (actuels + archives)
.print "=== PASSAGES DU JOUR ==="
.print "Passages actuels du jour:"
SELECT COUNT(*) as count
FROM passages
WHERE DATE(timestamp) = DATE('now');

.print ""
.print "Passages archivés du jour:"
SELECT COUNT(*) as count
FROM passages_archives
WHERE DATE(timestamp) = DATE('now');
