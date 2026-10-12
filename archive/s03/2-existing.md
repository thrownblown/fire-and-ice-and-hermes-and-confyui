# S03 existing VLM outputs

Do not re-run these. New passes only fill gaps so each shot has 3 constrained runs.

| shot | character_pass (q4, constrained) | composition_pass | stage2 q4 t0.2 | multipass |
|---|---|---|---|---|
| shot:00064 | 2m/0w, 2 described | wide / eye-level / static | yes | q4-t02, q4-t08, f16-t02 |
| shot:00065 | 0m/0w, 0 described | wide / eye-level / static | yes | q4-t02, q4-t08, f16-t02 |
| shot:00066 | 0m/2w, 2 described | medium / eye-level / person in purple robe moving forward | yes | q4-t02 |
| shot:00067 | 0m/1w, 1 described | close-up / eye-level / static | yes | none |
| shot:00068 | 1m/0w, 1 described | close-up / eye-level / static | yes | none |
| shot:00069 | 0m/1w, 1 described | close-up / eye-level / static | yes | none |
| shot:00070 | 1m/0w, 1 described | close-up / eye-level / static | yes | none |
| shot:00071 | 0m/1w, 1 described | close-up / eye-level / static | yes | none |
| shot:00072 | 1m/0w, 1 described | close-up / eye-level / static | yes | none |
| shot:00073 | 3m/1w, 4 described | medium / eye-level / hand gestures changing | yes | none |
| shot:00074 | 1m/1w, 2 described | close-up / eye-level / static | yes | none |
| shot:00075 | 1m/0w, 1 described | close-up / eye-level / static | yes | none |

Prompts:
- character_pass: count, sex, hair, clothing, action. No names. Counts as a constrained run.
- composition_pass: shot size, angle, motion, plus a setting noun. Setting is a location, so it is evidence for CAMERA only, not for the place name.
- stage2 q4 t0.2: the v3 PEOPLE/PERSON/CAMERA/ACTION prompt. Counts as a constrained run.
- multipass: an interrupted extra pass (q4 t0.2, q4 t0.8, f16 t0.2) on the first shots only. Overlaps stage2. Not a new model.

v2 free-form naming pass: not found as a per-shot file for this window. Not voted.
