# Radiology Digital Twin Pipeline

A self-contained module that adapts the [Digital-Twin-Simulation](https://github.com/tianyipeng-lab/Digital-Twin-Simulation) pipeline to work with radiology report persona files instead of the original Qualtrics survey dataset.

---

## How it fits into the repo

```
Digital-Twin-Simulation/
├── text_simulation/          ← original pipeline (unchanged)
│   ├── llm_helper.py
│   ├── create_text_simulation_input.py   ← reused as-is (Step 3)
│   ├── text_personas/        ← populated by Step 1
│   ├── text_questions/       ← populated by Step 2
│   ├── text_simulation_input/← populated by Step 3
│   └── radiology_simulation_output/  ← written by Step 4
│
└── radiology_pipeline/       ← THIS MODULE
    ├── prepare_personas.py          Step 1
    ├── generate_questions.py        Step 2
    ├── run_radiology_simulations.py Step 4 (replaces run_LLM_simulations.py)
    ├── postprocess_radiology.py     Step 5
    ├── configs/
    │   └── radiology_config.yaml
    ├── results/                     created at runtime
    │   ├── summary.csv
    │   └── parsed/<pid>_parsed.json
    ├── pid_mapping.csv              created at runtime
    └── run_radiology_pipeline.sh
```

---

## Quick start

### 1. Install dependencies

```bash
cd Digital-Twin-Simulation
poetry install
```

### 2. Set your OpenAI API key

```bash
echo "OPENAI_API_KEY=sk-..." > .env
```

### 3. Convert your PDF reports → persona files

Use the **RadPersona** Streamlit app (`radiology_persona_app/app.py`).

- Upload your PDF radiology reports
- Enable anonymisation if needed
- Download `personas_*.zip` and unzip it somewhere, e.g. `~/my_personas/`
- Keep the `anon_key_*.csv` safe — it maps IDs back to patient names

### 4. Run the pipeline

```bash
chmod +x radiology_pipeline/run_radiology_pipeline.sh

# Test run — 5 patients
./radiology_pipeline/run_radiology_pipeline.sh \
    --personas_dir ~/my_personas \
    --max_personas 5

# Full run — all patients
./radiology_pipeline/run_radiology_pipeline.sh \
    --personas_dir ~/my_personas \
    --max_personas -1 \
    --anon_key ~/anon_key_20251015_1430.csv
```

### 5. View results

| File | Contents |
|------|----------|
| `radiology_pipeline/results/summary.csv` | One row per patient, sorted by triage urgency (most urgent first) |
| `radiology_pipeline/results/parsed/<pid>_parsed.json` | Full structured clinical JSON per patient |
| `text_simulation/radiology_simulation_output/` | Raw LLM response JSONs |

---

## Pipeline steps in detail

| Step | Script | What it does |
|------|--------|-------------|
| 1 | `prepare_personas.py` | Renames `PT-001.txt` → `pid_0001.txt` and writes `pid_mapping.csv` |
| 2 | `generate_questions.py` | Creates a per-patient clinical question prompt file |
| 3 | `create_text_simulation_input.py` | Merges persona + question into a single LLM prompt |
| 4 | `run_radiology_simulations.py` | Calls the LLM, validates JSON responses, retries on failure |
| 5 | `postprocess_radiology.py` | Parses responses → `summary.csv` + per-patient JSON |

---

## Clinical questions asked (full mode)

Each patient's digital twin is asked six questions:

1. **Clinical presentation** — symptoms consistent with the imaging findings
2. **Differential diagnoses** — top 3, ranked with justifications
3. **Management plan** — immediate actions, referrals, investigations, follow-up
4. **Patient explanation** — plain-language summary for the patient
5. **Triage priority** — rated 1 (non-urgent) to 5 (emergency) with justification
6. **Red flags** — features that would change management immediately

Use `--question_set brief` for a shorter 5-field triage-focused output.

---

## Configuration

Edit `radiology_pipeline/configs/radiology_config.yaml` to change:

| Key | Default | Notes |
|-----|---------|-------|
| `model_name` | `gpt-4.1-mini-2025-04-14` | Use `gpt-4.1` for higher accuracy |
| `temperature` | `0.0` | Keep at 0 for consistent clinical output |
| `max_tokens` | `4096` | Sufficient for full 6-question response |
| `num_workers` | `20` | Concurrent API requests — tune to your rate limit |
| `max_retries` | `5` | Retries when JSON validation fails |
| `provider` | `openai` | `openai` or `gemini` |

---

## Re-linking anonymized results to patients

If you anonymized your reports with RadPersona, pass the `--anon_key` flag:

```bash
./radiology_pipeline/run_radiology_pipeline.sh \
    --personas_dir ~/my_personas \
    --anon_key ~/anon_key_20251015_1430.csv
```

The postprocessor will join on `persona_id` and populate the
`original_name` and `hosp_no` columns in `summary.csv`.

---

## Key differences from the original pipeline

| Original pipeline | Radiology pipeline |
|---|---|
| Input: Qualtrics survey JSON | Input: PDF → RadPersona `.txt` files |
| Step 1-2: `convert_persona_to_text.py` + `convert_question_json_to_text.py` | Step 1-2: `prepare_personas.py` + `generate_questions.py` |
| Verification: checks against `answer_blocks` JSON | Verification: validates LLM returned parseable JSON |
| Output: survey responses | Output: structured clinical workup JSON |
| Postprocessing: MAD accuracy evaluation | Postprocessing: triage-sorted clinical summary CSV |
