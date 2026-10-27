-- REPORT 08: High Utilizers (3+ Inpatient Admissions in 12 Months)
-- Request:  "Care coordination wants patients admitted 3 or more times in the
--            last year, with their top diagnosis and total bed days."
-- Skills:   window function (ROW_NUMBER) for "top 1 per group", HAVING, joins

WITH recent AS (
    SELECT *
    FROM encounters
    WHERE encounter_class = 'inpatient'
      AND admit_dt >= datetime('2026-09-30', '-12 months')
),
top_dx AS (
    SELECT patient_id, primary_dx_code,
           ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY COUNT(*) DESC, primary_dx_code) AS rn
    FROM recent
    GROUP BY patient_id, primary_dx_code
)
SELECT p.mrn,
       p.last_name || ', ' || p.first_name                                   AS patient,
       CAST((julianday('2026-09-30') - julianday(p.birth_date)) / 365.25 AS INTEGER) AS age,
       COUNT(*)                                                              AS admissions_12mo,
       ROUND(SUM(julianday(r.discharge_dt) - julianday(r.admit_dt)), 1)      AS total_bed_days,
       t.primary_dx_code                                                     AS most_common_dx,
       date(MAX(r.discharge_dt))                                             AS last_discharge
FROM recent r
JOIN patients p ON p.patient_id = r.patient_id
JOIN top_dx  t ON t.patient_id = r.patient_id AND t.rn = 1
GROUP BY p.patient_id
HAVING COUNT(*) >= 3
ORDER BY admissions_12mo DESC, total_bed_days DESC;
