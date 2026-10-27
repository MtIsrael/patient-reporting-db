"""
Generate a synthetic hospital dataset (no real patient data).

Creates CSV files in ./data that model a small health system's clinical data:
patients, departments, providers, encounters, diagnoses, labs, medications,
and surgical procedures. Patterns are built in on purpose (readmissions,
abnormal labs, surgical volume) so the SQL reports have something to find.

Usage:
    python generate_data.py              # 2,500 patients, seed 42
    python generate_data.py --patients 2000 --seed 7
"""
import argparse
import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
START = datetime(2025, 1, 1)
END = datetime(2026, 9, 30)

FIRST_F = ["Maria", "Aisha", "Jennifer", "Linda", "Grace", "Sofia", "Keisha", "Emily", "Rosa", "Hannah",
           "Priya", "Danielle", "Olivia", "Carmen", "Nicole", "Tanya", "Mei", "Ruth", "Angela", "Brianna"]
FIRST_M = ["James", "Michael", "Carlos", "David", "Andre", "Robert", "Kevin", "Luis", "Daniel", "Marcus",
           "Thomas", "Anthony", "Jamal", "William", "Raj", "Eric", "Victor", "Samuel", "Brian", "Isaac"]
LAST = ["Smith", "Johnson", "Williams", "Brown", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Lee",
        "Walker", "Hall", "Allen", "Young", "King", "Wright", "Lopez", "Hill", "Scott", "Green", "Adams",
        "Baker", "Nelson", "Carter", "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell"]
CITIES = [("Wilmington", "DE", "19801"), ("Newark", "DE", "19711"), ("Dover", "DE", "19901"),
          ("Middletown", "DE", "19709"), ("Bear", "DE", "19701"), ("New Castle", "DE", "19720"),
          ("Elkton", "MD", "21921"), ("Chester", "PA", "19013")]
INSURANCE = ["Medicare", "Medicaid", "Commercial - BCBS", "Commercial - Aetna", "Commercial - Cigna",
             "Medicare Advantage", "Self-Pay"]

DEPARTMENTS = [
    # id, name, unit_type, beds
    (1, "Emergency Department", "Emergency", 40),
    (2, "Medical-Surgical 4 West", "Inpatient", 16),
    (3, "Cardiac Step-Down", "Inpatient", 6),
    (4, "Medical ICU", "Critical Care", 5),
    (5, "Main OR", "Perioperative", 12),
    (6, "PACU", "Perioperative", 18),
    (7, "Primary Care Clinic", "Outpatient", 0),
    (8, "Cardiology Clinic", "Outpatient", 0),
]

PROVIDERS = [
    (1, "Dr. Alicia Moreno", "Emergency Medicine"), (2, "Dr. Kevin Osei", "Emergency Medicine"),
    (3, "Dr. Hannah Brooks", "Hospital Medicine"), (4, "Dr. Samir Patel", "Hospital Medicine"),
    (5, "Dr. Laura Chen", "Cardiology"), (6, "Dr. Marcus Reid", "Cardiology"),
    (7, "Dr. Elena Vasquez", "Critical Care"), (8, "Dr. Robert Klein", "General Surgery"),
    (9, "Dr. Tamara Wells", "Orthopedic Surgery"), (10, "Dr. Jonah Fisher", "Anesthesiology"),
    (11, "Dr. Priya Nair", "Family Medicine"), (12, "Dr. Daniel Ortiz", "Family Medicine"),
]

# code, description, weight, readmit_risk, typical inpatient dept
CONDITIONS = [
    ("I50.9", "Heart failure, unspecified", 8, 0.17, 3),
    ("J44.1", "COPD with acute exacerbation", 7, 0.13, 2),
    ("J18.9", "Pneumonia, unspecified organism", 9, 0.10, 2),
    ("A41.9", "Sepsis, unspecified organism", 4, 0.11, 4),
    ("N17.9", "Acute kidney failure, unspecified", 4, 0.12, 2),
    ("I21.4", "NSTEMI myocardial infarction", 4, 0.14, 3),
    ("E11.65", "Type 2 diabetes with hyperglycemia", 6, 0.09, 2),
    ("K35.80", "Acute appendicitis", 4, 0.03, 2),
    ("M17.11", "Primary osteoarthritis, right knee", 4, 0.03, 2),
    ("S72.001A", "Fracture of right femoral neck", 3, 0.08, 2),
    ("R07.9", "Chest pain, unspecified", 10, 0.04, 1),
    ("N39.0", "Urinary tract infection", 7, 0.05, 1),
]
OUTPATIENT_DX = [("I10", "Essential hypertension"), ("E11.9", "Type 2 diabetes without complications"),
                 ("E78.5", "Hyperlipidemia, unspecified"), ("Z00.00", "Routine adult health exam"),
                 ("I50.9", "Heart failure, unspecified"), ("J44.9", "COPD, unspecified")]

