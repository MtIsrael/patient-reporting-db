-- REPORT 03: 30-Day All-Cause Readmission Rate by Diagnosis
-- Request:  "Quality wants the 30-day readmission rate by primary diagnosis,
--            the measure CMS uses to penalize hospitals (HRRP)."
-- Skills:   window functions (LEAD), CTEs, conditional aggregation
-- Rules:    Index stay = inpatient discharge, excluding patients who expired.
--           Readmission = next inpatient admit within 30 days of discharge.

WITH inpatient AS (
    SELECT encounter_id,
           patient_id,
           primary_dx_code,
           admit_dt,
           discharge_dt,
           discharge_disposition,
           LEAD(admit_dt) OVER (PARTITION BY patient_id ORDER BY admit_dt) AS next_admit_dt
    FROM encounters
    WHERE encounter_class = 'inpatient'
),
index_stays AS (
    SELECT *,
           CASE WHEN next_admit_dt IS NOT NULL
                 AND julianday(next_admit_dt) - julianday(discharge_dt) <= 30
                THEN 1 ELSE 0 END AS readmitted_30d
    FROM inpatient
    WHERE discharge_disposition <> 'Expired'
)
SELECT i.primary_dx_code                         AS icd10,
       MAX(dx.description)                       AS diagnosis,
       COUNT(*)                                  AS index_discharges,
       SUM(i.readmitted_30d)                     AS readmissions,
       ROUND(100.0 * SUM(i.readmitted_30d) / COUNT(*), 1) AS readmit_rate_pct
FROM index_stays i
JOIN diagnoses dx ON dx.encounter_id = i.encounter_id AND dx.is_primary = 1
GROUP BY i.primary_dx_code
HAVING COUNT(*) >= 15
ORDER BY readmit_rate_pct DESC;
