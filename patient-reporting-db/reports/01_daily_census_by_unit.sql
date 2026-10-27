-- REPORT 01: Daily Census by Unit
-- Request:  "Nursing leadership wants average and peak midnight census for each
--            inpatient unit last month, plus occupancy against staffed beds."
-- Skills:   recursive CTE (date series), range joins, aggregation
-- Period:   September 2026

WITH RECURSIVE days(day) AS (
    SELECT date('2026-09-01')
    UNION ALL
    SELECT date(day, '+1 day') FROM days WHERE day < '2026-09-30'
),
midnight_census AS (
    SELECT d.day,
           dep.department_id,
           COUNT(e.encounter_id) AS patients
    FROM days d
    CROSS JOIN departments dep
    LEFT JOIN encounters e
           ON e.department_id = dep.department_id
          AND e.encounter_class = 'inpatient'
          AND e.admit_dt     <= d.day || ' 23:59:59'
          AND e.discharge_dt >  d.day || ' 23:59:59'
    WHERE dep.unit_type IN ('Inpatient', 'Critical Care')
    GROUP BY d.day, dep.department_id
)
SELECT dep.name                                   AS unit,
       dep.bed_count                              AS staffed_beds,
       ROUND(AVG(mc.patients), 1)                 AS avg_census,
       MAX(mc.patients)                           AS peak_census,
       ROUND(100.0 * AVG(mc.patients) / dep.bed_count, 1) AS avg_occupancy_pct
FROM midnight_census mc
JOIN departments dep ON dep.department_id = mc.department_id
GROUP BY dep.name, dep.bed_count
ORDER BY avg_occupancy_pct DESC;
