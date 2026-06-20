"""
postprocess_radiology.py
────────────────────────────────────────────────────────────────
Step 5 of the Radiology Digital Twin pipeline.

Reads every *_response.json file written by run_radiology_simulations.py,
parses the embedded JSON clinical answer, and writes:

  1. radiology_pipeline/results/summary.csv
       One row per patient with all structured fields flattened.

  2. radiology_pipeline/results/<pid>_parsed.json
       Clean, parsed JSON per patient (easier to consume programmatically).

Optionally joins with a PID mapping CSV (from prepare_personas.py) and/or
an anonymization key CSV (from the RadPersona Streamlit app) to restore
original patient identifiers in the summary.

Usage
─────
    python radiology_pipeline/postprocess_radiology.py \
        --simulation_output_dir text_simulation/radiology_simulation_output \
        --results_dir           radiology_pipeline/results \
        [--pid_mapping          radiology_pipeline/pid_mapping.csv] \
        [--anon_key             path/to/anon_key_YYYYMMDD_HHMM.csv]
"""

import os
import re
import sys
import json
import csv
import argparse
from pathlib import Path
from datetime import datetime


# ─── JSON extraction ─────────────────────────────────────────────────────────

def _extract_json(text: str) -> dict | None:
    """
    Robustly extract a JSON object from LLM output that may contain
    markdown fences, preamble, or postamble.
    """
    if not text:
        return None

    # 1. Strip markdown fences
    cleaned = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()

    # 2. Try direct parse
    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return obj
    except (json.JSONDecodeError, ValueError):
        pass

    # 3. Find the first {...} block
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                return obj
        except (json.JSONDecodeError, ValueError):
            pass

    return None


# ─── CSV row builder ─────────────────────────────────────────────────────────

