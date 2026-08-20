from florida_seed.meds import FORMULARY

# Real INNs/brands we must not emit as generic_name.
BLOCKLIST = {
    "levetiracetam", "lamotrigine", "sertraline", "metformin", "lisinopril",
    "atorvastatin", "omeprazole", "gabapentin", "amlodipine", "risperidone",
    "olanzapine", "quetiapine", "aripiprazole", "keppra", "zoloft", "lipitor",
}


def test_catalog_unique():
    codes = [d["code"] for d in FORMULARY]
    names = [d["generic_name"] for d in FORMULARY]
    assert len(codes) == len(set(codes))
    assert len(names) == len(set(names))
    assert len(FORMULARY) >= 30


def test_names_are_invented():
    for d in FORMULARY:
        assert d["generic_name"].lower() not in BLOCKLIST
        assert "TEST" in d["brand_synth"] or "sim" in d["generic_name"] or "-sim" in d["generic_name"] or d["generic_name"].endswith(("ex", "ene", "ane", "one", "ol", "im", "ine"))
        for field in (
            "used_for", "indication", "form", "strength", "route",
            "dose_amount", "frequency", "directions", "warnings",
            "side_effects", "ndc_synth",
        ):
            assert d[field], field
        assert d["ndc_synth"].startswith("99999-")
        assert d["code"].startswith("SYNTH-RX-")


def test_mar_fields_present():
    prn = [d for d in FORMULARY if d["prn"]]
    standing = [d for d in FORMULARY if not d["prn"]]
    assert prn and standing
    for d in standing:
        assert d["scheduled_times"]
    for d in prn:
        assert d["prn_reason"]
