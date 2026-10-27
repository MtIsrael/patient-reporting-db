-- Patient Data Reporting Database: schema
-- Modeled loosely on how EHR reporting databases (e.g. Epic Clarity) separate
-- patients, encounters, and the clinical events that hang off an encounter.
-- Written for SQLite; uses standard SQL so it ports to PostgreSQL / SQL Server
-- with minor type changes (TEXT datetimes -> TIMESTAMP / DATETIME2).

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS procedures;
DROP TABLE IF EXISTS medications;
DROP TABLE IF EXISTS labs;
DROP TABLE IF EXISTS diagnoses;
DROP TABLE IF EXISTS encounters;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS providers;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    department_id   INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL,
    unit_type       TEXT    NOT NULL,          -- Emergency, Inpatient, Critical Care, Perioperative, Outpatient
    bed_count       INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE providers (
    provider_id     INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    specialty       TEXT NOT NULL
);

CREATE TABLE patients (
    patient_id      INTEGER PRIMARY KEY,
    mrn             TEXT NOT NULL UNIQUE,      -- medical record number
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    birth_date      TEXT NOT NULL,             -- YYYY-MM-DD
    sex             TEXT NOT NULL CHECK (sex IN ('F', 'M')),
    city            TEXT,
    state           TEXT,
    zip             TEXT,
    insurance       TEXT
);

CREATE TABLE encounters (
    encounter_id          INTEGER PRIMARY KEY,
    patient_id            INTEGER NOT NULL REFERENCES patients(patient_id),
    provider_id           INTEGER NOT NULL REFERENCES providers(provider_id),
    department_id         INTEGER NOT NULL REFERENCES departments(department_id),
    encounter_class       TEXT    NOT NULL CHECK (encounter_class IN ('inpatient', 'emergency', 'outpatient', 'surgical')),
    admit_dt              TEXT    NOT NULL,
    discharge_dt          TEXT    NOT NULL,
    discharge_disposition TEXT,
    primary_dx_code       TEXT
);

CREATE TABLE diagnoses (
    diagnosis_id    INTEGER PRIMARY KEY,
    encounter_id    INTEGER NOT NULL REFERENCES encounters(encounter_id),
    icd10_code      TEXT    NOT NULL,
    description     TEXT    NOT NULL,
    is_primary      INTEGER NOT NULL CHECK (is_primary IN (0, 1))
);

CREATE TABLE labs (
    lab_id          INTEGER PRIMARY KEY,
    encounter_id    INTEGER NOT NULL REFERENCES encounters(encounter_id),
    patient_id      INTEGER NOT NULL REFERENCES patients(patient_id),
    test_name       TEXT    NOT NULL,
    loinc_code      TEXT    NOT NULL,
    result_value    REAL    NOT NULL,
    unit            TEXT,
    ref_low         REAL,
    ref_high        REAL,
    abnormal_flag   TEXT    NOT NULL CHECK (abnormal_flag IN ('N', 'H', 'L', 'HH', 'LL')),  -- HH/LL = critical
    collected_dt    TEXT    NOT NULL
);

CREATE TABLE medications (
    medication_id   INTEGER PRIMARY KEY,
    encounter_id    INTEGER NOT NULL REFERENCES encounters(encounter_id),
    patient_id      INTEGER NOT NULL REFERENCES patients(patient_id),
    medication_name TEXT    NOT NULL,
    dose            TEXT,
    route           TEXT,
    start_dt        TEXT    NOT NULL,
    stop_dt         TEXT
);

CREATE TABLE procedures (
    procedure_id        INTEGER PRIMARY KEY,
    encounter_id        INTEGER NOT NULL REFERENCES encounters(encounter_id),
    patient_id          INTEGER NOT NULL REFERENCES patients(patient_id),
    cpt_code            TEXT    NOT NULL,
    description         TEXT    NOT NULL,
    surgeon_id          INTEGER REFERENCES providers(provider_id),
    anesthesiologist_id INTEGER REFERENCES providers(provider_id),
    or_room             TEXT,
    asa_class           INTEGER CHECK (asa_class BETWEEN 1 AND 6),
    in_room_dt          TEXT,
    incision_dt         TEXT,
    out_room_dt         TEXT,
    pacu_out_dt         TEXT
);

-- Indexes on the columns reports filter and join on most
CREATE INDEX ix_enc_patient   ON encounters (patient_id, admit_dt);
CREATE INDEX ix_enc_dept      ON encounters (department_id, admit_dt);
CREATE INDEX ix_dx_encounter  ON diagnoses  (encounter_id);
CREATE INDEX ix_labs_patient  ON labs       (patient_id, collected_dt);
CREATE INDEX ix_labs_flag     ON labs       (abnormal_flag);
CREATE INDEX ix_meds_enc      ON medications(encounter_id);
CREATE INDEX ix_proc_enc      ON procedures (encounter_id);
