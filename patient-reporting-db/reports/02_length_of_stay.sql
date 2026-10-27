-- REPORT 02: Average Length of Stay (ALOS) by Unit and Diagnosis
-- Request:  "Case management wants to know which diagnoses drive the longest
--            stays on each unit so they can target discharge planning."
-- Skills:   date math, joins, GROUP BY with HAVING, ranking
-- Period:   All inpatient discharges

SELECT dep.name                                              AS unit,
       e.primary_dx_code                                     AS icd10,
       dx.description                                        AS diagnosis,
       COUNT(*)                                              AS discharges,
       ROUND(AVG(julianday(e.discharge_dt) - julianday(e.admit_dt)), 2) AS alos_days,
       ROUND(MAX(julianday(e.discharge_dt) - julianday(e.admit_dt)), 1) AS longest_stay_days
FROM encounters e
JOIN departments dep ON dep.department_id = e.department_id
JOIN diagnoses  dx   ON dx.encounter_id = e.encounter_id AND dx.is_primary = 1
WHERE e.encounter_class = 'inpatient'
GROUP BY dep.name, e.primary_dx_code, dx.description
HAVING COUNT(*) >= 10
ORDER BY dep.name, alos_days DESC;
