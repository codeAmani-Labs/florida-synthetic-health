-- Florida synthetic health seed schema.
-- All rows are invented. is_synthetic is always true.

CREATE TABLE IF NOT EXISTS seed_meta (
  id              SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  generator       TEXT NOT NULL,
  seed            INTEGER NOT NULL,
  patients        INTEGER NOT NULL,
  generated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  notes           TEXT NOT NULL DEFAULT 'SYNTHETIC — not PHI, not a real registry'
);

CREATE TABLE IF NOT EXISTS group_homes (
  id              UUID PRIMARY KEY,
  name            TEXT NOT NULL,
  license_no      TEXT NOT NULL UNIQUE,
  city            TEXT NOT NULL,
  county          TEXT NOT NULL,
  zip             TEXT NOT NULL,
  street          TEXT NOT NULL,
  phone           TEXT NOT NULL,
  beds            INTEGER NOT NULL CHECK (beds BETWEEN 2 AND 16),
  is_synthetic    BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS clinics (
  id              UUID PRIMARY KEY,
  name            TEXT NOT NULL,
  specialty       TEXT NOT NULL,
  city            TEXT NOT NULL,
  zip             TEXT NOT NULL,
  street          TEXT NOT NULL,
  phone           TEXT NOT NULL,
  is_synthetic    BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS pharmacies (
  id              UUID PRIMARY KEY,
  name            TEXT NOT NULL,
  npi_synth       TEXT NOT NULL,
  city            TEXT NOT NULL,
  zip             TEXT NOT NULL,
  street          TEXT NOT NULL,
  phone           TEXT NOT NULL,
  is_synthetic    BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS providers (
  id              UUID PRIMARY KEY,
  first_name      TEXT NOT NULL,
  last_name       TEXT NOT NULL,
  credential      TEXT NOT NULL,
  specialty       TEXT NOT NULL,
  npi_synth       TEXT NOT NULL UNIQUE,
  email           TEXT NOT NULL,
  phone           TEXT NOT NULL,
  clinic_id       UUID REFERENCES clinics(id),
  city            TEXT NOT NULL,
  zip             TEXT NOT NULL,
  is_synthetic    BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS patients (
  id              UUID PRIMARY KEY,
  first_name      TEXT NOT NULL,
  last_name       TEXT NOT NULL,
  date_of_birth   DATE NOT NULL,
  sex             TEXT NOT NULL,
  ssn_synth       TEXT NOT NULL,
  medicaid_synth  TEXT NOT NULL UNIQUE,
  street          TEXT NOT NULL,
  city            TEXT NOT NULL,
  zip             TEXT NOT NULL,
  phone           TEXT NOT NULL,
  group_home_id   UUID NOT NULL REFERENCES group_homes(id),
  pharmacy_id     UUID REFERENCES pharmacies(id),
  source          TEXT NOT NULL DEFAULT 'faker',
  is_synthetic    BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS patient_providers (
  patient_id      UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  provider_id     UUID NOT NULL REFERENCES providers(id),
  role            TEXT NOT NULL,
  PRIMARY KEY (patient_id, provider_id, role)
);

CREATE INDEX IF NOT EXISTS idx_patients_home ON patients(group_home_id);
CREATE INDEX IF NOT EXISTS idx_patients_city ON patients(city);
