-- REPORT 05: Surgical Volume, OR Case Time, and PACU Time by Procedure
-- Request:  "Perioperative services wants case volume and average OR and PACU
--            minutes per procedure to plan block time and PACU staffing."
-- Skills:   time-interval math, multi-join, aggregation
-- Metrics:  OR minutes = in room -> out of room; PACU minutes = out of room -> PACU out

SELECT pr.cpt_code,
       pr.description                                                         AS procedure_name,
       s.name                                                                 AS surgeon,
       COUNT(*)                                                               AS cases,
       ROUND(AVG((julianday(pr.out_room_dt) - julianday(pr.in_room_dt)) * 1440))  AS avg_or_minutes,
       ROUND(AVG((julianday(pr.out_room_dt) - julianday(pr.incision_dt)) * 1440)) AS avg_incision_to_out_min,
       ROUND(AVG((julianday(pr.pacu_out_dt) - julianday(pr.out_room_dt)) * 1440)) AS avg_pacu_minutes,
       ROUND(AVG(pr.asa_class), 1)                                            AS avg_asa_class
FROM procedures pr
JOIN providers s ON s.provider_id = pr.surgeon_id
GROUP BY pr.cpt_code, pr.description, s.name
ORDER BY cases DESC;
