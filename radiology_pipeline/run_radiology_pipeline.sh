#!/usr/bin/env bash
# =============================================================================
# run_radiology_pipeline.sh
# Full end-to-end Radiology Digital Twin pipeline
#
# Usage:
#   ./radiology_pipeline/run_radiology_pipeline.sh \
#       --personas_dir  /path/to/unzipped/personas \
#       [--max_personas 5] \
#       [--question_set full|brief] \
#       [--anon_key     /path/to/anon_key.csv] \
#       [--model        gpt-4.1-mini-2025-04-14]
#
# Prerequisites:
#   • poetry install  (run once from repo root)
#   • .env file in repo root containing OPENAI_API_KEY=...
# =============================================================================

set -euo pipefail

# ─── Defaults ────────────────────────────────────────────────────────────────
PERSONAS_DIR=""
MAX_PERSONAS=5
QUESTION_SET="full"
ANON_KEY=""
MODEL="gpt-4.1-mini-2025-04-14"
CONFIG="radiology_pipeline/configs/radiology_config.yaml"

# ─── Parse arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --personas_dir)  PERSONAS_DIR="$2";  shift 2 ;;
        --max_personas)  MAX_PERSONAS="$2";  shift 2 ;;
        --question_set)  QUESTION_SET="$2";  shift 2 ;;
        --anon_key)      ANON_KEY="$2";      shift 2 ;;
        --model)         MODEL="$2";         shift 2 ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

if [[ -z "$PERSONAS_DIR" ]]; then
    echo "ERROR: --personas_dir is required."
    echo "Usage: $0 --personas_dir /path/to/personas [options]"
    exit 1
fi

# ─── Patch model into config ──────────────────────────────────────────────────
# Works on both macOS (BSD sed) and Linux (GNU sed)
sed -i.bak "s|^model_name:.*|model_name: \"$MODEL\"|" "$CONFIG" && rm -f "${CONFIG}.bak"
sed -i.bak "s|^max_personas:.*|max_personas: $MAX_PERSONAS|" "$CONFIG" && rm -f "${CONFIG}.bak"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         Radiology Digital Twin Pipeline                         ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo "  Personas dir : $PERSONAS_DIR"
echo "  Max personas : $MAX_PERSONAS"
echo "  Question set : $QUESTION_SET"
echo "  Model        : $MODEL"
echo ""

# ─── Step 1: Prepare personas ────────────────────────────────────────────────
echo "[ Step 1 / 5 ]  Preparing persona files..."
poetry run python radiology_pipeline/prepare_personas.py \
    --input_dir   "$PERSONAS_DIR" \
    --output_dir  "text_simulation/text_personas" \
    --mapping_csv "radiology_pipeline/pid_mapping.csv"

# ─── Step 2: Generate question prompts ───────────────────────────────────────
echo ""
echo "[ Step 2 / 5 ]  Generating clinical question files..."
poetry run python radiology_pipeline/generate_questions.py \
    --persona_dir "text_simulation/text_personas" \
    --output_dir  "text_simulation/text_questions" \
    --question_set "$QUESTION_SET"

# ─── Step 3: Combine persona + question into LLM prompts ─────────────────────
echo ""
echo "[ Step 3 / 5 ]  Creating combined simulation input prompts..."
poetry run python text_simulation/create_text_simulation_input.py \
    --persona_text_dir      "text_simulation/text_personas" \
    --question_prompts_dir  "text_simulation/text_questions" \
    --output_combined_prompts_dir "text_simulation/text_simulation_input"

# ─── Step 4: Run LLM simulation ──────────────────────────────────────────────
echo ""
echo "[ Step 4 / 5 ]  Running LLM simulation..."
poetry run python radiology_pipeline/run_radiology_simulations.py \
    --config "$CONFIG" \
    --max_personas "$MAX_PERSONAS"

# ─── Step 5: Postprocess results ─────────────────────────────────────────────
echo ""
echo "[ Step 5 / 5 ]  Postprocessing results..."
ANON_ARG=""
[[ -n "$ANON_KEY" ]] && ANON_ARG="--anon_key $ANON_KEY"

poetry run python radiology_pipeline/postprocess_radiology.py \
    --simulation_output_dir "text_simulation/radiology_simulation_output" \
    --results_dir           "radiology_pipeline/results" \
    --pid_mapping           "radiology_pipeline/pid_mapping.csv" \
    $ANON_ARG

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  Pipeline complete!                                             ║"
echo "║                                                                 ║"
echo "║  Results:                                                       ║"
echo "║    Summary CSV  →  radiology_pipeline/results/summary.csv      ║"
echo "║    Per-patient  →  radiology_pipeline/results/parsed/          ║"
echo "║    Raw output   →  text_simulation/radiology_simulation_output/║"
echo "╚══════════════════════════════════════════════════════════════════╝"
