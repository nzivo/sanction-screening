-- Migration: Increase PEP field lengths
-- Purpose: Fix "value too long for type character varying(300)" error
-- Date: 2026-03-13

-- Change position field from VARCHAR(300) to TEXT to support longer descriptions
ALTER TABLE pep_lists ALTER COLUMN position TYPE TEXT;

-- Change organization field from VARCHAR(300) to VARCHAR(500)
ALTER TABLE pep_lists ALTER COLUMN organization TYPE VARCHAR(500);

-- Verify changes
SELECT 
    column_name, 
    data_type, 
    character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'pep_lists' 
AND column_name IN ('position', 'organization');
