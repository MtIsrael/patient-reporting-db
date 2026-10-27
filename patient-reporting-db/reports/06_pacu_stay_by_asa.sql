-- REPORT 06: PACU Length of Stay by ASA Class and Hour of Arrival
-- Request:  "The PACU manager says late-afternoon arrivals stay longer and back
--            up the OR. Is that true, and does patient acuity (ASA) explain it?"
-- Skills:   CASE bucketing, strftime, pivot-style conditional aggregation

SELECT CASE
         WHEN CAST(strftime('%H', out_room_dt) AS INTEGER) < 12 THEN '1) Before noon'
         WHEN CAST(strftime('%H', out_room_dt) AS INTEGER) < 16 THEN '2) 12:00-15:59'
         ELSE '3) 16:00 or later'
       END                                                                  AS pacu_arrival_window,
       COUNT(*)                                                             AS cases,
       ROUND(AVG((julianday(pacu_out_dt) - julianday(out_room_dt)) * 1440)) AS avg_pacu_min,
       ROUND(AVG(CASE WHEN asa_class <= 2 THEN (julianday(pacu_out_dt) - julianday(out_room_dt)) * 1440 END)) AS asa_1_2_avg_min,
       ROUND(AVG(CASE WHEN asa_class >= 3 THEN (julianday(pacu_out_dt) - julianday(out_room_dt)) * 1440 END)) AS asa_3plus_avg_min,
       SUM(CASE WHEN (julianday(pacu_out_dt) - julianday(out_room_dt)) * 1440 > 120 THEN 1 ELSE 0 END)       AS stays_over_2hrs
FROM procedures
GROUP BY pacu_arrival_window
ORDER BY pacu_arrival_window;
