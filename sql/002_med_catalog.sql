-- Rich fake formulary + MAR-shaped patient meds.
-- Drops the thin v1 medications table.

DROP TABLE IF EXISTS medications CASCADE;

CREATE TABLE IF NOT EXISTS drug_catalog (
  code               TEXT PRIMARY KEY,
  generic_name       TEXT NOT NULL UNIQUE,
  brand_synth        TEXT NOT NULL,
  therapeutic_class  TEXT NOT NULL,
  used_for           TEXT NOT NULL,
  indication         TEXT NOT NULL,
  form               TEXT NOT NULL,
  strength           TEXT NOT NULL,
  strength_unit      TEXT NOT NULL,
  route              TEXT NOT NULL,
  dose_amount        TEXT NOT NULL,
  dose_unit          TEXT NOT NULL,
  frequency          TEXT NOT NULL,
  scheduled_times    TEXT NOT NULL DEFAULT '',
  directions         TEXT NOT NULL,
  warnings           TEXT NOT NULL,
  side_effects       TEXT NOT NULL,
  contraindications  TEXT NOT NULL,
  storage            TEXT NOT NULL,
  prn                BOOLEAN NOT NULL DEFAULT FALSE,
  prn_reason         TEXT NOT NULL DEFAULT '',
  quantity           INTEGER NOT NULL,
  refills            INTEGER NOT NULL,
  ndc_synth          TEXT NOT NULL,
  rx_otc             TEXT NOT NULL,
  is_synthetic       BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE medications (
  id                 UUID PRIMARY KEY,
  patient_id         UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  catalog_code       TEXT NOT NULL REFERENCES drug_catalog(code),
  generic_name       TEXT NOT NULL,
  brand_synth        TEXT NOT NULL,
  therapeutic_class  TEXT NOT NULL,
  used_for           TEXT NOT NULL,
  indication         TEXT NOT NULL,
  form               TEXT NOT NULL,
  strength           TEXT NOT NULL,
  strength_unit      TEXT NOT NULL,
  route              TEXT NOT NULL,
  dose_amount        TEXT NOT NULL,
  dose_unit          TEXT NOT NULL,
  frequency          TEXT NOT NULL,
  scheduled_times    TEXT NOT NULL DEFAULT '',
  directions         TEXT NOT NULL,
  warnings           TEXT NOT NULL,
  side_effects       TEXT NOT NULL,
  contraindications  TEXT NOT NULL,
  storage            TEXT NOT NULL,
  prn                BOOLEAN NOT NULL DEFAULT FALSE,
  prn_reason         TEXT NOT NULL DEFAULT '',
  quantity           INTEGER NOT NULL,
  refills            INTEGER NOT NULL,
  ndc_synth          TEXT NOT NULL,
  rx_otc             TEXT NOT NULL,
  start_date         DATE NOT NULL,
  end_date           DATE,
  prescriber_name    TEXT NOT NULL,
  pharmacy_id        UUID REFERENCES pharmacies(id),
  notes              TEXT NOT NULL DEFAULT '',
  active             BOOLEAN NOT NULL DEFAULT TRUE,
  is_synthetic       BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_meds_patient ON medications(patient_id);
CREATE INDEX IF NOT EXISTS idx_meds_catalog ON medications(catalog_code);
CREATE INDEX IF NOT EXISTS idx_meds_class ON medications(therapeutic_class);
