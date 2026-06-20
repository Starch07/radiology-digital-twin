"""
run_radiology_simulations.py
────────────────────────────────────────────────────────────────
Step 4 of the Radiology Digital Twin pipeline.

Adapted from the upstream run_LLM_simulations.py with two key changes:

  1. The verification callback no longer requires Qualtrics answer_blocks
     JSON files.  Instead it simply confirms that the LLM returned valid
     JSON and that the response file was written successfully.

  2. The persona_id regex accepts any word-token (pid_0001, PT-001, etc.)
     rather than only the strict pid_\\d+ pattern.

Everything else (async batch processing, retries, provider abstraction,
force_regenerate, max_personas) is identical to the upstream module.

Usage
─────
    python radiology_pipeline/run_radiology_simulations.py \
        --config radiology_pipeline/configs/radiology_config.yaml \
        [--max_personas 5]
"""

import os
import sys
import json
import re
import argparse
import asyncio
from datetime import datetime

import yaml
from dotenv import load_dotenv

# Allow importing from the sibling text_simulation package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "text_simulation"))
from llm_helper import LLMConfig, process_prompts_batch  # noqa: E402

load_dotenv()


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_output_path(base_output_dir: str, persona_id: str) -> str:
    folder = os.path.join(base_output_dir, persona_id)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"{persona_id}_response.json")


def _is_valid_json_response(text: str) -> bool:
    """Return True if text contains a parseable JSON object."""
    # Strip optional markdown fences the model may add
    cleaned = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()
    try:
        parsed = json.loads(cleaned)
        return isinstance(parsed, dict)
    except (json.JSONDecodeError, ValueError):
        return False


# ─── Verification callback (radiology-specific) ──────────────────────────────

def radiology_save_and_verify(
    prompt_id: str,
    llm_response_data: dict,
    original_prompt_text: str,
    **kwargs,
) -> bool:
    """
    Save the LLM response to disk and verify it contains valid JSON.

    This replaces the survey-specific postprocess_simulation_outputs_with_pid
    used in the original pipeline.  No answer_blocks files are required.
    """
    base_output_dir = kwargs.get("base_output_dir")
    if not base_output_dir:
        print(f"[verify] ERROR: base_output_dir not supplied for {prompt_id}")
        return False

    output_path = get_output_path(base_output_dir, prompt_id)

    # If the LLM call itself errored, persist the error and return False
    if llm_response_data.get("error"):
        payload = {
            "persona_id":    prompt_id,
            "prompt_text":   original_prompt_text,
            "response_text": "",
            "usage_details": {},
            "llm_call_error": llm_response_data["error"],
        }
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass
        return False

    response_text = llm_response_data.get("response_text", "")

    # Write the response
    payload = {
        "persona_id":    prompt_id,
        "prompt_text":   original_prompt_text,
        "response_text": response_text,
        "usage_details": llm_response_data.get("usage_details", {}),
        "llm_call_error": None,
    }
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        print(f"[verify] ERROR writing {output_path}: {e}")
        return False

    # Verify: the model should have returned a JSON object
    if not _is_valid_json_response(response_text):
        # Will trigger a retry in llm_helper
        return False

    return True


# ─── Main simulation runner ──────────────────────────────────────────────────

