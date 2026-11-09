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
   },
   "clipmeta": {
    "runs/testruns/s03-c01_T0001_t01_00001_.mp4": {},
    "runs/testruns/s03-c02_T0001_t01_00001_.mp4": {},
    "runs/testruns/s03-c03_T0001_t01_00001_.mp4": {}
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
   },
   "clipmeta": {
    "runs/T0002_s03_ref2v-actionsplit/output/s03-c01_T0002_t01.mp4": {},
    "runs/T0002_s03_ref2v-actionsplit/output/s03-c02_T0002_t01.mp4": {},
    "runs/T0002_s03_ref2v-actionsplit/output/s03-c03_T0002_t01.mp4": {},
    "runs/T0002_s03_ref2v-actionsplit/output/s03-c04_T0002_t01.mp4": {},
    "runs/T0002_s03_ref2v-actionsplit/output/s03-c05_T0002_t01.mp4": {},
    "runs/testruns/s03-c01_T0002_t01_00001_.mp4": {},
    "runs/testruns/s03-c02_T0002_t01_00001_.mp4": {},
    "runs/testruns/s03-c03_T0002_t01_00001_.mp4": {},
    "runs/testruns/s03-c04_T0002_t01_00001_.mp4": {},
    "runs/testruns/s03-c05_T0002_t01_00001_.mp4": {}
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
   },
   "clipmeta": {
    "runs/T0003_s03_fl2va-srcfflf/s03_T0003_stitched.mp4": {},
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c01_T0003_t01.mp4": {},
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c02_T0003_t01.mp4": {},
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c03_T0003_t01.mp4": {},
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c04_T0003_t01.mp4": {},
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c05_T0003_t01.mp4": {},
    "runs/testruns/s03-c01_T0003_t01_00001_.mp4": {},
    "runs/testruns/s03-c02_T0003_t01_00001_.mp4": {},
    "runs/testruns/s03-c03_T0003_t01_00001_.mp4": {},
    "runs/testruns/s03-c04_T0003_t01_00001_.mp4": {},
    "runs/testruns/s03-c05_T0003_t01_00001_.mp4": {}
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
   },
   "clipmeta": {
    "runs/T0004_s03_fl2va-motionpath/output/s03-c01_T0004_t01.mp4": {},
    "runs/T0004_s03_fl2va-motionpath/output/s03-c02_T0004_t01.mp4": {},
    "runs/T0004_s03_fl2va-motionpath/output/s03-c03_T0004_t01.mp4": {},
    "runs/T0004_s03_fl2va-motionpath/output/s03-c04_T0004_t01.mp4": {},
    "runs/T0004_s03_fl2va-motionpath/output/s03-c05_T0004_t01.mp4": {},
    "runs/testruns/s03-c01_T0004_t01_00001_.mp4": {},
    "runs/testruns/s03-c01_T0004_t01_00002_.mp4": {},
    "runs/testruns/s03-c02_T0004_t01_00001_.mp4": {},
    "runs/testruns/s03-c02_T0004_t01_00002_.mp4": {},
    "runs/testruns/s03-c03_T0004_t01_00001_.mp4": {},
    "runs/testruns/s03-c03_T0004_t01_00002_.mp4": {},
    "runs/testruns/s03-c04_T0004_t01_00001_.mp4": {},
    "runs/testruns/s03-c04_T0004_t01_00002_.mp4": {},
    "runs/testruns/s03-c05_T0004_t01_00001_.mp4": {},
    "runs/testruns/s03-c05_T0004_t01_00002_.mp4": {}
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
   },
   "clipmeta": {
    "runs/testruns/s03-c01_T0005_t01_00001_.mp4": {},
    "runs/testruns/s03-c02_T0005_t01_00001_.mp4": {},
    "runs/testruns/s03-c03_T0005_t01_00001_.mp4": {},
    "runs/testruns/s03-c04_T0005_t01_00001_.mp4": {},
    "runs/testruns/s03-c05_T0005_t01_00001_.mp4": {}
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
   },
   "clipmeta": {
    "runs/T0008_audio-over-s03/S03-c01_audioA.mp4": {},
    "runs/T0008_audio-over-s03/S03-c02_audioA.mp4": {},
    "runs/T0008_audio-over-s03/S03-c03_audioA.mp4": {}
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
   },
   "clipmeta": {
    "fullrun/stitched/S02_full_t01.mp4": {},
    "runs/T0009_s02_continuity/S02_chronological_audioA.mp4": {},
    "runs/T0009_s02_continuity/S02_continuity_audioA.mp4": {},
    "runs/T0009_s02_continuity/output/S02-k01_full_t01.mp4": {
     "take": "01",
     "chunk": "S02-k01",
     "warning": "no graph or prompt file found for this take"
    },
    "runs/T0009_s02_continuity/output/S02-k02_full_t01.mp4": {
     "take": "01",
     "chunk": "S02-k02",
     "warning": "no graph or prompt file found for this take"
    },
    "runs/T0009_s02_continuity/output/S02-k03_full_t01.mp4": {
     "take": "01",
     "chunk": "S02-k03",
     "warning": "no graph or prompt file found for this take"
    },
    "runs/T0009_s02_continuity/output/S02-k04_full_t01.mp4": {
     "take": "01",
     "chunk": "S02-k04",
     "warning": "no graph or prompt file found for this take"
    },
    "runs/T0009_s02_continuity/output/S02-k05_full_t01.mp4": {
     "take": "01",
     "chunk": "S02-k05",
     "warning": "no graph or prompt file found for this take"
    },
    "runs/T0009_s02_continuity/output/S02-k06_full_t01.mp4": {
     "take": "01",
     "chunk": "S02-k06",
     "warning": "no graph or prompt file found for this take"
    },
    "runs/T0009_s02_continuity/stitched/S02_full_t01.mp4": {}
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
   "chunks": {},
   "clipmeta": {
    "runs/T0010_s02_chain/S02_anchored_audioA.mp4": {},
    "runs/T0010_s02_chain/S02_chain_audioA.mp4": {},
    "runs/T0010_s02_chain/output/S02-k01_full_t01.mp4": {
     "take": "01",
     "chunk": "S02-k01",
     "warning": "no graph or prompt file found for this take"
    },
    "runs/T0010_s02_chain/output/S02-k02_full_t01.mp4": {
     "take": "01",
     "chunk": "S02-k02",
     "warning": "no graph or prompt file found for this take"
    },
    "runs/T0010_s02_chain/output/S02-k03_full_t01.mp4": {
     "take": "01",
     "chunk": "S02-k03",
     "warning": "no graph or prompt file found for this take"
    },
    "runs/T0010_s02_chain/output/S02-k04_full_t01.mp4": {
     "take": "01",
     "chunk": "S02-k04",
     "warning": "no graph or prompt file found for this take"
    },
    "runs/T0010_s02_chain/output/S02-k05_full_t01.mp4": {
     "take": "01",
     "chunk": "S02-k05",
     "warning": "no graph or prompt file found for this take"
    },
    "runs/T0010_s02_chain/output/S02-k06_full_t01.mp4": {
     "take": "01",
     "chunk": "S02-k06",
     "warning": "no graph or prompt file found for this take"
    },
    "runs/T0010_s02_chain/stitched/S02_full_t01.mp4": {}
   }
  },
  {
   "id": "T0011",
   "scope": "S06",
   "title": "setup-ref2va baseline (chronological chunk S06-c01)",
   "question": "Control for the setup experiments: the ordinary chronological chunk (shots 197,198,199) as one reference.",
   "verdict": "awaiting Alex",
   "status": "pending",
   "notes": "",
   "files": [
    "runs/T0011_T0012_setup_ref2va/S06-c01_ref_t01_00001_.mp4",
    "runs/T0011_T0012_setup_ref2va/setup-S06-A_ref_t01_00001_.mp4"
   ],
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
   },
   "clipmeta": {
    "runs/T0011_T0012_setup_ref2va/S06-c01_ref_t01_00001_.mp4": {
     "prompt": "How the reference pictures align with the target video \u2014 Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot 3) aligns with the 9.42-second mark of the target video.\n\nintegrated_multimodal_description: [Shot 1] 2D-animated rotoscope painted animation in the style of a 1983 fantasy film: inked figures over cool-toned painted stone interiors, cold blue-grey cavern light. The opening frame matches <Picture 1>: In a cavernous, dimly lit space with red-hued rock formations and glowing embers, three figures in dark blue hooded robes stand facing forward. The camera stays low and tilts up slightly as the figure moves. The camera pulls out with small amplitude at slow speed, opening the space around the figures. On screen: large, white, light, dark red tunic and pants; slender, long dark, light, white top and light-colored pants; tall thin, hidden by hood, dark, blue robe with hood. a hooded subhuman envoy in a dark robe with yellow eyes and dark skin (S1) speaks while off-screen: <d>[English] If you peacefully surrender, my lord Nekron will cease the destruction of-</d> He shifts his weight, turns his shoulders, and brings one arm up across his chest before letting it fall. [Shot 2] At 00:03.337, the camera cuts to a new angle. The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen: large and muscular, bald, light brown, red sleeveless tunic with gold circular necklace and large gold hoop earring. a young prince with dark hair, in Fire Keep dress with a high collar (S2) says: <d>[English] This is your message of peace?</d> He steps forward, lifts a hand toward the figure before him, and holds it out while his head turns to follow. [Shot 3] At 00:05.714, the camera cuts to a new angle. The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. On screen: muscular, black, shoulder-length, light brown, red sleeveless top, red loincloth with gold studs, red boots; muscular, bald, light brown, red sleeveless top with gold necklace, red shorts, gold armbands, red boots; slender, hidden under purple hood, light brown, purple hooded robe. a young prince with dark hair, in Fire Keep dress with a high collar (S2) speaks while off-screen: <d>[English] A demand for our total and unconditional surrender?</d> He shifts his weight, turns his shoulders, and brings one arm up across his chest before letting it fall. Only in the last seconds do these movements slow and stop, and the figure comes to rest in the pose, spacing, framing, and lighting established by <Picture 2>.\n\noverall_soundscape: Room reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\nnon_diegetic_music: Low sustained strings at a slow tempo with widely spaced woodwind notes, dynamics held quiet throughout.",
     "prompt_source": "fullrun/graphs/S06-c01.json",
     "take": "01",
     "chunk": "S06-c01"
    },
    "runs/T0011_T0012_setup_ref2va/setup-S06-A_ref_t01_00001_.mp4": {}
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
   },
   "clipmeta": {}
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
   },
   "clipmeta": {}
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
   },
   "clipmeta": {}
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
   },
   "clipmeta": {
    "runs/T0015_s05_technicolor-sheets-ref2va/output/S05-c01_technicolor_t01_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra sits low and lounges back on a cushioned couch, relaxed and listening; Tutor stands beside her, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pulls out with small amplitude at slow speed, opening the space around the figures.\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] All matter in our world is from the natural bases...</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c01.json",
     "take": "01",
     "chunk": "S05-c01"
    }
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
   },
   "clipmeta": {
    "runs/T0016_s05_technicolor-audio-only-ref2va/S05_audioOnly_T0016_stitched.mp4": {},
    "runs/T0016_s05_technicolor-audio-only-ref2va/S05_audioOnly_T0016_t03_stitched.mp4": {},
    "runs/T0016_s05_technicolor-audio-only-ref2va/S05_audioOnly_T0016_t04_stitched.mp4": {},
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/S05-c01_audioOnly_t01_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra sits low and lounges back on a cushioned couch, relaxed and listening; Tutor stands beside her, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pulls out with small amplitude at slow speed, opening the space around the figures.\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] All matter in our world is from the natural bases...</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c01_audioOnly_t01.json",
     "take": "01",
     "chunk": "S05-c01"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/S05-c01_audioOnly_t02_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra sits low and lounges back on a cushioned couch, relaxed and listening; Tutor stands beside her, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pulls out with small amplitude at slow speed, opening the space around the figures.\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] All matter in our world is from the natural bases...</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c01.json",
     "take": "02",
     "chunk": "S05-c01"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/S05-c02_audioOnly_t01_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on the cushioned couch, relaxed, reading; Tutor stands beside her with one arm raised, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pulls out with small amplitude at slow speed, opening the space around the figures. <Subject 1> (S1) says: <d>[English] which are earth, air, fire and water...</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] the four elements from which all things are created.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c02.json",
     "take": "01",
     "chunk": "S05-c02"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/S05-c03_audioOnly_t01_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n<Subject 2> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on a chaise lounge, relaxed and at ease; Tutor sits facing her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] How can you talk about elements when the war draws nearer to us every hour?</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] Princess Teegra, we all have our duty.</d> <Subject 2> (S2) says: <d>[English] Your father's duty is to be king and lead.</d>\n\n[Shot 3] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 2> (S2) says: <d>[English] Your brother's duty is to soldier. And your duty is to learn.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c03.json",
     "take": "01",
     "chunk": "S05-c03"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/S05-c04_audioOnly_t01_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 2>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra lies back on the couch with her arms stretched above her head, entirely relaxed; Tutor sits in profile beside her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face.\n\n[Shot 2] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] You mean my duty is to stay shut up...</d> <Subject 1> (S1) says: <d>[English] while all the men do the fighting and share all the glory.</d> <Subject 1> (S1) says: <d>[English] We think that stinks.</d> <Subject 1> (S1) says: <d>[English] Don't we, Shaitan?</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c04.json",
     "take": "01",
     "chunk": "S05-c04"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t02/S05-c02_audioOnly_t02_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on the cushioned couch, relaxed, reading; Tutor stands beside her with one arm raised, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pulls out with small amplitude at slow speed, opening the space around the figures. <Subject 1> (S1) says: <d>[English] which are earth, air, fire and water...</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] the four elements from which all things are created.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c02.json",
     "take": "02",
     "chunk": "S05-c02"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t02/S05-c03_audioOnly_t02_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n<Subject 2> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on a chaise lounge, relaxed and at ease; Tutor sits facing her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] How can you talk about elements when the war draws nearer to us every hour?</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] Princess Teegra, we all have our duty.</d> <Subject 2> (S2) says: <d>[English] Your father's duty is to be king and lead.</d>\n\n[Shot 3] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 2> (S2) says: <d>[English] Your brother's duty is to soldier. And your duty is to learn.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c03.json",
     "take": "02",
     "chunk": "S05-c03"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t02/S05-c04_audioOnly_t02_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 2>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra lies back on the couch with her arms stretched above her head, entirely relaxed; Tutor sits in profile beside her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face.\n\n[Shot 2] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] You mean my duty is to stay shut up...</d> <Subject 1> (S1) says: <d>[English] while all the men do the fighting and share all the glory.</d> <Subject 1> (S1) says: <d>[English] We think that stinks.</d> <Subject 1> (S1) says: <d>[English] Don't we, Shaitan?</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c04.json",
     "take": "02",
     "chunk": "S05-c04"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t03/S05-c01_audioOnly_t03_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra sits low and lounges back on a cushioned couch, relaxed and listening; Tutor stands beside her, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pulls out with small amplitude at slow speed, opening the space around the figures.\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] All matter in our world is from the natural bases...</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c01.json",
     "take": "03",
     "chunk": "S05-c01"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t03/S05-c02_audioOnly_t03_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on the cushioned couch, relaxed, reading; Tutor stands beside her with one arm raised, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pulls out with small amplitude at slow speed, opening the space around the figures. <Subject 1> (S1) says: <d>[English] which are earth, air, fire and water...</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] the four elements from which all things are created.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c02.json",
     "take": "03",
     "chunk": "S05-c02"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t03/S05-c03_audioOnly_t03_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n<Subject 2> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on a chaise lounge, relaxed and at ease; Tutor sits facing her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] How can you talk about elements when the war draws nearer to us every hour?</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] Princess Teegra, we all have our duty.</d> <Subject 2> (S2) says: <d>[English] Your father's duty is to be king and lead.</d>\n\n[Shot 3] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 2> (S2) says: <d>[English] Your brother's duty is to soldier. And your duty is to learn.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c03.json",
     "take": "03",
     "chunk": "S05-c03"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t03/S05-c04_audioOnly_t03_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 2>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra lies back on the couch with her arms stretched above her head, entirely relaxed; Tutor sits in profile beside her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face.\n\n[Shot 2] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] You mean my duty is to stay shut up...</d> <Subject 1> (S1) says: <d>[English] while all the men do the fighting and share all the glory.</d> <Subject 1> (S1) says: <d>[English] We think that stinks.</d> <Subject 1> (S1) says: <d>[English] Don't we, Shaitan?</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c04.json",
     "take": "03",
     "chunk": "S05-c04"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t04/S05-c01_audioOnly_t04_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra sits low and lounges back on a cushioned couch, relaxed and listening; Tutor stands beside her, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pulls out with small amplitude at slow speed, opening the space around the figures.\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] All matter in our world is from the natural bases...</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c01.json",
     "take": "04",
     "chunk": "S05-c01"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t04/S05-c02_audioOnly_t04_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on the cushioned couch, relaxed, reading; Tutor stands beside her with one arm raised, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pulls out with small amplitude at slow speed, opening the space around the figures. <Subject 1> (S1) says: <d>[English] which are earth, air, fire and water...</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] the four elements from which all things are created.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c02.json",
     "take": "04",
     "chunk": "S05-c02"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t04/S05-c03_audioOnly_t04_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n<Subject 2> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on a chaise lounge, relaxed and at ease; Tutor sits facing her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] How can you talk about elements when the war draws nearer to us every hour?</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] Princess Teegra, we all have our duty.</d> <Subject 2> (S2) says: <d>[English] Your father's duty is to be king and lead.</d>\n\n[Shot 3] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 2> (S2) says: <d>[English] Your brother's duty is to soldier. And your duty is to learn.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c03.json",
     "take": "04",
     "chunk": "S05-c03"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/t04/S05-c04_audioOnly_t04_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 2>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra lies back on the couch with her arms stretched above her head, entirely relaxed; Tutor sits in profile beside her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face.\n\n[Shot 2] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] You mean my duty is to stay shut up...</d> <Subject 1> (S1) says: <d>[English] while all the men do the fighting and share all the glory.</d> <Subject 1> (S1) says: <d>[English] We think that stinks.</d> <Subject 1> (S1) says: <d>[English] Don't we, Shaitan?</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c04.json",
     "take": "04",
     "chunk": "S05-c04"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c01_audioOnly_t01_s111_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra sits low and lounges back on a cushioned couch, relaxed and listening; Tutor stands beside her, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pulls out with small amplitude at slow speed, opening the space around the figures.\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] All matter in our world is from the natural bases...</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c01_audioOnly_t01.json",
     "take": "01",
     "chunk": "S05-c01"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c01_audioOnly_t01_s2222_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra sits low and lounges back on a cushioned couch, relaxed and listening; Tutor stands beside her, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pulls out with small amplitude at slow speed, opening the space around the figures.\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] All matter in our world is from the natural bases...</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c01_audioOnly_t01.json",
     "take": "01",
     "chunk": "S05-c01"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c01_audioOnly_t01_s33333_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra sits low and lounges back on a cushioned couch, relaxed and listening; Tutor stands beside her, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pulls out with small amplitude at slow speed, opening the space around the figures.\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] All matter in our world is from the natural bases...</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c01_audioOnly_t01.json",
     "take": "01",
     "chunk": "S05-c01"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c01_audioOnly_t01_s444444_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra sits low and lounges back on a cushioned couch, relaxed and listening; Tutor stands beside her, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pulls out with small amplitude at slow speed, opening the space around the figures.\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] All matter in our world is from the natural bases...</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c01_audioOnly_t01.json",
     "take": "01",
     "chunk": "S05-c01"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c01_audioOnly_t01_s5555555_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra sits low and lounges back on a cushioned couch, relaxed and listening; Tutor stands beside her, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pulls out with small amplitude at slow speed, opening the space around the figures.\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] All matter in our world is from the natural bases...</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c01_audioOnly_t01.json",
     "take": "01",
     "chunk": "S05-c01"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c01_audioOnly_t01_s66666666_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra sits low and lounges back on a cushioned couch, relaxed and listening; Tutor stands beside her, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pulls out with small amplitude at slow speed, opening the space around the figures.\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] All matter in our world is from the natural bases...</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c01_audioOnly_t01.json",
     "take": "01",
     "chunk": "S05-c01"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c02_audioOnly_t01_s111_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on the cushioned couch, relaxed, reading; Tutor stands beside her with one arm raised, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pulls out with small amplitude at slow speed, opening the space around the figures. <Subject 1> (S1) says: <d>[English] which are earth, air, fire and water...</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] the four elements from which all things are created.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c02.json",
     "take": "01",
     "chunk": "S05-c02"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c02_audioOnly_t01_s2222_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on the cushioned couch, relaxed, reading; Tutor stands beside her with one arm raised, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pulls out with small amplitude at slow speed, opening the space around the figures. <Subject 1> (S1) says: <d>[English] which are earth, air, fire and water...</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] the four elements from which all things are created.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c02.json",
     "take": "01",
     "chunk": "S05-c02"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c02_audioOnly_t01_s33333_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on the cushioned couch, relaxed, reading; Tutor stands beside her with one arm raised, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pulls out with small amplitude at slow speed, opening the space around the figures. <Subject 1> (S1) says: <d>[English] which are earth, air, fire and water...</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] the four elements from which all things are created.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c02.json",
     "take": "01",
     "chunk": "S05-c02"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c02_audioOnly_t01_s444444_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on the cushioned couch, relaxed, reading; Tutor stands beside her with one arm raised, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pulls out with small amplitude at slow speed, opening the space around the figures. <Subject 1> (S1) says: <d>[English] which are earth, air, fire and water...</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] the four elements from which all things are created.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c02.json",
     "take": "01",
     "chunk": "S05-c02"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c02_audioOnly_t01_s5555555_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on the cushioned couch, relaxed, reading; Tutor stands beside her with one arm raised, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pulls out with small amplitude at slow speed, opening the space around the figures. <Subject 1> (S1) says: <d>[English] which are earth, air, fire and water...</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] the four elements from which all things are created.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c02.json",
     "take": "01",
     "chunk": "S05-c02"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c02_audioOnly_t01_s66666666_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 1>.\n<Subject 2> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TUTOR, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on the cushioned couch, relaxed, reading; Tutor stands beside her with one arm raised, teaching. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pulls out with small amplitude at slow speed, opening the space around the figures. <Subject 1> (S1) says: <d>[English] which are earth, air, fire and water...</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] the four elements from which all things are created.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c02.json",
     "take": "01",
     "chunk": "S05-c02"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c03_audioOnly_t01_s111_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n<Subject 2> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on a chaise lounge, relaxed and at ease; Tutor sits facing her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] How can you talk about elements when the war draws nearer to us every hour?</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] Princess Teegra, we all have our duty.</d> <Subject 2> (S2) says: <d>[English] Your father's duty is to be king and lead.</d>\n\n[Shot 3] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 2> (S2) says: <d>[English] Your brother's duty is to soldier. And your duty is to learn.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c03.json",
     "take": "01",
     "chunk": "S05-c03"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c03_audioOnly_t01_s2222_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n<Subject 2> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on a chaise lounge, relaxed and at ease; Tutor sits facing her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] How can you talk about elements when the war draws nearer to us every hour?</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] Princess Teegra, we all have our duty.</d> <Subject 2> (S2) says: <d>[English] Your father's duty is to be king and lead.</d>\n\n[Shot 3] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 2> (S2) says: <d>[English] Your brother's duty is to soldier. And your duty is to learn.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c03.json",
     "take": "01",
     "chunk": "S05-c03"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c03_audioOnly_t01_s33333_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n<Subject 2> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on a chaise lounge, relaxed and at ease; Tutor sits facing her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] How can you talk about elements when the war draws nearer to us every hour?</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] Princess Teegra, we all have our duty.</d> <Subject 2> (S2) says: <d>[English] Your father's duty is to be king and lead.</d>\n\n[Shot 3] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 2> (S2) says: <d>[English] Your brother's duty is to soldier. And your duty is to learn.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c03.json",
     "take": "01",
     "chunk": "S05-c03"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c03_audioOnly_t01_s444444_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n<Subject 2> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on a chaise lounge, relaxed and at ease; Tutor sits facing her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] How can you talk about elements when the war draws nearer to us every hour?</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] Princess Teegra, we all have our duty.</d> <Subject 2> (S2) says: <d>[English] Your father's duty is to be king and lead.</d>\n\n[Shot 3] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 2> (S2) says: <d>[English] Your brother's duty is to soldier. And your duty is to learn.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c03.json",
     "take": "01",
     "chunk": "S05-c03"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c03_audioOnly_t01_s5555555_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n<Subject 2> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on a chaise lounge, relaxed and at ease; Tutor sits facing her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] How can you talk about elements when the war draws nearer to us every hour?</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] Princess Teegra, we all have our duty.</d> <Subject 2> (S2) says: <d>[English] Your father's duty is to be king and lead.</d>\n\n[Shot 3] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 2> (S2) says: <d>[English] Your brother's duty is to soldier. And your duty is to learn.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c03.json",
     "take": "01",
     "chunk": "S05-c03"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c03_audioOnly_t01_s66666666_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n<Subject 2> is TUTOR, a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep a black bob with bangs, light brown skin, a light blue bandeau top and skirt, and a broad gold collar and belt consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra reclines on a chaise lounge, relaxed and at ease; Tutor sits facing her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera stays low and tilts up slightly. The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] How can you talk about elements when the war draws nearer to us every hour?</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] Princess Teegra, we all have our duty.</d> <Subject 2> (S2) says: <d>[English] Your father's duty is to be king and lead.</d>\n\n[Shot 3] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 2> (S2) says: <d>[English] Your brother's duty is to soldier. And your duty is to learn.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c03.json",
     "take": "01",
     "chunk": "S05-c03"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c04_audioOnly_t01_s111_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 2>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra lies back on the couch with her arms stretched above her head, entirely relaxed; Tutor sits in profile beside her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face.\n\n[Shot 2] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] You mean my duty is to stay shut up...</d> <Subject 1> (S1) says: <d>[English] while all the men do the fighting and share all the glory.</d> <Subject 1> (S1) says: <d>[English] We think that stinks.</d> <Subject 1> (S1) says: <d>[English] Don't we, Shaitan?</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c04.json",
     "take": "01",
     "chunk": "S05-c04"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c04_audioOnly_t01_s2222_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 2>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra lies back on the couch with her arms stretched above her head, entirely relaxed; Tutor sits in profile beside her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face.\n\n[Shot 2] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] You mean my duty is to stay shut up...</d> <Subject 1> (S1) says: <d>[English] while all the men do the fighting and share all the glory.</d> <Subject 1> (S1) says: <d>[English] We think that stinks.</d> <Subject 1> (S1) says: <d>[English] Don't we, Shaitan?</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c04.json",
     "take": "01",
     "chunk": "S05-c04"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c04_audioOnly_t01_s33333_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 2>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra lies back on the couch with her arms stretched above her head, entirely relaxed; Tutor sits in profile beside her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face.\n\n[Shot 2] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] You mean my duty is to stay shut up...</d> <Subject 1> (S1) says: <d>[English] while all the men do the fighting and share all the glory.</d> <Subject 1> (S1) says: <d>[English] We think that stinks.</d> <Subject 1> (S1) says: <d>[English] Don't we, Shaitan?</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c04.json",
     "take": "01",
     "chunk": "S05-c04"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c04_audioOnly_t01_s444444_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 2>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra lies back on the couch with her arms stretched above her head, entirely relaxed; Tutor sits in profile beside her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face.\n\n[Shot 2] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] You mean my duty is to stay shut up...</d> <Subject 1> (S1) says: <d>[English] while all the men do the fighting and share all the glory.</d> <Subject 1> (S1) says: <d>[English] We think that stinks.</d> <Subject 1> (S1) says: <d>[English] Don't we, Shaitan?</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c04.json",
     "take": "01",
     "chunk": "S05-c04"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c04_audioOnly_t01_s5555555_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 2>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra lies back on the couch with her arms stretched above her head, entirely relaxed; Tutor sits in profile beside her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face.\n\n[Shot 2] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] You mean my duty is to stay shut up...</d> <Subject 1> (S1) says: <d>[English] while all the men do the fighting and share all the glory.</d> <Subject 1> (S1) says: <d>[English] We think that stinks.</d> <Subject 1> (S1) says: <d>[English] Don't we, Shaitan?</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c04.json",
     "take": "01",
     "chunk": "S05-c04"
    },
    "runs/T0016_s05_technicolor-audio-only-ref2va/output/seedhunt/S05-c04_audioOnly_t01_s66666666_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 1>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of TEEGRA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 2>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Teegra and Tutor are present, and both remain in the royal bedchamber the whole time. Teegra lies back on the couch with her arms stretched above her head, entirely relaxed; Tutor sits in profile beside her, talking. Nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face.\n\n[Shot 2] The camera arcs around the figures with small amplitude at slow speed, shifting the angle across the passage. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] You mean my duty is to stay shut up...</d> <Subject 1> (S1) says: <d>[English] while all the men do the fighting and share all the glory.</d> <Subject 1> (S1) says: <d>[English] We think that stinks.</d> <Subject 1> (S1) says: <d>[English] Don't we, Shaitan?</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nSoft plucked strings over a slow rising line of low clarinets, held at a moderate tempo and easing down to a quiet close.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S05-c04.json",
     "take": "01",
     "chunk": "S05-c04"
    }
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
    "runs/T0017_s03_technicolor-audio-only/arms/take2__S03-c01_audioOnly_t02_00001_.mp4",
    "runs/T0017_s03_technicolor-audio-only/arms/take2__S03-c02_audioOnly_t02_00001_.mp4",
    "runs/T0017_s03_technicolor-audio-only/arms/take3__S03-c01_audioOnly_t03_00001_.mp4",
    "runs/T0017_s03_technicolor-audio-only/arms/take3__S03-c02_audioOnly_t03_00001_.mp4",
    "runs/T0017_s03_technicolor-audio-only/arms/take4__S03-c01_audioOnly_t04_00001_.mp4",
    "runs/T0017_s03_technicolor-audio-only/arms/take4__S03-c02_audioOnly_t04_00001_.mp4",
    "runs/T0017_s03_technicolor-audio-only/arms/take5__S03-c01_audioOnly_t05_00001_.mp4",
    "runs/T0017_s03_technicolor-audio-only/arms/take5__S03-c02_audioOnly_t05_00001_.mp4",
    "runs/T0017_s03_technicolor-audio-only/arms/take6__S03-c01_audioOnly_t06_00001_.mp4",
    "runs/T0017_s03_technicolor-audio-only/arms/take6__S03-c02_audioOnly_t06_00001_.mp4",
    "runs/T0017_s03_technicolor-audio-only/arms/take7__S03-c01_audioOnly_t07_00001_.mp4",
    "runs/T0017_s03_technicolor-audio-only/arms/take7__S03-c02_audioOnly_t07_00001_.mp4",
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
   },
   "clipmeta": {
    "runs/T0017_s03_technicolor-audio-only/S03_audioOnly_stitched.mp4": {},
    "runs/T0017_s03_technicolor-audio-only/arms/take2__S03-c01_audioOnly_t02_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n<Subject 3> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 3>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 2].\n<Subject 3>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 4>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Juliana stands facing Nekron in medium close-up; Nekron stands facing her. Both remain in place; nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] You have done well, my son.</d> <Subject 1> (S1) says: <d>[English] The North Village has fallen. We have won.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] I want to thank you, Mother.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 2> (S2) says: <d>[English] The Great Plain is all that stands between ourselves and Fire Keep.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c01_audioOnly_t02.json",
     "take": "02",
     "chunk": "S03-c01"
    },
    "runs/T0017_s03_technicolor-audio-only/arms/take2__S03-c02_audioOnly_t02_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n<Subject 3> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 3>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 2].\n<Subject 3>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 4>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Nekron is seated on the throne, turned slightly toward the camera; Juliana stands facing him with one hand raised in a gesture. Both remain in place; nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] That is a long distance.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] A distance we may not have to travel.</d> <Subject 2> (S2) says: <d>[English] I am sending our envoys to Jarol with our new demands.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] He will not submit.</d> <Subject 2> (S2) says: <d>[English] Perhaps.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c02_audioOnly_t02.json",
     "take": "02",
     "chunk": "S03-c02"
    },
    "runs/T0017_s03_technicolor-audio-only/arms/take3__S03-c01_audioOnly_t03_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n<Subject 3> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 3>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 3].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 3].\n<Subject 3>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 3].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 4>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Juliana stands facing Nekron in medium close-up; Nekron stands facing her. Both remain in place; nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 female, pale, long, straight, black hair, purple top with deep neckline (this is JULIANA). Nobody else is visible. <Subject 1> (S1) says: <d>[English] You have done well, my son.</d> <Subject 1> (S1) says: <d>[English] The North Village has fallen. We have won.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 male, pale grayish, long white hair, dark purple robe with black cuffs (this is NEKRON). Nobody else is visible. <Subject 2> (S2) says: <d>[English] I want to thank you, Mother.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. On screen in this shot: exactly 1 person, alone \u2014 female, pale, long black hair with a headband hair, purple dress with deep neckline (this is JULIANA). Nobody else is visible. <Subject 2> (S2) says: <d>[English] The Great Plain is all that stands between ourselves and Fire Keep.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c01_audioOnly_t03.json",
     "take": "03",
     "chunk": "S03-c01"
    },
    "runs/T0017_s03_technicolor-audio-only/arms/take3__S03-c02_audioOnly_t03_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n<Subject 3> is TEEGRA, very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace, shown in <Picture 3>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 3].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 3].\n<Subject 3>: fully_preserved \u2014 keep very long black hair, pale skin, green eyes, a lightweight purple two-piece costume, and a gold necklace consistent across [Shot 1] and [Shot 3].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 4>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Nekron is seated on the throne, turned slightly toward the camera; Juliana stands facing him with one hand raised in a gesture. Both remain in place; nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 male, grayish, long white hair hair, dark robe with blue collar and green buttons (this is NEKRON). Nobody else is visible. <Subject 1> (S1) says: <d>[English] That is a long distance.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 female, pale grayish tone, long black hair with a beaded headband hair, purple v-neck top (this is TEEGRA). Nobody else is visible. <Subject 2> (S2) says: <d>[English] A distance we may not have to travel.</d> <Subject 2> (S2) says: <d>[English] I am sending our envoys to Jarol with our new demands.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. On screen in this shot: exactly 1 person, alone \u2014 male, pale grayish tone, long white hair hair, dark purple coat with green buttons and dark cuffs (this is NEKRON). Nobody else is visible. <Subject 1> (S1) says: <d>[English] He will not submit.</d> <Subject 2> (S2) says: <d>[English] Perhaps.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c02_audioOnly_t03.json",
     "take": "03",
     "chunk": "S03-c02"
    },
    "runs/T0017_s03_technicolor-audio-only/arms/take4__S03-c01_audioOnly_t04_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 3].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 3].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Juliana stands facing Nekron in medium close-up; Nekron stands facing her. Both remain in place; nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 female, pale, long, straight, black hair, purple top with deep neckline (this is JULIANA). Nobody else is visible. <Subject 1> (S1) says: <d>[English] You have done well, my son.</d> <Subject 1> (S1) says: <d>[English] The North Village has fallen. We have won.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 male, pale grayish, long white hair, dark purple robe with black cuffs (this is NEKRON). Nobody else is visible. <Subject 2> (S2) says: <d>[English] I want to thank you, Mother.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. On screen in this shot: exactly 1 person, alone \u2014 female, pale, long black hair with a headband hair, purple dress with deep neckline (this is JULIANA). Nobody else is visible. <Subject 2> (S2) says: <d>[English] The Great Plain is all that stands between ourselves and Fire Keep.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c01_audioOnly_t04.json",
     "take": "04",
     "chunk": "S03-c01"
    },
    "runs/T0017_s03_technicolor-audio-only/arms/take4__S03-c02_audioOnly_t04_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 3].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 3].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Nekron is seated on the throne, turned slightly toward the camera; Juliana stands facing him with one hand raised in a gesture. Both remain in place; nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 male, grayish, long white hair hair, dark robe with blue collar and green buttons (this is NEKRON). Nobody else is visible. <Subject 1> (S1) says: <d>[English] That is a long distance.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 female, pale grayish tone, long black hair with a beaded headband hair, purple v-neck top (this is JULIANA). Nobody else is visible. <Subject 2> (S2) says: <d>[English] A distance we may not have to travel.</d> <Subject 2> (S2) says: <d>[English] I am sending our envoys to Jarol with our new demands.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. On screen in this shot: exactly 1 person, alone \u2014 male, pale grayish tone, long white hair hair, dark purple coat with green buttons and dark cuffs (this is NEKRON). Nobody else is visible. <Subject 1> (S1) says: <d>[English] He will not submit.</d> <Subject 2> (S2) says: <d>[English] Perhaps.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c02_audioOnly_t04.json",
     "take": "04",
     "chunk": "S03-c02"
    },
    "runs/T0017_s03_technicolor-audio-only/arms/take5__S03-c01_audioOnly_t05_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 3].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 3].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Juliana stands facing Nekron in medium close-up; Nekron stands facing her. Both remain in place; nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 female, pale, long, straight, black hair, purple top with deep neckline (this is JULIANA). Nobody else is visible. <Subject 1> (S1) says: <d>[English] You have done well, my son.</d> <Subject 1> (S1) says: <d>[English] The North Village has fallen. We have won.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 male, pale grayish, long white hair, dark purple robe with black cuffs (this is NEKRON). Nobody else is visible. <Subject 2> (S2) says: <d>[English] I want to thank you, Mother.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. On screen in this shot: exactly 1 person, alone \u2014 female, pale, long black hair with a headband hair, purple dress with deep neckline (this is JULIANA). Nobody else is visible. <Subject 2> (S2) says: <d>[English] The Great Plain is all that stands between ourselves and Fire Keep.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c01_audioOnly_t05.json",
     "take": "05",
     "chunk": "S03-c01"
    },
    "runs/T0017_s03_technicolor-audio-only/arms/take5__S03-c02_audioOnly_t05_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 3].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 3].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Nekron is seated on the throne, turned slightly toward the camera; Juliana stands facing him with one hand raised in a gesture. Both remain in place; nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 male, grayish, long white hair hair, dark robe with blue collar and green buttons (this is NEKRON). Nobody else is visible. <Subject 1> (S1) says: <d>[English] That is a long distance.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 female, pale grayish tone, long black hair with a beaded headband hair, purple v-neck top (this is JULIANA). Nobody else is visible. <Subject 2> (S2) says: <d>[English] A distance we may not have to travel.</d> <Subject 2> (S2) says: <d>[English] I am sending our envoys to Jarol with our new demands.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. On screen in this shot: exactly 1 person, alone \u2014 male, pale grayish tone, long white hair hair, dark purple coat with green buttons and dark cuffs (this is NEKRON). Nobody else is visible. <Subject 1> (S1) says: <d>[English] He will not submit.</d> <Subject 2> (S2) says: <d>[English] Perhaps.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c02_audioOnly_t05.json",
     "take": "05",
     "chunk": "S03-c02"
    },
    "runs/T0017_s03_technicolor-audio-only/arms/take6__S03-c01_audioOnly_t06_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 3].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 3].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Juliana stands facing Nekron in medium close-up; Nekron stands facing her. Both remain in place; nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 female, pale, long, straight, black hair, purple top with deep neckline (this is JULIANA). Nobody else is visible. <Subject 1> (S1) says: <d>[English] You have done well, my son.</d> <Subject 1> (S1) says: <d>[English] The North Village has fallen. We have won.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 male, pale grayish, long white hair, dark purple robe with black cuffs (this is NEKRON). Nobody else is visible. <Subject 2> (S2) says: <d>[English] I want to thank you, Mother.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. On screen in this shot: exactly 1 person, alone \u2014 female, pale, long black hair with a headband hair, purple dress with deep neckline (this is JULIANA). Nobody else is visible. <Subject 2> (S2) says: <d>[English] The Great Plain is all that stands between ourselves and Fire Keep.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c01_audioOnly_t06.json",
     "take": "06",
     "chunk": "S03-c01"
    },
    "runs/T0017_s03_technicolor-audio-only/arms/take6__S03-c02_audioOnly_t06_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 3].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 3].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Nekron is seated on the throne, turned slightly toward the camera; Juliana stands facing him with one hand raised in a gesture. Both remain in place; nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 male, grayish, long white hair hair, dark robe with blue collar and green buttons (this is NEKRON). Nobody else is visible. <Subject 1> (S1) says: <d>[English] That is a long distance.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 female, pale grayish tone, long black hair with a beaded headband hair, purple v-neck top (this is JULIANA). Nobody else is visible. <Subject 2> (S2) says: <d>[English] A distance we may not have to travel.</d> <Subject 2> (S2) says: <d>[English] I am sending our envoys to Jarol with our new demands.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. On screen in this shot: exactly 1 person, alone \u2014 male, pale grayish tone, long white hair hair, dark purple coat with green buttons and dark cuffs (this is NEKRON). Nobody else is visible. <Subject 1> (S1) says: <d>[English] He will not submit.</d> <Subject 2> (S2) says: <d>[English] Perhaps.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c02_audioOnly_t06.json",
     "take": "06",
     "chunk": "S03-c02"
    },
    "runs/T0017_s03_technicolor-audio-only/arms/take7__S03-c01_audioOnly_t07_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 3].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 3].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Juliana stands facing Nekron in medium close-up; Nekron stands facing her. Both remain in place; nobody walks or moves toward the camera.\n\nWhere the paragraph above has both characters in frame together, the per-shot cast lines below override it: inside each shot ONLY the person named there is visible, and the other character is out of frame.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 female, pale, long, straight, black hair, purple top with deep neckline (this is JULIANA). Nobody else is visible. <Subject 1> (S1) says: <d>[English] You have done well, my son.</d> <Subject 1> (S1) says: <d>[English] The North Village has fallen. We have won.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 male, pale grayish, long white hair, dark purple robe with black cuffs (this is NEKRON). Nobody else is visible. <Subject 2> (S2) says: <d>[English] I want to thank you, Mother.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. On screen in this shot: exactly 1 person, alone \u2014 female, pale, long black hair with a headband hair, purple dress with deep neckline (this is JULIANA). Nobody else is visible. <Subject 2> (S2) says: <d>[English] The Great Plain is all that stands between ourselves and Fire Keep.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c01_audioOnly_t07.json",
     "take": "07",
     "chunk": "S03-c01"
    },
    "runs/T0017_s03_technicolor-audio-only/arms/take7__S03-c02_audioOnly_t07_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 3].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 3].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Nekron is seated on the throne, turned slightly toward the camera; Juliana stands facing him with one hand raised in a gesture. Both remain in place; nobody walks or moves toward the camera.\n\nWhere the paragraph above has both characters in frame together, the per-shot cast lines below override it: inside each shot ONLY the person named there is visible, and the other character is out of frame.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 male, grayish, long white hair hair, dark robe with blue collar and green buttons (this is NEKRON). Nobody else is visible. <Subject 1> (S1) says: <d>[English] That is a long distance.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. On screen in this shot: exactly 1 person, alone \u2014 female, pale grayish tone, long black hair with a beaded headband hair, purple v-neck top (this is JULIANA). Nobody else is visible. <Subject 2> (S2) says: <d>[English] A distance we may not have to travel.</d> <Subject 2> (S2) says: <d>[English] I am sending our envoys to Jarol with our new demands.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. On screen in this shot: exactly 1 person, alone \u2014 male, pale grayish tone, long white hair hair, dark purple coat with green buttons and dark cuffs (this is NEKRON). Nobody else is visible. <Subject 1> (S1) says: <d>[English] He will not submit.</d> <Subject 2> (S2) says: <d>[English] Perhaps.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c02_audioOnly_t07.json",
     "take": "07",
     "chunk": "S03-c02"
    },
    "runs/T0017_s03_technicolor-audio-only/output/S03-c01_audioOnly_t01_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Juliana stands facing Nekron in medium close-up; Nekron stands facing her. Both remain in place; nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] You have done well, my son.</d> <Subject 1> (S1) says: <d>[English] The North Village has fallen. We have won.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] I want to thank you, Mother.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 2> (S2) says: <d>[English] The Great Plain is all that stands between ourselves and Fire Keep.</d>\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c01_audioOnly_t01.json",
     "take": "01",
     "chunk": "S03-c01"
    },
    "runs/T0017_s03_technicolor-audio-only/output/S03-c02_audioOnly_t01_00001_.mp4": {
     "prompt": "subject_definitions:\n\n<Subject 1> is JULIANA, pale skin, very long straight jet-black hair, and a deep purple gown, shown in <Picture 1>.\n<Subject 2> is NEKRON, very long white hair, pale skin, and dark purple robes, shown in <Picture 2>.\n\n\n\nsummary:\n\n[audio reuse] A technicolor 80s sword-and-sandals epic, shot on 35mm: a single continuous live-action scene of JULIANA, preserving each character's appearance from their reference sheet and the spoken dialogue and timing of the reference audio.\n\n\n\nretention_analysis:\n\n<Subject 1>: fully_preserved \u2014 keep pale skin, very long straight jet-black hair, and a deep purple gown consistent across [Shot 1] and [Shot 2].\n<Subject 2>: fully_preserved \u2014 keep very long white hair, pale skin, and dark purple robes consistent across [Shot 1] and [Shot 2].\nReference audio: fully_copy \u2014 reuse the spoken lines and their exact timing.\n<Picture 3>: background_only \u2014 this is the location as a painted environment, not people; keep ONLY the environment (layout, lighting, color, architecture) and ignore any figures.\n\n\n\ndetailed_description:\n\na technicolor 80s sword-and-sandals epic, shot on 35mm: vivid saturated colour, deep blacks and high contrast, practical sets, high-fantasy practical effects on an unlimited budget, vast torchlit stone halls with heavy drapery, brass and gold, jewelled saturated colour\n\nONLY the named characters are present in the shot \u2014 there are no other people, no crowd, no background figures and no extras at any point. The scene is quiet, intimate and relaxed. The characters stay where they are; nobody walks, enters, or moves toward the camera.\n\nOnly Juliana and Nekron are present, alone in the icy throne hall. Nekron is seated on the throne, turned slightly toward the camera; Juliana stands facing him with one hand raised in a gesture. Both remain in place; nobody walks or moves toward the camera.\n\n[Shot 1] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 1> (S1) says: <d>[English] That is a long distance.</d>\n\n[Shot 2] The camera pushes in with small amplitude at slow speed, tightening toward the face. <Subject 2> (S2) says: <d>[English] A distance we may not have to travel.</d> <Subject 2> (S2) says: <d>[English] I am sending our envoys to Jarol with our new demands.</d>\n\n[Shot 3] The camera pushes in with small amplitude at slow speed, tightening toward the face. The move slows and stops as the figure settles. <Subject 1> (S1) says: <d>[English] He will not submit.</d> <Subject 2> (S2) says: <d>[English] Perhaps.</d>\n\n\n\noverall_soundscape:\n\nRoom reverb and a low air movement through stone, distant movement echoing off hard surfaces, cloth and body movement.\n\n\n\nnon_diegetic_music:\n\nLow sustained strings and slow woodwind pulses at a slow tempo, with sparse bell tones above; dynamics stay quiet and grow only slightly.",
     "prompt_source": "runs/T0016_s05_technicolor-audio-only-ref2va/graphs/S03-c02.json",
     "take": "01",
     "chunk": "S03-c02"
    }
   }
  },
  {
   "id": "T0018",
   "scope": "",
   "title": "(unrecorded run)",
   "question": "",
   "verdict": "unrecorded",
   "status": "pending",
   "notes": "",
   "files": [
    "runs/T0018_s03_vlm-prompt-fl2va/output/compare_T0003_template_srcAudio.mp4",
    "runs/T0018_s03_vlm-prompt-fl2va/output/compare_T0018_vlm_srcAudio.mp4",
    "runs/T0018_s03_vlm-prompt-fl2va/output/s03-c01_T0018_t01_00001_.mp4"
   ],
   "clipmeta": {
    "runs/T0018_s03_vlm-prompt-fl2va/output/compare_T0003_template_srcAudio.mp4": {},
    "runs/T0018_s03_vlm-prompt-fl2va/output/compare_T0018_vlm_srcAudio.mp4": {},
    "runs/T0018_s03_vlm-prompt-fl2va/output/s03-c01_T0018_t01_00001_.mp4": {}
   }
  },
  {
   "id": "T0019",
   "scope": "",
   "title": "(unrecorded run)",
   "question": "",
   "verdict": "unrecorded",
   "status": "pending",
   "notes": "",
   "files": [
    "runs/T0019_s03_vlm-prompt-sweep/output/S03_template_T0003_stitched.mp4",
    "runs/T0019_s03_vlm-prompt-sweep/output/S03_template_srcAudio_stitched.mp4",
    "runs/T0019_s03_vlm-prompt-sweep/output/S03_vlm_T0019+T0018_stitched.mp4",
    "runs/T0019_s03_vlm-prompt-sweep/output/S03_vlm_srcAudio_stitched.mp4",
    "runs/T0019_s03_vlm-prompt-sweep/output/compare_s03-c01_vlm_srcAudio.mp4",
    "runs/T0019_s03_vlm-prompt-sweep/output/compare_s03-c02_vlm_srcAudio.mp4",
    "runs/T0019_s03_vlm-prompt-sweep/output/compare_s03-c03_vlm_srcAudio.mp4",
    "runs/T0019_s03_vlm-prompt-sweep/output/compare_s03-c04_vlm_srcAudio.mp4",
    "runs/T0019_s03_vlm-prompt-sweep/output/compare_s03-c05_vlm_srcAudio.mp4",
    "runs/T0019_s03_vlm-prompt-sweep/output/s03-c02_T0019_t01_00001_.mp4",
    "runs/T0019_s03_vlm-prompt-sweep/output/s03-c03_T0019_t01_00001_.mp4",
    "runs/T0019_s03_vlm-prompt-sweep/output/s03-c04_T0019_t01_00001_.mp4",
    "runs/T0019_s03_vlm-prompt-sweep/output/s03-c05_T0019_t01_00001_.mp4"
   ],
   "clipmeta": {
    "runs/T0019_s03_vlm-prompt-sweep/output/S03_template_T0003_stitched.mp4": {},
    "runs/T0019_s03_vlm-prompt-sweep/output/S03_template_srcAudio_stitched.mp4": {},
    "runs/T0019_s03_vlm-prompt-sweep/output/S03_vlm_T0019+T0018_stitched.mp4": {},
    "runs/T0019_s03_vlm-prompt-sweep/output/S03_vlm_srcAudio_stitched.mp4": {},
    "runs/T0019_s03_vlm-prompt-sweep/output/compare_s03-c01_vlm_srcAudio.mp4": {},
    "runs/T0019_s03_vlm-prompt-sweep/output/compare_s03-c02_vlm_srcAudio.mp4": {},
    "runs/T0019_s03_vlm-prompt-sweep/output/compare_s03-c03_vlm_srcAudio.mp4": {},
    "runs/T0019_s03_vlm-prompt-sweep/output/compare_s03-c04_vlm_srcAudio.mp4": {},
    "runs/T0019_s03_vlm-prompt-sweep/output/compare_s03-c05_vlm_srcAudio.mp4": {},
    "runs/T0019_s03_vlm-prompt-sweep/output/s03-c02_T0019_t01_00001_.mp4": {},
    "runs/T0019_s03_vlm-prompt-sweep/output/s03-c03_T0019_t01_00001_.mp4": {},
    "runs/T0019_s03_vlm-prompt-sweep/output/s03-c04_T0019_t01_00001_.mp4": {},
    "runs/T0019_s03_vlm-prompt-sweep/output/s03-c05_T0019_t01_00001_.mp4": {}
   }
  }
 ]
};
