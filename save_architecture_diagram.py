import os

svg_content = '''<svg width="680" height="720" viewBox="0 0 680 720" xmlns="http://www.w3.org/2000/svg" style="background:white;font-family:Arial,sans-serif">
<defs>
<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
<path d="M2 1L8 5L2 9" fill="none" stroke="#666" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
</marker>
</defs>

<text font-size="15" font-weight="600" x="340" y="28" text-anchor="middle" fill="#222">Radiology Digital Twin Framework - System Architecture</text>

<rect x="220" y="48" width="240" height="56" rx="8" fill="#FAECE7" stroke="#993C1D" stroke-width="0.5"/>
<text font-size="14" font-weight="600" x="340" y="71" text-anchor="middle" dominant-baseline="central" fill="#712B13">Hospital radiology data</text>
<text font-size="12" x="340" y="89" text-anchor="middle" dominant-baseline="central" fill="#993C1D">100 brain MRI PDF reports (Abuja)</text>

<line x1="340" y1="104" x2="340" y2="128" stroke="#666" stroke-width="1.5" marker-end="url(#arrow)"/>

<rect x="180" y="128" width="320" height="56" rx="8" fill="#EEEDFE" stroke="#534AB7" stroke-width="0.5"/>
<text font-size="14" font-weight="600" x="340" y="151" text-anchor="middle" dominant-baseline="central" fill="#3C3489">Stage 1 - RadPersona app</text>
<text font-size="12" x="340" y="169" text-anchor="middle" dominant-baseline="central" fill="#534AB7">Text extraction, anonymization, persona generation</text>

<line x1="340" y1="184" x2="340" y2="208" stroke="#666" stroke-width="1.5" marker-end="url(#arrow)"/>

<rect x="180" y="208" width="320" height="56" rx="8" fill="#EEEDFE" stroke="#534AB7" stroke-width="0.5"/>
<text font-size="14" font-weight="600" x="340" y="231" text-anchor="middle" dominant-baseline="central" fill="#3C3489">Stage 2 - Persona preparation</text>
<text font-size="12" x="340" y="249" text-anchor="middle" dominant-baseline="central" fill="#534AB7">PID mapping, 100 pid_XXXX.txt files created</text>

<line x1="340" y1="264" x2="340" y2="288" stroke="#666" stroke-width="1.5" marker-end="url(#arrow)"/>

<rect x="180" y="288" width="320" height="56" rx="8" fill="#E6F1FB" stroke="#185FA5" stroke-width="0.5"/>
<text font-size="14" font-weight="600" x="340" y="311" text-anchor="middle" dominant-baseline="central" fill="#0C447C">Stage 3 - Question generation</text>
<text font-size="12" x="340" y="329" text-anchor="middle" dominant-baseline="central" fill="#185FA5">6 clinical domains: triage, diagnosis, referrals</text>

<line x1="340" y1="344" x2="340" y2="368" stroke="#666" stroke-width="1.5" marker-end="url(#arrow)"/>

<rect x="180" y="368" width="320" height="56" rx="8" fill="#E6F1FB" stroke="#185FA5" stroke-width="0.5"/>
<text font-size="14" font-weight="600" x="340" y="391" text-anchor="middle" dominant-baseline="central" fill="#0C447C">Stage 4 - Simulation input</text>
<text font-size="12" x="340" y="409" text-anchor="middle" dominant-baseline="central" fill="#185FA5">Persona + questions combined into prompts</text>

<line x1="340" y1="424" x2="340" y2="448" stroke="#666" stroke-width="1.5" marker-end="url(#arrow)"/>

<rect x="160" y="448" width="360" height="56" rx="8" fill="#FAEEDA" stroke="#854F0B" stroke-width="1"/>
<text font-size="14" font-weight="600" x="340" y="471" text-anchor="middle" dominant-baseline="central" fill="#633806">Stage 5 - LLM Simulation (Gemini 2.5 Flash)</text>
<text font-size="12" x="340" y="489" text-anchor="middle" dominant-baseline="central" fill="#854F0B">AI generates clinical assessments for 100 patients</text>

<line x1="340" y1="504" x2="340" y2="528" stroke="#666" stroke-width="1.5" marker-end="url(#arrow)"/>

<rect x="180" y="528" width="320" height="56" rx="8" fill="#E1F5EE" stroke="#0F6E56" stroke-width="0.5"/>
<text font-size="14" font-weight="600" x="340" y="551" text-anchor="middle" dominant-baseline="central" fill="#085041">Stage 6 - Postprocessing</text>
<text font-size="12" x="340" y="569" text-anchor="middle" dominant-baseline="central" fill="#0F6E56">JSON parsing, summary CSV, results compiled</text>

<line x1="340" y1="584" x2="340" y2="608" stroke="#666" stroke-width="1.5" marker-end="url(#arrow)"/>

<rect x="200" y="608" width="280" height="56" rx="8" fill="#E1F5EE" stroke="#0F6E56" stroke-width="0.5"/>
<text font-size="14" font-weight="600" x="340" y="631" text-anchor="middle" dominant-baseline="central" fill="#085041">Results dashboard</text>
<text font-size="12" x="340" y="649" text-anchor="middle" dominant-baseline="central" fill="#0F6E56">Triage charts, referrals, patient table</text>

<rect x="518" y="448" width="144" height="56" rx="8" fill="#FCEBEB" stroke="#A32D2D" stroke-width="0.5"/>
<text font-size="13" font-weight="600" x="590" y="468" text-anchor="middle" dominant-baseline="central" fill="#791F1F">100 patients</text>
<text font-size="11" x="590" y="486" text-anchor="middle" dominant-baseline="central" fill="#A32D2D">100% success rate</text>
<line x1="520" y1="476" x2="500" y2="476" stroke="#999" stroke-width="0.5" stroke-dasharray="3 3"/>

<rect x="518" y="528" width="144" height="56" rx="8" fill="#EAF3DE" stroke="#3B6D11" stroke-width="0.5"/>
<text font-size="13" font-weight="600" x="590" y="548" text-anchor="middle" dominant-baseline="central" fill="#27500A">66 emergency</text>
<text font-size="11" x="590" y="566" text-anchor="middle" dominant-baseline="central" fill="#3B6D11">25 red flags found</text>
<line x1="520" y1="556" x2="500" y2="556" stroke="#999" stroke-width="0.5" stroke-dasharray="3 3"/>
</svg>'''

with open('radiology_pipeline/results/evaluation_plots/architecture_diagram.svg', 'w') as f:
    f.write(svg_content)
print("Architecture diagram saved!")
print("Location: radiology_pipeline/results/evaluation_plots/architecture_diagram.svg")
