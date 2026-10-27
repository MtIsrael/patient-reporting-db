-- REPORT 04: Abnormal Outpatient Labs With No Follow-Up Visit (Care Gap)
-- Request:  "Primary care wants a worklist of patients whose clinic labs came
--            back abnormal but who haven't been seen again within 30 days."
-- Skills:   NOT EXISTS anti-join, multi-table joins, worklist output
-- Output:   One row per patient + lab, most severe first

SELECT p.mrn,
       p.last_name || ', ' || p.first_name                   AS patient,
       l.test_name,
       l.result_value || ' ' || l.unit                       AS result,
       l.ref_low || ' - ' || l.ref_high                      AS reference_range,
       l.abnormal_flag,
       date(l.collected_dt)                                  AS collected,
       pr.name                                               AS ordering_provider
FROM labs l
JOIN encounters e ON e.encounter_id = l.encounter_id
JOIN patients   p ON p.patient_id   = l.patient_id
JOIN providers  pr ON pr.provider_id = e.provider_id
WHERE e.encounter_class = 'outpatient'
  AND l.abnormal_flag IN ('H', 'L', 'HH', 'LL')
  AND l.collected_dt < datetime('2026-09-30', '-30 days')       -- give 30 days to follow up
  AND NOT EXISTS (
        SELECT 1
        FROM encounters f
        WHERE f.patient_id = l.patient_id
          AND f.admit_dt >  l.collected_dt
          AND f.admit_dt <= datetime(l.collected_dt, '+30 days')
  )
ORDER BY CASE l.abnormal_flag WHEN 'HH' THEN 1 WHEN 'LL' THEN 1 ELSE 2 END,
         l.collected_dt DESC;