def _flatten_to_row(pid: str, parsed: dict, raw_response: str,
                    pid_map: dict, anon_map: dict) -> dict:
    """Flatten a parsed clinical JSON into a single CSV row."""

    original_file = pid_map.get(pid, {}).get("original_file", "")
    original_name = anon_map.get(pid, {}).get("original_name", "")
    hosp_no       = anon_map.get(pid, {}).get("original_hosp_no", "")

    # ── Clinical presentation ──────────────────────────────────────────────
    cp = parsed.get("clinical_presentation", [])
    if isinstance(cp, list):
        cp_str = " | ".join(cp)
    else:
        cp_str = str(cp)

    # ── Differential diagnoses ────────────────────────────────────────────
    dd = parsed.get("differential_diagnoses", [])
    dd_parts = []
    if isinstance(dd, list):
        for item in dd:
            if isinstance(item, dict):
                dd_parts.append(
                    f"{item.get('rank','?')}. {item.get('diagnosis','?')}"
                    f" – {item.get('justification','')}"
                )
            else:
                dd_parts.append(str(item))
    dd_str = " | ".join(dd_parts) if dd_parts else str(dd)

    # ── Management plan ───────────────────────────────────────────────────
    mp = parsed.get("management_plan", {})
    if isinstance(mp, dict):
        immediate    = mp.get("immediate_actions") or ""
        referrals    = " & ".join(mp.get("specialist_referrals", []) or [])
        investigs    = " & ".join(mp.get("further_investigations", []) or [])
        follow_up    = mp.get("follow_up_timeline", "")
    else:
        immediate = referrals = investigs = follow_up = str(mp)

    # ── Triage ────────────────────────────────────────────────────────────
    triage = parsed.get("triage_priority", {})
    if isinstance(triage, dict):
        triage_rating = triage.get("rating", "")
        triage_just   = triage.get("justification", "")
    elif isinstance(triage, (int, float, str)):
        triage_rating = triage
        triage_just   = ""
    else:
        triage_rating = triage_just = ""

    # ── Red flags ─────────────────────────────────────────────────────────
    rf = parsed.get("red_flags", [])
    if isinstance(rf, list):
        rf_str = " | ".join(rf) if rf else "None identified"
    else:
        rf_str = str(rf)

    # ── Brief-mode fields (question_set=brief) ────────────────────────────
    impression_summary = parsed.get("impression_summary", "")
    recommended_action = parsed.get("recommended_action", "")
    referral_needed    = parsed.get("referral_needed", "")
    referral_specialty = parsed.get("referral_specialty", "")

    return {
        "pid":                  pid,
        "original_file":        original_file,
        "original_name":        original_name,
        "hosp_no":              hosp_no,
        "triage_priority":      triage_rating,
        "triage_justification": triage_just,
        "clinical_presentation":cp_str,
        "differential_diagnoses": dd_str,
        "immediate_actions":    immediate,
        "specialist_referrals": referrals,
        "further_investigations": investigs,
        "follow_up_timeline":   follow_up,
        "patient_explanation":  parsed.get("patient_explanation", ""),
        "red_flags":            rf_str,
        # brief-mode extras
        "impression_summary":   impression_summary,
        "recommended_action":   recommended_action,
        "referral_needed":      referral_needed,
        "referral_specialty":   referral_specialty,
        # meta
        "parse_status":         "ok",
        "raw_response_snippet": (raw_response or "")[:200].replace("\n", " "),
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def postprocess(
    simulation_output_dir: str,
    results_dir: str,
    pid_mapping_csv: str | None = None,
    anon_key_csv: str | None    = None,
) -> None:

    sim_path     = Path(simulation_output_dir)
    results_path = Path(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)
    parsed_dir = results_path / "parsed"
    parsed_dir.mkdir(exist_ok=True)

    # ── Load optional lookup tables ───────────────────────────────────────
    pid_map  = {}   # pid → {original_file, ...}
    anon_map = {}   # pid → {original_name, original_hosp_no, ...}

    if pid_mapping_csv and Path(pid_mapping_csv).exists():
        with open(pid_mapping_csv, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                pid_map[row["pid"]] = row
        print(f"Loaded PID mapping: {len(pid_map)} entries")

    if anon_key_csv and Path(anon_key_csv).exists():
        with open(anon_key_csv, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                anon_map[row["persona_id"]] = row
        print(f"Loaded anonymization key: {len(anon_map)} entries")

    # ── Collect response files ─────────────────────────────────────────────
    response_files = sorted(sim_path.rglob("*_response.json"))
    if not response_files:
        print(f"No *_response.json files found in {simulation_output_dir}")
        return

    print(f"Found {len(response_files)} response files.")

    csv_rows   = []
    ok_count   = 0
    fail_count = 0

    FIELDNAMES = [
        "pid", "original_file", "original_name", "hosp_no",
        "triage_priority", "triage_justification",
        "clinical_presentation", "differential_diagnoses",
        "immediate_actions", "specialist_referrals",
        "further_investigations", "follow_up_timeline",
        "patient_explanation", "red_flags",
        "impression_summary", "recommended_action",
        "referral_needed", "referral_specialty",
        "parse_status", "raw_response_snippet",
    ]

    for rfile in response_files:
        try:
            with open(rfile, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  [skip] Cannot read {rfile}: {e}")
            fail_count += 1
            continue

        pid          = data.get("persona_id", rfile.parent.name)
        raw_response = data.get("response_text", "")
        llm_error    = data.get("llm_call_error")

        if llm_error:
            row = {k: "" for k in FIELDNAMES}
            row.update({"pid": pid, "parse_status": f"llm_error: {llm_error}",
                        "raw_response_snippet": str(llm_error)[:200]})
            csv_rows.append(row)
            fail_count += 1
            continue

        parsed = _extract_json(raw_response)

        if parsed is None:
            row = {k: "" for k in FIELDNAMES}
            row.update({"pid": pid, "parse_status": "json_parse_failed",
                        "raw_response_snippet": (raw_response or "")[:200].replace("\n", " ")})
            csv_rows.append(row)
            fail_count += 1
        else:
            row = _flatten_to_row(pid, parsed, raw_response, pid_map, anon_map)
            csv_rows.append(row)

            # Save per-patient parsed JSON
            parsed_out = parsed_dir / f"{pid}_parsed.json"
            with open(parsed_out, "w", encoding="utf-8") as pf:
                json.dump({"pid": pid, "parsed": parsed,
                           "source_file": str(rfile)}, pf, indent=2)
            ok_count += 1

    # ── Write summary CSV ─────────────────────────────────────────────────
    # Sort by triage_priority descending (most urgent first)
    def triage_sort_key(row):
        try:
            return -int(row.get("triage_priority", 0) or 0)
        except (ValueError, TypeError):
            return 0

    csv_rows.sort(key=triage_sort_key)

    summary_path = results_path / "summary.csv"
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"\nPostprocessing complete.")
    print(f"  ✓ Parsed successfully : {ok_count}")
    print(f"  ✗ Failed / errors     : {fail_count}")
    print(f"  Summary CSV           → {summary_path}")
    print(f"  Per-patient JSON      → {parsed_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Postprocess radiology simulation outputs into a summary CSV."
    )
    parser.add_argument(
        "--simulation_output_dir",
        default="text_simulation/radiology_simulation_output",
        help="Directory containing per-persona output folders from step 4."
    )
    parser.add_argument(
        "--results_dir",
        default="radiology_pipeline/results",
        help="Directory to write the summary CSV and parsed JSONs."
    )
    parser.add_argument(
        "--pid_mapping",
        default=None,
        help="Optional: pid_mapping.csv from prepare_personas.py."
    )
    parser.add_argument(
        "--anon_key",
        default=None,
        help="Optional: anon_key CSV from the RadPersona Streamlit app."
    )
    args = parser.parse_args()
    postprocess(
        simulation_output_dir=args.simulation_output_dir,
        results_dir=args.results_dir,
        pid_mapping_csv=args.pid_mapping,
        anon_key_csv=args.anon_key,
    )
