# Security

This repository ships **synthetic** data only.

- Never open a PR that contains real names, DOBs, SSNs, NPIs, Medicaid IDs, or facility licenses.
- Never point `DATABASE_URL` at a HIPAA production database (for CODEAMANI LABS: not `medtrack`).
- Identifiers use reserved test shapes (`666-xx-xxxx` SSN, `SYNTH-` NPI, `FLTEST` Medicaid, `TEST-AHCA-` licenses).
- Report accidental real-data commits to hq@codeamanilabs.org; we will purge the git object.
