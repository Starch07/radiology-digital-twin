"""
generate_questions.py
────────────────────────────────────────────────────────────────
Step 2 of the Radiology Digital Twin pipeline.

Reads every pid_XXXX.txt persona file in text_personas/ and writes a
matching pid_XXXX.txt question file in text_questions/.

The question file is the clinical prompt that will be appended to the
persona text and fed to the LLM in Step 4 (run_radiology_simulations.py).

A "question" here is a bundle of clinically relevant tasks that the LLM
should perform *as if it were the digital twin of this specific patient*.

Usage
─────
    python radiology_pipeline/generate_questions.py \
        --persona_dir text_simulation/text_personas \
        --output_dir  text_simulation/text_questions \
        [--question_set full | brief]
"""

import os
import re
import argparse
from pathlib import Path

# ─── Clinical Question Templates ─────────────────────────────────────────────

QUESTION_FULL = """\
You are a clinical expert reviewing the radiology report summarised in the \
Persona Profile above.

Answer ALL of the following questions based ONLY on the information in the \
persona profile. Be precise, evidence-based, and consistent with the findings \
described. Format your response as a valid JSON object with the exact keys shown.

QUESTIONS:

1. CLINICAL_PRESENTATION
   What clinical symptoms and signs is this patient most likely presenting with, \
given the imaging findings? List up to five bullet points.

2. DIFFERENTIAL_DIAGNOSES
   What are the top three differential diagnoses consistent with these findings? \
Rank them by likelihood (most likely first) and give a one-sentence justification \
for each.

3. MANAGEMENT_PLAN
   What is the recommended clinical management for this patient? Include:
   - Immediate actions (if any)
   - Specialist referrals needed
   - Further investigations
   - Follow-up timeline

4. PATIENT_EXPLANATION
   Write a brief explanation of the imaging findings in plain, non-technical \
language suitable for explaining to the patient.

5. TRIAGE_PRIORITY
   Rate the urgency of this case on a scale of 1–5:
     1 = Non-urgent (routine follow-up)
     2 = Routine (outpatient review within weeks)
     3 = Semi-urgent (review within days)
     4 = Urgent (same-day review)
     5 = Emergency (immediate intervention)
   Provide the numeric rating AND a one-sentence justification.

6. RED_FLAGS
   List any specific red-flag features in the report that would change clinical \
management immediately, or state "None identified" if there are no red flags.

REQUIRED OUTPUT FORMAT (JSON only – no markdown fences, no preamble):
{
  "persona_id": "<fill in from persona profile>",
  "clinical_presentation": ["<symptom 1>", "<symptom 2>", ...],
  "differential_diagnoses": [
    {"rank": 1, "diagnosis": "<name>", "justification": "<one sentence>"},
    {"rank": 2, "diagnosis": "<name>", "justification": "<one sentence>"},
    {"rank": 3, "diagnosis": "<name>", "justification": "<one sentence>"}
  ],
  "management_plan": {
    "immediate_actions": "<text or null>",
    "specialist_referrals": ["<referral 1>", ...],
    "further_investigations": ["<investigation 1>", ...],
    "follow_up_timeline": "<text>"
  },
  "patient_explanation": "<plain language paragraph>",
  "triage_priority": {
    "rating": <1-5>,
    "justification": "<one sentence>"
  },
  "red_flags": ["<flag 1>", ...] or "None identified"
}
"""

QUESTION_BRIEF = """\
You are a clinical expert reviewing the radiology report summarised in the \
Persona Profile above.

Answer the following questions based ONLY on the information in that profile. \
Return a valid JSON object with the exact keys shown — no markdown, no preamble.

{
  "persona_id": "<fill in from persona profile>",
  "impression_summary": "<one-sentence plain-language summary of the key finding>",
  "triage_priority": <1-5>,
  "recommended_action": "<single most important next clinical step>",
  "referral_needed": true or false,
  "referral_specialty": "<specialty name or null>"
}
"""

QUESTION_SETS = {
    "full":  QUESTION_FULL,
    "brief": QUESTION_BRIEF,
}


def generate_questions(persona_dir: str, output_dir: str,
                       question_set: str = "full") -> int:
    """
    For every pid_XXXX.txt file in persona_dir, write a matching
    pid_XXXX.txt question file in output_dir.

    Returns the number of question files written.
    """
    persona_path = Path(persona_dir)
    output_path  = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    question_template = QUESTION_SETS.get(question_set, QUESTION_FULL)

    persona_files = sorted(persona_path.glob("*.txt"))
    if not persona_files:
        print(f"[generate_questions] No persona files found in {persona_dir}")
        return 0

    written = 0
    for pf in persona_files:
        # Extract pid from filename (pid_XXXX or any stem)
        pid_match = re.search(r"(pid_\d+)", pf.stem)
        pid       = pid_match.group(1) if pid_match else pf.stem

        # Inject the actual persona_id into the question template
        question_text = question_template.replace(
            '"<fill in from persona profile>"', f'"{pid}"'
        )

        out_file = output_path / f"{pid}.txt"
        out_file.write_text(question_text, encoding="utf-8")
        written += 1

    print(f"[generate_questions] Wrote {written} question files → {output_dir}")
    return written


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate per-patient clinical question prompts."
    )
    parser.add_argument(
        "--persona_dir",
        default="text_simulation/text_personas",
        help="Directory containing pid_XXXX.txt persona files."
    )
    parser.add_argument(
        "--output_dir",
        default="text_simulation/text_questions",
        help="Directory to write question prompt files."
    )
    parser.add_argument(
        "--question_set",
        choices=["full", "brief"],
        default="full",
        help=(
            "'full'  – 6-question clinical workup (default)\n"
            "'brief' – concise 5-field triage summary"
        ),
    )
    args = parser.parse_args()
    generate_questions(args.persona_dir, args.output_dir, args.question_set)
