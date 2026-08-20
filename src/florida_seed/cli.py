"""CLI: generate Florida synthetic health rows and optionally load Postgres."""

from __future__ import annotations

import argparse
import csv
import os
import sys
import uuid
from pathlib import Path

from faker import Faker

from .geo_fl import CITIES, CLINIC_KINDS, MEDS, SPECIALTIES

ROOT = Path(__file__).resolve().parents[2]


def _ids(rng_seed: int) -> Faker:
    fake = Faker("en_US")
    fake.seed_instance(rng_seed)
    return fake


def synth_ssn(n: int) -> str:
    # SSA does not issue area 666.
    return f"666-{n % 100:02d}-{1000 + (n % 9000):04d}"


def synth_npi(kind: str, n: int) -> str:
    return f"SYNTH-{kind[:3].upper()}-{n:07d}"


def synth_medicaid(n: int) -> str:
    return f"FLTEST{n:08d}"


def pick_city(fake: Faker):
    return fake.random.choice(CITIES)


def generate(seed: int, patients: int, homes: int, clinics: int, pharmacies: int, providers: int):
    fake = _ids(seed)
    homes_n = max(1, homes)
    clinic_rows = []
    pharm_rows = []
    home_rows = []
    prov_rows = []
    patient_rows = []
    link_rows = []
    med_rows = []

    for i in range(clinics):
        city, county, zipc = pick_city(fake)
        kind = fake.random.choice(CLINIC_KINDS)
        clinic_rows.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"clinic-{seed}-{i}")),
            "name": f"{city} {kind} (TEST)",
            "specialty": kind,
            "city": city,
            "zip": zipc,
            "street": fake.street_address(),
            "phone": fake.numerify("407-555-####"),
        })

    for i in range(pharmacies):
        city, county, zipc = pick_city(fake)
        pharm_rows.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"pharm-{seed}-{i}")),
            "name": f"{city} Test Pharmacy {i+1:03d}",
            "npi_synth": synth_npi("org", i + 10_000),
            "city": city,
            "zip": zipc,
            "street": fake.street_address(),
            "phone": fake.numerify("813-555-####"),
        })

    for i in range(homes_n):
        city, county, zipc = pick_city(fake)
        home_rows.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"home-{seed}-{i}")),
            "name": f"{fake.last_name()} Palms Test Home {i+1:04d}",
            "license_no": f"TEST-AHCA-{i+1:05d}",
            "city": city,
            "county": county,
            "zip": zipc,
            "street": fake.street_address(),
            "phone": fake.numerify("850-555-####"),
            "beds": fake.random.randint(4, 12),
        })

    for i in range(providers):
        spec = fake.random.choice(SPECIALTIES)
        city, county, zipc = pick_city(fake)
        clinic = clinic_rows[i % len(clinic_rows)]
        first, last = fake.first_name(), fake.last_name()
        prov_rows.append({
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"prov-{seed}-{i}")),
            "first_name": first,
            "last_name": last,
            "credential": spec[1],
            "specialty": spec[2],
            "npi_synth": synth_npi("ind", i + 1),
            "email": f"{first[0].lower()}.{last.lower()}.{i}@test.invalid",
            "phone": fake.numerify("305-555-####"),
            "clinic_id": clinic["id"],
            "city": city,
            "zip": zipc,
            "role_key": spec[0],
        })

    roles = ["physician", "psychiatrist", "dentist", "neurology", "wsc"]
    by_role = {r: [p for p in prov_rows if p["role_key"] == r] or prov_rows for r in roles}

    for i in range(patients):
        city, county, zipc = pick_city(fake)
        home = home_rows[i % len(home_rows)]
        pharm = pharm_rows[i % len(pharm_rows)]
        dob = fake.date_of_birth(minimum_age=18, maximum_age=90)
        sex = fake.random.choice(["F", "M", "X"])
        first, last = fake.first_name(), fake.last_name()
        pid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"pat-{seed}-{i}"))
        patient_rows.append({
            "id": pid,
            "first_name": first,
            "last_name": last,
            "date_of_birth": dob.isoformat(),
            "sex": sex,
            "ssn_synth": synth_ssn(i),
            "medicaid_synth": synth_medicaid(i),
            "street": fake.street_address(),
            "city": home["city"],
            "zip": home["zip"],
            "phone": fake.numerify("904-555-####"),
            "group_home_id": home["id"],
            "pharmacy_id": pharm["id"],
            "source": "faker",
        })
        for role in roles:
            pool = by_role[role]
            prov = pool[i % len(pool)]
            link_rows.append({
                "patient_id": pid,
                "provider_id": prov["id"],
                "role": role,
            })
        k = 2 + (i % 4)
        for j, med in enumerate(fake.random.sample(MEDS, k=min(k, len(MEDS)))):
            med_rows.append({
                "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"med-{seed}-{i}-{j}")),
                "patient_id": pid,
                "name": med[0],
                "dose": med[1],
                "frequency": med[2],
            })

    return {
        "meta": {"seed": seed, "patients": patients, "generator": "florida-synthetic-health/faker"},
        "clinics": clinic_rows,
        "pharmacies": pharm_rows,
        "group_homes": home_rows,
        "providers": prov_rows,
        "patients": patient_rows,
        "patient_providers": link_rows,
        "medications": med_rows,
    }