# name, loinc, unit, ref_low, ref_high, normal mean, sd
LABS = [
    ("Hemoglobin", "718-7", "g/dL", 12.0, 17.5, 13.8, 1.8),
    ("White Blood Cell Count", "6690-2", "10*3/uL", 4.0, 11.0, 7.5, 2.8),
    ("Potassium", "2823-3", "mmol/L", 3.5, 5.1, 4.2, 0.5),
    ("Sodium", "2951-2", "mmol/L", 135, 145, 139, 3.5),
    ("Creatinine", "2160-0", "mg/dL", 0.6, 1.3, 1.0, 0.45),
    ("Glucose", "2345-7", "mg/dL", 70, 140, 115, 40),
    ("Troponin I", "10839-9", "ng/mL", 0.0, 0.04, 0.02, 0.05),
    ("BNP", "30934-4", "pg/mL", 0, 100, 80, 160),
    ("Hemoglobin A1c", "4548-4", "%", 4.0, 5.6, 6.2, 1.3),
    ("Lactate", "2524-7", "mmol/L", 0.5, 2.0, 1.4, 0.9),
]
LAB_PANELS = {
    "I50.9": ["BNP", "Potassium", "Sodium", "Creatinine"], "I21.4": ["Troponin I", "Potassium", "Hemoglobin"],
    "A41.9": ["Lactate", "White Blood Cell Count", "Creatinine"], "E11.65": ["Glucose", "Hemoglobin A1c", "Potassium"],
    "N17.9": ["Creatinine", "Potassium", "Sodium"], "R07.9": ["Troponin I", "Hemoglobin"],
}
YOUNG_DX = {"J18.9", "K35.80", "N39.0", "R07.9", "E11.65", "J44.1", "A41.9"}
BASE_LABS = ["Hemoglobin", "White Blood Cell Count", "Sodium", "Potassium", "Glucose"]

MEDS = {
    "I50.9": [("Furosemide", "40 mg", "IV"), ("Carvedilol", "6.25 mg", "PO"), ("Lisinopril", "10 mg", "PO")],
    "J44.1": [("Prednisone", "40 mg", "PO"), ("Albuterol nebulizer", "2.5 mg", "INH"), ("Azithromycin", "500 mg", "PO")],
    "J18.9": [("Ceftriaxone", "1 g", "IV"), ("Azithromycin", "500 mg", "IV")],
    "A41.9": [("Piperacillin-tazobactam", "4.5 g", "IV"), ("Vancomycin", "1250 mg", "IV"), ("Norepinephrine", "8 mcg/min", "IV")],
    "N17.9": [("Sodium chloride 0.9%", "1000 mL", "IV")],
    "I21.4": [("Aspirin", "81 mg", "PO"), ("Heparin", "per protocol", "IV"), ("Atorvastatin", "80 mg", "PO")],
    "E11.65": [("Insulin glargine", "20 units", "SubQ"), ("Insulin lispro", "sliding scale", "SubQ")],
    "K35.80": [("Cefazolin", "2 g", "IV"), ("Hydromorphone", "0.5 mg", "IV")],
    "M17.11": [("Cefazolin", "2 g", "IV"), ("Oxycodone", "5 mg", "PO"), ("Enoxaparin", "40 mg", "SubQ")],
    "S72.001A": [("Cefazolin", "2 g", "IV"), ("Morphine", "2 mg", "IV"), ("Enoxaparin", "40 mg", "SubQ")],
    "R07.9": [("Aspirin", "325 mg", "PO"), ("Nitroglycerin", "0.4 mg", "SL")],
    "N39.0": [("Nitrofurantoin", "100 mg", "PO")],
}
ANESTHESIA_MEDS = [("Propofol", "150 mg", "IV"), ("Fentanyl", "100 mcg", "IV"), ("Ondansetron", "4 mg", "IV")]

