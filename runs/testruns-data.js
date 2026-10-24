window.TESTDATA = {
 "runs": [
  {
   "id": "T0001",
   "scope": "S03",
   "title": "ref2v, original film stills",
   "question": "Does a straight reference-to-video render of the pilot scene play back at all?",
   "verdict": "decent \u2014 Alex, 2026-09-27",
   "status": "judged",
   "notes": "First scene that played back. 31/31 validator checks passed.",
   "files": [
    "runs/testruns/s03-c01_T0001_t01_00001_.mp4",
    "runs/testruns/s03-c02_T0001_t01_00001_.mp4",
    "runs/testruns/s03-c03_T0001_t01_00001_.mp4"
   ],
   "chunks": {
    "s03-c01": [
     "00067",
     "00068",
     "00069"
    ],
    "s03-c02": [
     "00070",
     "00071",
     "00072"
    ],
    "s03-c03": [
     "00073",
     "00074"
    ]
   }
  },
  {
   "id": "T0002",
   "scope": "S03",
   "title": "ref2v, split at action beats",
   "question": "Same refs and seed as T0001, but chunks cut at action beats instead of even time \u2014 does motion improve?",
   "verdict": "pretty good, on the right track \u2014 Alex, 2026-09-28",
   "status": "judged",
   "notes": "Action-beat chunking adopted as the chunking rule.",
   "files": [
    "runs/T0002_s03_ref2v-actionsplit/output/s03-c01_T0002_t01.mp4",
    "runs/T0002_s03_ref2v-actionsplit/output/s03-c02_T0002_t01.mp4",
    "runs/T0002_s03_ref2v-actionsplit/output/s03-c03_T0002_t01.mp4",
    "runs/T0002_s03_ref2v-actionsplit/output/s03-c04_T0002_t01.mp4",
    "runs/T0002_s03_ref2v-actionsplit/output/s03-c05_T0002_t01.mp4",
    "runs/testruns/s03-c01_T0002_t01_00001_.mp4",
    "runs/testruns/s03-c02_T0002_t01_00001_.mp4",
    "runs/testruns/s03-c03_T0002_t01_00001_.mp4",
    "runs/testruns/s03-c04_T0002_t01_00001_.mp4",
    "runs/testruns/s03-c05_T0002_t01_00001_.mp4"
   ],
   "chunks": {
    "s03-c01": [
     "00067"
    ],
    "s03-c02": [
     "00068",
     "00069"
    ],
    "s03-c03": [
     "00070",
     "00071"
    ],
    "s03-c04": [
     "00072"
    ],
    "s03-c05": [
     "00073",
     "00074"
    ]
   }
  },
  {
   "id": "T0003",
   "scope": "S03",
   "title": "fl2va, first/last source stills",
   "question": "Same chunks and seed as T0002, but generated as first-frame/last-frame video instead of reference-to-video \u2014 does anchoring both ends beat reference mode?",
   "verdict": "awaiting Alex",
   "status": "pending",
   "notes": "This is the mode the full run (fullrun.py) uses.",
   "files": [
    "runs/T0003_s03_fl2va-srcfflf/s03_T0003_stitched.mp4",
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c01_T0003_t01.mp4",
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c02_T0003_t01.mp4",
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c03_T0003_t01.mp4",
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c04_T0003_t01.mp4",
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c05_T0003_t01.mp4",
    "runs/testruns/s03-c01_T0003_t01_00001_.mp4",
    "runs/testruns/s03-c02_T0003_t01_00001_.mp4",
    "runs/testruns/s03-c03_T0003_t01_00001_.mp4",
    "runs/testruns/s03-c04_T0003_t01_00001_.mp4",
    "runs/testruns/s03-c05_T0003_t01_00001_.mp4"
   ],
   "chunks": {
    "s03-c01": [
     "00067"
    ],
    "s03-c02": [
     "00068",
     "00069"
    ],
    "s03-c03": [
     "00070",
     "00071"
    ],
    "s03-c04": [
     "00072"
    ],
    "s03-c05": [
     "00073",
     "00074"
    ]
   }
  },
  {
   "id": "T0004",
   "scope": "S03",
   "title": "fl2va, motion-path variant",
   "question": "Do source-frame deltas (motion path) between the anchor stills drive better motion? Two takes.",
   "verdict": "awaiting Alex",
   "status": "pending",
   "notes": "2 takes rendered.",
   "files": [
    "runs/T0004_s03_fl2va-motionpath/output/s03-c01_T0004_t01.mp4",
    "runs/T0004_s03_fl2va-motionpath/output/s03-c02_T0004_t01.mp4",
    "runs/T0004_s03_fl2va-motionpath/output/s03-c03_T0004_t01.mp4",
    "runs/T0004_s03_fl2va-motionpath/output/s03-c04_T0004_t01.mp4",
    "runs/T0004_s03_fl2va-motionpath/output/s03-c05_T0004_t01.mp4",
    "runs/testruns/s03-c01_T0004_t01_00001_.mp4",
    "runs/testruns/s03-c01_T0004_t01_00002_.mp4",
    "runs/testruns/s03-c02_T0004_t01_00001_.mp4",
    "runs/testruns/s03-c02_T0004_t01_00002_.mp4",
    "runs/testruns/s03-c03_T0004_t01_00001_.mp4",
    "runs/testruns/s03-c03_T0004_t01_00002_.mp4",
    "runs/testruns/s03-c04_T0004_t01_00001_.mp4",
    "runs/testruns/s03-c04_T0004_t01_00002_.mp4",
    "runs/testruns/s03-c05_T0004_t01_00001_.mp4",
    "runs/testruns/s03-c05_T0004_t01_00002_.mp4"
   ],
   "chunks": {
    "s03-c01": [
     "00067"
    ],
    "s03-c02": [
     "00068",
     "00069"
    ],
    "s03-c03": [
     "00070",
     "00071"
    ],
    "s03-c04": [
     "00072"
    ],
    "s03-c05": [
     "00073",
     "00074"
    ]
   }
  },
  {
   "id": "T0005",
   "scope": "S03",
   "title": "fl2va, action variant",
   "question": "Action-oriented prompt variant on the same chunks \u2014 does it help fight/action beats?",
   "verdict": "awaiting Alex",
   "status": "pending",
   "notes": "",
   "files": [
    "runs/testruns/s03-c01_T0005_t01_00001_.mp4",
    "runs/testruns/s03-c02_T0005_t01_00001_.mp4",
    "runs/testruns/s03-c03_T0005_t01_00001_.mp4",
    "runs/testruns/s03-c04_T0005_t01_00001_.mp4",
    "runs/testruns/s03-c05_T0005_t01_00001_.mp4"
   ],
   "chunks": {
    "s03-c01": [
     "00067"
    ],
    "s03-c02": [
     "00068",
     "00069"
    ],
    "s03-c03": [
     "00070",
     "00071"
    ],
    "s03-c04": [
     "00072"
    ],
    "s03-c05": [
     "00073",
     "00074"
    ]
   }
  },
  {
   "id": "T0008",
   "scope": "S03",
   "title": "original audio over T0001 video",
   "question": "Audio plan A baseline: the film's own audio laid over the rendered video at exact source timecodes \u2014 how bad is the lip-sync mismatch really?",
   "verdict": "audition pending",
   "status": "pending",
   "notes": "Free to build, nothing rendered. Per-chunk overlays from audio/master_audio_48k_stereo.wav.",
   "files": [
    "runs/T0008_audio-over-s03/S03-c01_audioA.mp4",
    "runs/T0008_audio-over-s03/S03-c02_audioA.mp4",
    "runs/T0008_audio-over-s03/S03-c03_audioA.mp4"
   ],
   "chunks": {
    "s03-c01": [
     "00067",
     "00068",
     "00069"
    ],
    "s03-c02": [
     "00070",
     "00071",
     "00072"
    ],
    "s03-c03": [
     "00073",
     "00074"
    ]
   }
  },
  {
   "id": "T0009",
   "scope": "S02",
   "title": "continuity packing (glacier chains intact) vs chronological",
   "question": "Do chunk boundaries derived from setup/chain analysis (SSIM) beat strict chronological packing? Variable: boundaries only.",
   "verdict": "renders in flight",
   "status": "running",
   "notes": "Continuity: [16][17,18,19][20,21][22][23,24,25][26,27] vs chronological [16,17,18][19,20,21][22,23,24][25,26,27]. Compare the two audioA files: glacier chains 17->18 and 24->25 should read as continuous motion.",
   "files": [
    "fullrun/stitched/S02_full_t01.mp4",
    "runs/T0009_s02_continuity/S02_chronological_audioA.mp4",
    "runs/T0009_s02_continuity/S02_continuity_audioA.mp4",
    "runs/T0009_s02_continuity/output/S02-k01_full_t01.mp4",
    "runs/T0009_s02_continuity/output/S02-k02_full_t01.mp4",
    "runs/T0009_s02_continuity/output/S02-k03_full_t01.mp4",
    "runs/T0009_s02_continuity/output/S02-k04_full_t01.mp4",
    "runs/T0009_s02_continuity/output/S02-k05_full_t01.mp4",
    "runs/T0009_s02_continuity/output/S02-k06_full_t01.mp4",
    "runs/T0009_s02_continuity/stitched/S02_full_t01.mp4"
   ],
   "chunks": {
    "s02-k01": [
     "00016"
    ],
    "s02-k02": [
     "00017",
     "00018",
     "00019"
    ],
    "s02-k03": [
     "00020",
     "00021"
    ],
    "s02-k04": [
     "00022"
    ],
    "s02-k05": [
     "00023",
     "00024",
     "00025"
    ],
    "s02-k06": [
     "00026",
     "00027"
    ]
   }
  },
  {
   "id": "T0010",
   "scope": "S02",
   "title": "motion-context chaining / bridging",
   "question": "Can a clip be extended by feeding the previous clip's tail back as motion context (chaining/bridging) instead of fresh latents?",
   "verdict": "awaiting Alex",
   "status": "pending",
   "notes": "Skill reference: fni-h3-pipeline references/chaining.md.",
   "files": [
    "runs/T0010_s02_chain/S02_anchored_audioA.mp4",
    "runs/T0010_s02_chain/S02_chain_audioA.mp4",
    "runs/T0010_s02_chain/output/S02-k01_full_t01.mp4",
    "runs/T0010_s02_chain/output/S02-k02_full_t01.mp4",
    "runs/T0010_s02_chain/output/S02-k03_full_t01.mp4",
    "runs/T0010_s02_chain/output/S02-k04_full_t01.mp4",
    "runs/T0010_s02_chain/output/S02-k05_full_t01.mp4",
    "runs/T0010_s02_chain/output/S02-k06_full_t01.mp4",
    "runs/T0010_s02_chain/stitched/S02_full_t01.mp4"
   ],
   "chunks": {}
  },
  {
   "id": "T0011",
   "scope": "S06",
   "title": "setup-ref2va baseline (chronological chunk S06-c01)",
   "question": "Control for the setup experiments: the ordinary chronological chunk (shots 197,198,199) as one reference.",
   "verdict": "awaiting Alex",
   "status": "pending",
   "notes": "",
   "files": [],
   "chunks": {
    "s06-c01": [
     "00197",
     "00198",
     "00199"
    ],
    "setup-s06-a": [
     "00197",
     "00199",
     "00201",
     "00203",
     "00205"
    ],
    "t0013-s06-a-s197": [
     "00197"
    ],
    "t0014-s06-a-s197": [
     "00197"
    ]
   }
  },
  {
   "id": "T0012",
   "scope": "S06",
   "title": "setup-ref2va stitched-video (setup S06-A as one ref)",
   "question": "Re-group by camera angle: concat one setup's shots (A/A/A) into a single reference video instead of a chronological A/B/A mix \u2014 does angle consistency improve the render?",
   "verdict": "awaiting Alex",
   "status": "pending",
   "notes": "Approach X2. See docs/plans/setup-ref2va-tests.md.",
   "files": [],
   "chunks": {
    "s06-c01": [
     "00197",
     "00198",
     "00199"
    ],
    "setup-s06-a": [
     "00197",
     "00199",
     "00201",
     "00203",
     "00205"
    ],
    "t0013-s06-a-s197": [
     "00197"
    ],
    "t0014-s06-a-s197": [
     "00197"
    ]
   }
  },
  {
   "id": "T0013",
   "scope": "S06",
   "title": "setup plate + ONE shot's video",
   "question": "Can a still 'master plate' of the setup stand in for part of the video reference \u2014 plate image + a single shot's clip, to cut the reference-encode cost?",
   "verdict": "awaiting Alex",
   "status": "pending",
   "notes": "Approach X3. Setup plate injected as an extra <Picture> with a background_only retention line.",
   "files": [],
   "chunks": {
    "s06-c01": [
     "00197",
     "00198",
     "00199"
    ],
    "setup-s06-a": [
     "00197",
     "00199",
     "00201",
     "00203",
     "00205"
    ],
    "t0013-s06-a-s197": [
     "00197"
    ],
    "t0014-s06-a-s197": [
     "00197"
    ]
   }
  },
  {
   "id": "T0014",
   "scope": "S06",
   "title": "per-shot + shared plate",
   "question": "Shared setup plate WITHOUT re-grouping: a single shot's video plus the setup's plate image \u2014 is the shared plate alone enough?",
   "verdict": "awaiting Alex",
   "status": "pending",
   "notes": "Approach X4.",
   "files": [],
   "chunks": {
    "s06-c01": [
     "00197",
     "00198",
     "00199"
    ],
    "setup-s06-a": [
     "00197",
     "00199",
     "00201",
     "00203",
     "00205"
    ],
    "t0013-s06-a-s197": [
     "00197"
    ],
    "t0014-s06-a-s197": [
     "00197"
    ]
   }
  },
  {
   "id": "T0015",
   "scope": "S05",
   "title": "Track A ref2va \u2014 technicolor sheets + plate, WITH video ref",
   "question": "With the technicolor character sheets + location plate wired as <Picture> refs, does REF2VA hold the live-action 80s register while the raw 1983 video ref conditions the motion?",
   "verdict": "NEGATIVE \u2014 reads flat 2D rotoscope cel, not live-action (every sampled frame)",
   "status": "judged",
   "notes": "The video reference dominates appearance, so styling only the PICTURE refs is not enough \u2014 the same failure as the FL2VA TEST-1 pinning result, one stage up. Resolved by T0016 (drop the video ref). Driver: runs/build_technicolor_ref2va.py.",
   "files": [
    "runs/T0015_s05_technicolor-sheets-ref2va/output/S05-c01_technicolor_t01_00001_.mp4"
   ],
   "chunks": {
    "s05-c01": [
     "00188",
     "00189"
    ],
    "s05-c02": [
     "00190",
     "00191"
    ],
    "s05-c03": [
     "00192",
     "00193",
     "00194"
    ],
    "s05-c04": [
     "00195",
     "00196"
    ]
   }
  },
  {
   "id": "T0016",
   "scope": "S05",
   "title": "ref2va AUDIO-ONLY (no video ref) + authored blocking + clean plate",
   "question": "Drop the video reference, keep only the source AUDIO (ref_audios + audio_vae): do the technicolor sheets + plate then hold the live-action register, and does an explicit per-chunk blocking line stop H3 inventing a walk-in and a background crowd?",
   "verdict": "register HOLDS \u2014 live-action 80s technicolor; exactly two characters, no background extras, lounging/seated as authored. Residual: a brief mid-clip stand.",
   "status": "judged",
   "notes": "Take ladder on one scene: t01 = walking to camera + crowd; t03 = two people seated (blocking added, but the plate still had painted figures); t04 = clean plate -> exactly two people, no crowd. Per-chunk takes in output/t02, output/t03; the 4x6 seed sweep in output/seedhunt/. Driver: runs/build_technicolor_audio_only.py. Stitched: S05_audioOnly_T0016_t04_stitched.mp4.",
   "files": [
    "runs/T0016_s05_technicolor-audio-only-ref2va/S05_audioOnly_T0016_stitched.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/S05_audioOnly_T0016_t03_stitched.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/S05_audioOnly_T0016_t04_stitched.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/S05-c01_audioOnly_t01_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/S05-c01_audioOnly_t02_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/S05-c02_audioOnly_t01_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/S05-c03_audioOnly_t01_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/S05-c04_audioOnly_t01_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t02/S05-c02_audioOnly_t02_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t02/S05-c03_audioOnly_t02_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t02/S05-c04_audioOnly_t02_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t03/S05-c01_audioOnly_t03_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t03/S05-c02_audioOnly_t03_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t03/S05-c03_audioOnly_t03_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t03/S05-c04_audioOnly_t03_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t04/S05-c01_audioOnly_t04_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t04/S05-c02_audioOnly_t04_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t04/S05-c03_audioOnly_t04_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t04/S05-c04_audioOnly_t04_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c01_audioOnly_t01_s111_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c01_audioOnly_t01_s2222_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c01_audioOnly_t01_s33333_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c01_audioOnly_t01_s444444_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c01_audioOnly_t01_s5555555_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c01_audioOnly_t01_s66666666_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c02_audioOnly_t01_s111_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c02_audioOnly_t01_s2222_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c02_audioOnly_t01_s33333_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c02_audioOnly_t01_s444444_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c02_audioOnly_t01_s5555555_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c02_audioOnly_t01_s66666666_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c03_audioOnly_t01_s111_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c03_audioOnly_t01_s2222_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c03_audioOnly_t01_s33333_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c03_audioOnly_t01_s444444_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c03_audioOnly_t01_s5555555_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c03_audioOnly_t01_s66666666_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c04_audioOnly_t01_s111_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c04_audioOnly_t01_s2222_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c04_audioOnly_t01_s33333_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c04_audioOnly_t01_s444444_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c04_audioOnly_t01_s5555555_00001_.mp4",
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c04_audioOnly_t01_s66666666_00001_.mp4"
   ],
   "chunks": {
    "s05-c01": [
     "00188",
     "00189"
    ],
    "s05-c02": [
     "00190",
     "00191"
    ],
    "s05-c03": [
     "00192",
     "00193",
     "00194"
    ],
    "s05-c04": [
     "00195",
     "00196"
    ]
   }
  },
  {
   "id": "T0017",
   "scope": "S03",
   "title": "audio-only REF2VA \u2014 Ice Peak throne hall (Juliana / Nekron)",
   "question": "Does the audio-only recipe carry to a second scene \u2014 different location plate, different cast \u2014 and land an authored sitting/standing blocking?",
   "verdict": "register holds; two characters; Nekron seated on the ice throne per the authored blocking",
   "status": "judged",
   "notes": "One blurred background figure in frame 1 (that chunk also carries a TEEGRA mis-stamp in the ledger). Driver: runs/build_technicolor_audio_only.py --chunk S03-c01 --subjects JULIANA,NEKRON.",
   "files": [
    "runs/T0017_s03_technicolor-audio-only/S03_audioOnly_stitched.mp4",
    "runs/T0017_s03_technicolor-audio-only/output/S03-c01_audioOnly_t01_00001_.mp4",
    "runs/T0017_s03_technicolor-audio-only/output/S03-c02_audioOnly_t01_00001_.mp4"
   ],
   "chunks": {
    "s03-c01": [
     "00067",
     "00068",
     "00069"
    ],
    "s03-c02": [
     "00070",
     "00071",
     "00072"
    ]
   }
  }
 ]
};