def write_csv(bundle: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("group_homes", "clinics", "pharmacies", "providers", "patients", "patient_providers", "medications"):
        rows = bundle[name]
        if not rows:
            continue
        path = out_dir / f"{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for row in rows:
                w.writerow({k: row[k] for k in w.fieldnames})


def load_postgres(bundle: dict, dsn: str) -> None:
    import psycopg
    from psycopg.rows import dict_row

    schema = (ROOT / "sql" / "001_schema.sql").read_text(encoding="utf-8")
    with psycopg.connect(dsn) as conn:
        conn.execute(schema)
        with conn.cursor() as cur:
            cur.execute("TRUNCATE medications, patient_providers, patients, providers, pharmacies, clinics, group_homes, seed_meta CASCADE")
        _copy(conn, "group_homes", bundle["group_homes"], [
            "id", "name", "license_no", "city", "county", "zip", "street", "phone", "beds",
        ])
        _copy(conn, "clinics", bundle["clinics"], [
            "id", "name", "specialty", "city", "zip", "street", "phone",
        ])
        _copy(conn, "pharmacies", bundle["pharmacies"], [
            "id", "name", "npi_synth", "city", "zip", "street", "phone",
        ])
        _copy(conn, "providers", bundle["providers"], [
            "id", "first_name", "last_name", "credential", "specialty", "npi_synth",
            "email", "phone", "clinic_id", "city", "zip",
        ])
        _copy(conn, "patients", bundle["patients"], [
            "id", "first_name", "last_name", "date_of_birth", "sex", "ssn_synth",
            "medicaid_synth", "street", "city", "zip", "phone", "group_home_id",
            "pharmacy_id", "source",
        ])
        _copy(conn, "patient_providers", bundle["patient_providers"], [
            "patient_id", "provider_id", "role",
        ])
        _copy(conn, "medications", bundle["medications"], [
            "id", "patient_id", "name", "dose", "frequency",
        ])
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO seed_meta (id, generator, seed, patients, notes)
                   VALUES (1, %s, %s, %s, %s)
                   ON CONFLICT (id) DO UPDATE SET
                     generator = EXCLUDED.generator,
                     seed = EXCLUDED.seed,
                     patients = EXCLUDED.patients,
                     generated_at = now()""",
                (
                    bundle["meta"]["generator"],
                    bundle["meta"]["seed"],
                    bundle["meta"]["patients"],
                    "SYNTHETIC — not PHI, not a real Florida registry",
                ),
            )
        conn.commit()
        with conn.cursor(row_factory=dict_row) as cur:
            counts = {}
            for table in ("group_homes", "clinics", "pharmacies", "providers", "patients", "medications"):
                cur.execute(f"SELECT count(*) AS n FROM {table}")
                counts[table] = cur.fetchone()["n"]
        print("loaded", counts)


def _copy(conn, table: str, rows: list, cols: list) -> None:
    if not rows:
        return
    from psycopg import sql
    with conn.cursor() as cur:
        with cur.copy(
            sql.SQL("COPY {} ({}) FROM STDIN").format(
                sql.Identifier(table),
                sql.SQL(", ").join(sql.Identifier(c) for c in cols),
            )
        ) as copy:
            for row in rows:
                copy.write_row([row.get(c) for c in cols])


def fetch_synthea_sample(dest: Path) -> Path:
    """Download MITRE's 100-patient CSV sample (Apache-2.0)."""
    import io
    import urllib.request
    import zipfile

    dest.mkdir(parents=True, exist_ok=True)
    url = "https://synthetichealth.github.io/synthea-sample-data/downloads/latest/synthea_sample_data_csv_latest.zip"
    print("fetching Synthea sample CSV (100 patients)…")
    with urllib.request.urlopen(url, timeout=120) as resp:
        blob = resp.read()
    with zipfile.ZipFile(io.BytesIO(blob)) as zf:
        zf.extractall(dest)
    print("extracted to", dest)
    return dest


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Florida synthetic health seeder (not PHI)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("seed", help="Generate Faker rows and optionally load Postgres")
    s.add_argument("--seed", type=int, default=int(os.environ.get("SEED", "42")))
    s.add_argument("--patients", type=int, default=int(os.environ.get("PATIENTS", "10000")))
    s.add_argument("--homes", type=int, default=800)
    s.add_argument("--clinics", type=int, default=400)
    s.add_argument("--pharmacies", type=int, default=300)
    s.add_argument("--providers", type=int, default=2500)
    s.add_argument("--out", type=Path, default=ROOT / "data" / "generated")
    s.add_argument("--load", action="store_true", help="COPY into DATABASE_URL")
    s.add_argument("--csv-only", action="store_true")

    sub.add_parser("fetch-synthea", help="Download MITRE Synthea 100-patient CSV sample")

    args = p.parse_args(argv)
    if args.cmd == "fetch-synthea":
        fetch_synthea_sample(ROOT / "data" / "synthea")
        return 0

    bundle = generate(
        seed=args.seed,
        patients=args.patients,
        homes=args.homes,
        clinics=args.clinics,
        pharmacies=args.pharmacies,
        providers=args.providers,
    )
    print(
        f"generated patients={len(bundle['patients'])} homes={len(bundle['group_homes'])} "
        f"clinics={len(bundle['clinics'])} pharmacies={len(bundle['pharmacies'])} "
        f"providers={len(bundle['providers'])} meds={len(bundle['medications'])}"
    )
    if args.csv_only or not args.load:
        write_csv(bundle, args.out)
        print("csv", args.out)
    if args.load:
        dsn = os.environ.get("DATABASE_URL") or os.environ.get("NEON_SYNTHETIC_DATABASE_URL")
        if not dsn:
            print("DATABASE_URL / NEON_SYNTHETIC_DATABASE_URL is required for --load", file=sys.stderr)
            return 2
        hostish = dsn.split("@")[-1].split("/")[0] if "@" in dsn else "unknown-host"
        print("loading into host", hostish.split(".")[0] + "…")
        if "steep-water-27074984" in dsn or "medtrack" in dsn:
            print("refusing to load into production medtrack", file=sys.stderr)
            return 3
        load_postgres(bundle, dsn)
    return 0