# dx code -> (cpt, description, surgeon_id, typical minutes)
SURGERY_FOR = {
    "K35.80": ("44970", "Laparoscopic appendectomy", 8, 55),
    "M17.11": ("27447", "Total knee arthroplasty", 9, 110),
    "S72.001A": ("27236", "Open treatment femoral neck fracture", 9, 95),
}
ELECTIVE = [("47562", "Laparoscopic cholecystectomy", 8, 75), ("49505", "Inguinal hernia repair", 8, 60),
            ("29881", "Knee arthroscopy with meniscectomy", 9, 45), ("27130", "Total hip arthroplasty", 9, 115)]
DISPOSITIONS = [("Home", 70), ("Home with Home Health", 12), ("Skilled Nursing Facility", 9),
                ("Rehab Facility", 4), ("Expired", 1), ("Left Against Medical Advice", 4)]


def wchoice(items, weights):
    return random.choices(items, weights=weights, k=1)[0]


def rand_dt(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))


def fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


class Gen:
    def __init__(self):
        self.rows = {k: [] for k in ["patients", "encounters", "diagnoses", "labs", "medications", "procedures"]}
        self.ids = {k: 0 for k in self.rows}

    def next_id(self, table):
        self.ids[table] += 1
        return self.ids[table]

    def patient(self):
        pid = self.next_id("patients")
        sex = random.choice(["F", "M"])
        age = int(min(95, max(18, random.gauss(58, 18))))
        birth = date(2026, 1, 1) - timedelta(days=age * 365 + random.randint(0, 364))
        city = random.choice(CITIES)
        if age >= 65:
            ins = random.choice(["Medicare", "Medicare", "Medicare Advantage", "Commercial - BCBS"])
        else:
            ins = random.choice([i for i in INSURANCE if not i.startswith("Medicare")])
        self.rows["patients"].append({
            "patient_id": pid, "mrn": f"CC{100000 + pid * 7}",
            "first_name": random.choice(FIRST_F if sex == "F" else FIRST_M), "last_name": random.choice(LAST),
            "birth_date": birth.isoformat(), "sex": sex, "city": city[0], "state": city[1], "zip": city[2],
            "insurance": ins})
        return pid, age

    def add_dx(self, eid, code, desc, primary):
        self.rows["diagnoses"].append({"diagnosis_id": self.next_id("diagnoses"), "encounter_id": eid,
                                       "icd10_code": code, "description": desc, "is_primary": int(primary)})

    def add_lab(self, pid, eid, name, when, abnormal_bias=0.0):
        n, loinc, unit, lo, hi, mean, sd = next(l for l in LABS if l[0] == name)
        if lo < mean < hi:
            val = random.gauss(mean, (hi - lo) / 7)          # mostly within range
        else:
            val = random.gauss(mean, sd)                     # e.g. A1c, already elevated in this population
        if random.random() < abnormal_bias:
            if random.random() < 0.75 or lo == 0:
                val = hi + abs(random.gauss(sd, sd))
            else:
                val = lo * random.uniform(0.6, 0.97)
        val = max(0.0, val)
        val = round(val) if n in ("Sodium", "Glucose", "BNP") else round(val, 2 if n in ("Troponin I", "Creatinine") else 1)
        flag = "H" if val > hi else ("L" if val < lo else "N")
        if flag != "N" and (val > hi * 1.6 or (lo > 0 and val < lo * 0.7)):
            flag = "HH" if val > hi else "LL"
        self.rows["labs"].append({"lab_id": self.next_id("labs"), "encounter_id": eid, "patient_id": pid,
                                  "test_name": n, "loinc_code": loinc, "result_value": val, "unit": unit,
                                  "ref_low": lo, "ref_high": hi, "abnormal_flag": flag, "collected_dt": fmt(when)})

    def add_meds(self, pid, eid, meds, start, stop):
        for name, dose, route in meds:
            self.rows["medications"].append({"medication_id": self.next_id("medications"), "encounter_id": eid,
                                             "patient_id": pid, "medication_name": name, "dose": dose,
                                             "route": route, "start_dt": fmt(start), "stop_dt": fmt(stop)})

    def encounter(self, pid, enc_class, dept, provider, admit, discharge, dx_code, disposition):
        eid = self.next_id("encounters")
        self.rows["encounters"].append({
            "encounter_id": eid, "patient_id": pid, "provider_id": provider, "department_id": dept,
            "encounter_class": enc_class, "admit_dt": fmt(admit), "discharge_dt": fmt(discharge),
            "discharge_disposition": disposition, "primary_dx_code": dx_code})
        return eid

    def surgery(self, pid, eid, cpt, desc, surgeon, minutes, start_dt, age):
        in_room = start_dt
        incision = in_room + timedelta(minutes=random.randint(15, 35))
        close = incision + timedelta(minutes=max(20, int(random.gauss(minutes, minutes * 0.2))))
        out_room = close + timedelta(minutes=random.randint(8, 20))
        asa = 3 if age > 70 else random.choice([1, 2, 2, 2, 3])
        # PACU stay: sicker patients and late-day arrivals (thinner staffing) stay longer
        pacu_min = random.randint(45, 110) + (25 if asa >= 3 else 0) + (30 if out_room.hour >= 16 else 0)
        self.rows["procedures"].append({
            "procedure_id": self.next_id("procedures"), "encounter_id": eid, "patient_id": pid, "cpt_code": cpt,
            "description": desc, "surgeon_id": surgeon, "anesthesiologist_id": 10,
            "or_room": f"OR-{random.randint(1, 8)}", "asa_class": asa, "in_room_dt": fmt(in_room),
            "incision_dt": fmt(incision), "out_room_dt": fmt(out_room),
            "pacu_out_dt": fmt(out_room + timedelta(minutes=pacu_min))})
        self.add_meds(pid, eid, ANESTHESIA_MEDS, in_room, out_room)
        return out_room

    def acute_episode(self, pid, age, when, cond=None):
        """ED visit, possibly admitted; may produce a readmission later."""
        if cond is None:
            pool = CONDITIONS if age >= 50 else [c for c in CONDITIONS if c[0] in YOUNG_DX]
            cond = wchoice(pool, [c[2] for c in pool])
        code, desc, _, readmit_risk, inpt_dept = cond
        ed_arrive = when
        ed_leave = ed_arrive + timedelta(hours=random.uniform(2, 9))
        admitted = code not in ("R07.9", "N39.0") or random.random() < 0.2
        if not admitted:
            eid = self.encounter(pid, "emergency", 1, random.choice([1, 2]), ed_arrive, ed_leave, code, "Home")
            self.add_dx(eid, code, desc, True)
            for lab in LAB_PANELS.get(code, BASE_LABS[:3]):
                self.add_lab(pid, eid, lab, ed_arrive + timedelta(minutes=40), 0.25)
            self.add_meds(pid, eid, MEDS[code][:1], ed_arrive + timedelta(hours=1), ed_leave)
            return ed_leave
        dept = 4 if code == "A41.9" and random.random() < 0.6 else inpt_dept
        if dept == 1:  # admitted from ED for observation
            dept = 3 if code == "R07.9" else 2
        if code in ("R07.9", "N39.0"):                     # observation stay
            discharge = ed_leave + timedelta(hours=random.uniform(18, 40))
        else:
            los_mean = {4: 5.5, 3: 4.2, 2: 3.8}[dept] + (1.5 if age > 75 else 0)
            discharge = ed_leave + timedelta(days=max(1.0, random.gauss(los_mean, 1.8)), hours=random.uniform(0, 6))
        disposition = wchoice([d[0] for d in DISPOSITIONS], [d[1] for d in DISPOSITIONS])
        if age > 78 and random.random() < 0.3:
            disposition = "Skilled Nursing Facility"
        provider = {4: 7, 3: random.choice([5, 6])}.get(dept, random.choice([3, 4]))
        eid = self.encounter(pid, "inpatient", dept, provider, ed_arrive, discharge, code, disposition)
        self.add_dx(eid, code, desc, True)
        if age > 60 and random.random() < 0.5:
            self.add_dx(eid, "I10", "Essential hypertension", False)
        if random.random() < 0.3:
            self.add_dx(eid, "E11.9", "Type 2 diabetes without complications", False)
        for day in range(int((discharge - ed_arrive).days) + 1):
            draw = ed_arrive + timedelta(days=day, hours=random.uniform(4, 7))
            for lab in (LAB_PANELS.get(code, []) + BASE_LABS) if day == 0 else BASE_LABS[:3]:
                self.add_lab(pid, eid, lab, draw, 0.35 if day == 0 else 0.15)
        self.add_meds(pid, eid, MEDS[code], ed_arrive + timedelta(hours=2), discharge)
        if code in SURGERY_FOR:
            cpt, sdesc, surgeon, mins = SURGERY_FOR[code]
            or_start = ed_leave + timedelta(hours=random.uniform(3, 20))
            self.surgery(pid, eid, cpt, sdesc, surgeon, mins, or_start, age)
        end = discharge
        if disposition != "Expired" and random.random() < readmit_risk:
            readmit_at = discharge + timedelta(days=random.uniform(2, 29), hours=random.uniform(0, 12))
            if readmit_at < END:
                end = self.acute_episode(pid, age, readmit_at, cond)
        return end if disposition != "Expired" else None

    def elective_surgery(self, pid, age, when):
        cpt, desc, surgeon, mins = random.choice(ELECTIVE)
        day = when.replace(hour=random.choice([7, 7, 8, 9, 10, 11, 12, 13]), minute=random.choice([0, 15, 30, 45]))
        if day.weekday() >= 5:
            day += timedelta(days=7 - day.weekday())
        eid = self.encounter(pid, "surgical", 5, surgeon, day - timedelta(hours=1.5), day, "", "Home")
        out = self.surgery(pid, eid, cpt, desc, surgeon, mins, day, age)
        stay = timedelta(days=random.choice([1, 2, 3])) if cpt in ("27130",) else timedelta(hours=random.uniform(3, 6))
        disc = out + stay
        self.rows["encounters"][-1]["discharge_dt"] = fmt(disc)
        dx = {"47562": ("K80.20", "Calculus of gallbladder"), "49505": ("K40.90", "Unilateral inguinal hernia"),
              "29881": ("M23.221", "Derangement of meniscus"), "27130": ("M16.11", "Primary osteoarthritis, right hip")}[cpt]
        self.rows["encounters"][-1]["primary_dx_code"] = dx[0]
        self.add_dx(eid, dx[0], dx[1], True)
        self.add_lab(pid, eid, "Hemoglobin", day - timedelta(hours=1), 0.1)
        self.add_lab(pid, eid, "Potassium", day - timedelta(hours=1), 0.1)
        return disc

    def clinic_visit(self, pid, when):
        code, desc = random.choice(OUTPATIENT_DX)
        dept, prov = (8, random.choice([5, 6])) if code == "I50.9" else (7, random.choice([11, 12]))
        start = when.replace(hour=random.randint(8, 16), minute=random.choice([0, 20, 40]))
        eid = self.encounter(pid, "outpatient", dept, prov, start, start + timedelta(minutes=30), code, "Home")
        self.add_dx(eid, code, desc, True)
        if random.random() < 0.6:
            for lab in (["Hemoglobin A1c", "Glucose"] if code.startswith("E11") else ["Sodium", "Potassium", "Creatinine"]):
                self.add_lab(pid, eid, lab, start + timedelta(minutes=10), 0.3)
        return start + timedelta(minutes=30)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patients", type=int, default=2500)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    random.seed(args.seed)
    g = Gen()
    for _ in range(args.patients):
        pid, age = g.patient()
        t = rand_dt(START, START + timedelta(days=90))
        while t and t < END:
            r = random.random()
            if r < 0.45:
                t = g.clinic_visit(pid, t)
            elif r < 0.85:
                t = g.acute_episode(pid, age, t)
            else:
                t = g.elective_surgery(pid, age, t)
            if t:
                t += timedelta(days=random.expovariate(1 / (140 if age >= 65 else 260)))

    DATA_DIR.mkdir(exist_ok=True)
    static = {
        "departments": [dict(zip(["department_id", "name", "unit_type", "bed_count"], d)) for d in DEPARTMENTS],
        "providers": [dict(zip(["provider_id", "name", "specialty"], p)) for p in PROVIDERS],
    }
    for name, rows in {**static, **g.rows}.items():
        with open(DATA_DIR / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"{name:12s} {len(rows):>7,} rows")


if __name__ == "__main__":
    main()