async def run_simulations(
    prompts_root_dir: str,
    base_output_dir: str,
    llm_config_params: dict,
    provider: str,
    num_workers: int,
    max_retries: int,
    force_regenerate: bool,
    max_personas: int | None,
) -> None:

    verification_args = {"base_output_dir": base_output_dir}

    llm_config = LLMConfig(
        model_name=llm_config_params["model_name"],
        temperature=llm_config_params.get("temperature", 0.0),
        max_tokens=llm_config_params.get("max_tokens"),
        system_instruction=llm_config_params.get("system_instruction"),
        max_retries=max_retries,
        max_concurrent_requests=num_workers,
        verification_callback=radiology_save_and_verify,
        verification_callback_args=verification_args,
    )

    # ── Collect prompt files ──────────────────────────────────────────────────
    try:
        all_files = sorted(
            f for f in os.listdir(prompts_root_dir) if f.endswith("_prompt.txt")
        )
    except FileNotFoundError:
        print(f"ERROR: Prompts directory not found: {prompts_root_dir}")
        return

    if max_personas and max_personas > 0:
        all_files = all_files[:max_personas]
        print(f"Limiting to {max_personas} prompt files.")

    prompt_infos = []
    for fname in all_files:
        # Accept pid_XXXX or any other prefix
        m = re.search(r"([\w\-]+?)_prompt\.txt$", fname)
        if m:
            prompt_infos.append({
                "persona_id": m.group(1),
                "file_path":  os.path.join(prompts_root_dir, fname),
            })

    if not prompt_infos:
        print(f"No *_prompt.txt files found in {prompts_root_dir}")
        return

    os.makedirs(base_output_dir, exist_ok=True)

    # ── Skip already-verified outputs ────────────────────────────────────────
    prompts_to_run = []
    skipped = 0

    for info in prompt_infos:
        pid   = info["persona_id"]
        opath = get_output_path(base_output_dir, pid)

        if os.path.exists(opath) and not force_regenerate:
            try:
                with open(opath, encoding="utf-8") as f:
                    existing = json.load(f)
                if _is_valid_json_response(existing.get("response_text", "")):
                    skipped += 1
                    continue
            except Exception:
                pass   # Re-run if file is corrupt

        try:
            with open(info["file_path"], encoding="utf-8") as f:
                content = f.read()
            prompts_to_run.append((pid, content))
        except Exception as e:
            print(f"Error reading {info['file_path']}: {e}")

    if skipped:
        print(f"Skipped {skipped} already-processed personas.")
    if not prompts_to_run:
        print("Nothing to process.")
        return

    print(
        f"Processing {len(prompts_to_run)} personas "
        f"({num_workers} concurrent, provider={provider})."
    )

    # ── Run ───────────────────────────────────────────────────────────────────
    results = await process_prompts_batch(
        prompts_to_run,
        llm_config,
        provider,
        desc="Radiology LLM simulation",
    )

    ok = sum(1 for v in results.values() if not v.get("error"))
    fail = len(results) - ok
    print(f"\nDone. ✓ {ok} succeeded  ✗ {fail} failed permanently.")


# ─── CLI entry-point ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run radiology Digital Twin simulations."
    )
    parser.add_argument("--config",       required=True,
                        help="Path to YAML config file.")
    parser.add_argument("--max_personas", type=int, default=None,
                        help="Limit number of personas (overrides config).")
    args = parser.parse_args()

    cfg = load_config(args.config)

    # Resolve directories (relative paths are relative to repo root)
    repo_root = os.path.join(os.path.dirname(__file__), "..")
    prompts_dir = os.path.normpath(
        os.path.join(repo_root, "text_simulation",
                     cfg.get("input_folder_dir", "text_simulation_input"))
    )
    output_dir  = os.path.normpath(
        os.path.join(repo_root, "text_simulation",
                     cfg.get("output_folder_dir", "radiology_simulation_output"))
    )

    provider = "gemini"
    num_workers = cfg.get("num_workers", 5)
    max_retries = cfg.get("max_retries", 3)
    force_regen = cfg.get("force_regenerate", False)
    max_pers    = args.max_personas or cfg.get("max_personas") or None
    if max_pers == -1:
        max_pers = None

    llm_cfg = cfg.get("llm_config", {})
    if "model_name" not in llm_cfg:
        llm_cfg["model_name"] = "gemini-2.5-flash"
    if not llm_cfg.get("model_name"):
        raise ValueError("model_name must be set in the config file.")

    print(f"Radiology simulation started at {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"Provider : {provider}  |  Model: {llm_cfg['model_name']}")
    print(f"Input    : {prompts_dir}")
    print(f"Output   : {output_dir}")

    asyncio.run(
        run_simulations(
            prompts_root_dir=prompts_dir,
            base_output_dir=output_dir,
            llm_config_params=llm_cfg,
            provider=provider,
            num_workers=num_workers,
            max_retries=max_retries,
            force_regenerate=force_regen,
            max_personas=max_pers,
        )
    )
