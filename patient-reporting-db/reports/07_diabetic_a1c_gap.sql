-- REPORT 07: Diabetic Patients Without an A1c in the Last 12 Months (Quality Measure)
-- Request:  "Population health needs the list of diabetic patients missing a
--            Hemoglobin A1c in the past year, for outreach (HEDIS-style measure)."
-- Skills:   CTEs, LEFT JOIN + IS NULL, MAX over subgroup, age calculation

WITH diabetics AS (
    SELECT DISTINCT e.patient_id
    FROM diagnoses d
    JOIN encounters e ON e.encounter_id = d.encounter_id
    WHERE d.icd10_code LIKE 'E11%'
),
last_a1c AS (
    SELECT patient_id, MAX(collected_dt) AS last_a1c_dt
    FROM labs
    WHERE test_name = 'Hemoglobin A1c'
    GROUP BY patient_id
)
SELECT p.mrn,
       p.last_name || ', ' || p.first_name                          AS patient,
       CAST((julianday('2026-09-30') - julianday(p.birth_date)) / 365.25 AS INTEGER) AS age,
       p.insurance,
       COALESCE(date(a.last_a1c_dt), 'Never')                      AS last_a1c
FROM diabetics dm
JOIN patients p       ON p.patient_id = dm.patient_id
LEFT JOIN last_a1c a  ON a.patient_id = dm.patient_id
WHERE a.last_a1c_dt IS NULL
   OR a.last_a1c_dt < datetime('2026-09-30', '-12 months')
ORDER BY last_a1c, p.last_name;
