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
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c01_T0003_t01.mp4",
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c02_T0003_t01.mp4",
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c03_T0003_t01.mp4",
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c04_T0003_t01.mp4",
    "runs/T0003_s03_fl2va-srcfflf/output/s03-c05_T0003_t01.mp4",
    "runs/T0003_s03_fl2va-srcfflf/s03_T0003_stitched.mp4",
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
  }
 ]
};
