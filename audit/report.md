# LM Studio quiver audit

baseline image: `C:\Users\gsfny\AppData\Local\hermes\images\dashboard_20261013_072743_a12cc767_ComfyUI_00063.png`

| model | load s | echo_identifiers | tool_call | json_shape | h3_3field | vision_caption | vision_stability |
|---|---|---|---|---|---|---|---|
| qwen3.8-27b-heretic-abliterated-uncensored | 12.5 | 1.00 | 1.00 | 1.00 | 0.83 | 0.25 | 0.28 |
| qwen2.5-vl-32b-instruct-abliterated | 17.3 | 1.00 | 1.00 | 1.00 | 0.83 | 1.00 | 0.42 |
| qwen3.8-flash-next@bf16 | 0.0 | — | — | — | — | — | — |
| qwen3.8-flash-next@q8_0 | 0.0 | — | — | — | — | — | — |
| gemma-4-26b-a4b-it-heretic | 9.7 | 0.00 | 1.00 | 0.00 | 0.33 | — | — |
| qwen3.8-27b-obliterated | 16.9 | 1.00 | 0.00 | 1.00 | 0.83 | 1.00 | 0.46 |
| mistral-7b-instruct-v0.3-abliterated | 9.1 | 1.00 | 1.00 | 1.00 | 0.83 | — | — |
| supergemma4-e4b-abliterated | 6.5 | 1.00 | 1.00 | 0.00 | 0.83 | — | — |
| qwen3-vl-8b-instruct-abliterated-v2.0@f16 | 16.0 | 1.00 | 1.00 | 1.00 | 0.83 | 1.00 | 0.55 |
| qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s | 6.0 | 1.00 | 1.00 | 1.00 | 0.83 | 1.00 | 0.53 |
| q3.5-bluestar-v2-27b | 12.8 | 1.00 | 1.00 | 0.00 | 0.33 | — | — |
| qwq-32b-arliai-rpr-v4 | 12.8 | 1.00 | 1.00 | 1.00 | 0.83 | — | — |

## Details

### qwen3.8-27b-heretic-abliterated-uncensored
load_ok=True load_s=12.5 quant=Q4_K_S
- **echo_identifiers** score=1.0 — 12/12 exact
  ```
  {"echo":["E:\\FNI\\refs\\setups\\S06-A_plate.jpg","qwen3.8-flash-next@q8_0","delegation.fallback_providers[0].model","shot_01243_f00059.jpg","S05-c04_ref.mp4","text-embedding-nomic-embed-text-v1.5","100.104.7.72:8188","graph_length_frames","integrated_multimodal_description","retention_analysis","0.00-second","<d>[English] By the frozen sea.</d>"]}
  ```
- **tool_call** score=1.0 — pull_render_outputs({'run': 'S06', 'shot': 4, 'kind': 'video'})
  ```
  [{"type": "function", "id": "lKCY2Wq2Jdx2nZHUSYQoYjgvrNw5FgkV", "function": {"name": "pull_render_outputs", "arguments": "{\"run\":\"S06\",\"shot\":4,\"kind\":\"video\"}"}}]
  ```
- **json_shape** score=1.0 — array of 6, keys ok
  ```
  [
    {
      "shot_id": "S06-1",
      "setup_id": "SETUP_06A",
      "camera": "slow push-in",
      "action": "the protagonist steps into the doorway",
      "soundscape": "rain taps softly against a windowpane",
      "music": "a low cello drone sustains beneath the scene"
    },
    {
      "shot_id": "S06-2",
      "setup_id": "SETUP_06B",
      "camera": "handheld follow",
      "action": "the protagonist crosses the room quickly",
      "soundscape": "footsteps echo on a wooden floor",
      "music": "sparse piano notes enter with quiet tension"
    },
    {
      "shot_id": "S06-3",
      "setup_id": "SETUP_06C",
      "camera": "whip pan right",
      "action": "the protagonist turns toward a sudden noise",
      "soundscape": "a distant door slams shut",
      "music": "strings rise briefly before fading"
    },
    {
      "shot_id": "S06-4",
      "setup_id": "SETUP_06D",
      "camera": "slow dolly out",
      "action": "the protagonist lowers their head in defeat",
      "soundscape": "wind moans through a broken shutter",
      "music": "a mournful violin line emerges"
    },
    {
      "shot_id": "S06-5",
      "setup_id": "SETUP_06E",
      "camera": "crane up",
      "action": "the protagonist reaches for a fallen object",
      "soundscape": "dust settles from the ceiling above",
      "music": "a soft choir hum adds weight to the moment"
    },
    {
      "shot_id": "S06-6",
      "setup_id": "SETUP_06F",
      "camera": "static close-up",
      "action": "the protagonist grips the object tightly",
      "soundscape": "a single heartbeat thuds in silence",
      "music": "the score resolves into a final sustained note"
    }
  ]
  ```
- **h3_3field** score=0.83 — all_three_fields=Y, field_order=Y, no_dead_video_ref=Y, no_shot1_timestamp=Y, single_camera_move=N, substantive=Y [cams=[]]
  ```
  integrated_multimodal_description: 5-second FL2VA cinematic fantasy shot beginning on the provided plate in a low-angle ice cavern and ending as a balanced two-shot of DARKWOLF and TEEGRA at the cavern mouth, with a warm torch pool glowing on the right wall, cold blue falloff behind them, DARKWOLF large bare-chested with black mane, war paint, and an axe held in his right hand, TEEGRA tall with dark hair, light blue wrap, and barefoot, subtle wind-blown ice particles, grounded realistic textures, tense atmospheric framing.
  overall_soundscape: Low cavern wind rushing through the space, distant cracking ice with faint stone resonance, minimal breath and fabric movement, a restrained low ambient drone underneath, no dialogue.
  non_diegetic_music: Sparse minimalist underscore built from a slow sub-bass drone, airy high shimmer, and subtle tension pulses, no melody, no percussion, 5 seconds.
  ```
- **vision_caption** score=0.25 — json_line=N, has_colors=N, has_subjects=N, prose=Y
  ```
  This image is a 2D animated character design reference sheet (model/turnaround) presented on a plain white background. On the left is a large, straight-on head-and-shoulders portrait of a single female character with medium-brown skin, a short black bob haircut with blunt bangs, dark arched eyebrows, long eyelashes, and full lips colored deep red; she wears
  ```
- **vision_colors** score=0.0 — 0 regions
  ```
  
  ```
- **vision_stability** score=0.28 — jaccard vs temp0 = 0.28
  ```
  This image is a 2D animated character design reference / model sheet presented on a plain white background. On the far left is a large front-facing bust portrait of a woman with tan-brown skin, a short straight black bob haircut with blunt bangs, thick dark arched eyebrows, almond-shaped dark eyes, full lips colored deep burgundy-red, and a pleated bronze/gold collar necklace over bare shoulders and a strapless light-blue top. The center shows three full-body turnarounds of the same character in neutral standing poses: front view (light-blue laced bandeau top with brown criss-cross tie strings, a light-blue wrap skirt hanging from a beaded brown hip belt, bare feet), left profile view, and back view (showing the open back of the top, the long blue skirt, and the collar). On the right is a grid of six circular detail callouts: an eye with eyebrow, the mouth/lips, an ear, a solid black hair color swatch, skin texture with thin line markings, and a close-up of a brown oval-beaded belt on blue fabric. The art style is clean cartoon animation line work with flat shading.
  
  {"shot_type": "character model sheet", "subjects": 1, "characters": ["woman"], "weapon_visible": false, "weapon": "", "colors": {"skin": "brown", "hair": "black", "top": "blue", "bottom": "blue", "background": "white"}, "camera": "flat multi-angle turnaround with detail callouts", "style": "2D cartoon animation"}
  ```

### qwen2.5-vl-32b-instruct-abliterated
load_ok=True load_s=17.3 quant=Q4_K_S
- **echo_identifiers** score=1.0 — 12/12 exact
  ```
  ```json
  {"echo": ["E:\\FNI\\refs\\setups\\S06-A_plate.jpg", "qwen3.8-flash-next@q8_0", "delegation.fallback_providers[0].model", "shot_01243_f00059.jpg", "S05-c04_ref.mp4", "text-embedding-nomic-embed-text-v1.5", "100.104.7.72:8188", "graph_length_frames", "integrated_multimodal_description", "retention_analysis", "0.00-second", "<d>[English] By the frozen sea.</d>"]}
  ```
  ```
- **tool_call** score=1.0 — pull_render_outputs({'run': 'S06', 'shot': 4, 'kind': 'video'})
  ```
  [{"type": "function", "id": "3wN327vpqWs8ScmfqWKnyquSdvKUopvv", "function": {"name": "pull_render_outputs", "arguments": "{\"run\":\"S06\",\"shot\":4,\"kind\":\"video\"}"}}]
  ```
- **json_shape** score=1.0 — array of 6, keys ok
  ```
  ```json
  [
      {
          "shot_id": 1,
          "setup_id": "S06-01",
          "camera": "Pan from left to right.",
          "action": "A person walks into frame carrying a briefcase.",
          "soundscape": "The sound of footsteps on pavement.",
          "music": "Upbeat jazz melody."
      },
      {
          "shot_id": 2,
          "setup_id": "S06-02",
          "camera": "Zoom in on the person's face.",
          "action": "The person smiles and nods at someone off-screen.",
          "soundscape": "A gentle breeze rustles nearby leaves.",
          "music": "Soft, melodic piano notes."
      },
      {
          "shot_id": 3,
          "setup_id": "S06-03",
          "camera": "Tilt up to show the person's full body.",
          "action": "The person begins running towards a building entrance.",
          "soundscape": "Echoes of distant laughter in the background.",
          "music": "Energetic, rhythmic drumbeat."
      },
      {
          "shot_id": 4,
          "setup_id": "S06-04",
          "camera": "Static shot with slight shake to mimic handheld feel.",
          "action": "The person opens the door and steps inside.",
          "soundscape": "A quiet hum of air conditioning.",
          "music": "Mellow, ambient guitar strumming."
      },
      {
          "shot_id": 5,
          "setup_id": "S06-05",
          "camera": "Dolly out to reveal more of the room.",
          "action": "The person sets down their briefcase and sits at a desk.",
          "soundscape": "The sound of papers rustling as they open files.",
          "music": "Calm, soothing piano chords."
      },
      {
          "shot_id": 6,
          "setup_id": "S06-06",
          "camera": "Cut to an over-the-shoulder view from behind the person.",
          "action": "The person types on a keyboard while looking at a computer screen.",
          "soundscape": "The soft click of keys and occasional beeps from the computer.",
          "music": "Light, uplifting flute melody."
      }
  ]
  ```
  ```
- **h3_3field** score=0.83 — all_three_fields=Y, field_order=Y, no_dead_video_ref=Y, no_shot1_timestamp=Y, single_camera_move=N, substantive=Y [cams=[]]
  ```
  integrated_multimodal_description:  
  Scene S06, setup S06-A. Interior — ice cavern, low camera angle capturing the warm glow of torchlight pooling on the right wall, with cold blue falloff illuminating the background. Characters present include DARKWOLF (big, bare-chested, black mane, axe in his right hand, adorned with war paint) and TEEGRA (tall, dark hair, light blue wrap, barefoot). The shot transitions from a single frame to a two-shot as they approach the cavern mouth.
  
  overall_soundscape:  
  Wind whispers through the ice cavern, distant cracking of ice adds tension, low drone underpins the atmosphere.
  
  non_diegetic_music:  
  Low, resonant tones with subtle choral harmonies.
  ```
- **vision_caption** score=1.0 — json_line=Y, has_colors=Y, has_subjects=Y, prose=Y
  ```
  The image shows a detailed character design for an animated female figure. The main focus is on the front view of the character, who has short black hair styled in a bob cut and wears a blue top with a gold necklace. To the right of the main image are three additional views: a full-body side profile facing left, another full-body side profile facing right, and a back view showing the character's silhouette.
  
  In the upper right corner, there are close-up illustrations of specific facial features: an eye, nose, ear, lips, and two circular shapes with gold accents. These details suggest they are part of the character design process, highlighting key elements like jewelry or decorative patterns.
  
  The overall style is clean and illustrative, typical of animation concept art. The background is plain white, emphasizing the character and her features.
  
  Here is the JSON output:
  
  ```json
  {
    "shot_type": "concept_art",
    "subjects": 1,
    "characters": ["female"],
    "weapon_visible": false,
    "weapon": "",
    "colors": {
      "skin": "brown",
      "hair": "black",
      "top": "blue",
      "bottom": "blue",
      "background": "white"
    },
    "camera": "front_view_with_multiple_angles",
    "style": "illustrative"
  }
  ```
  ```
- **vision_colors** score=1.0 — 6 regions
  ```
  hair: black  
  skin: brown  
  top garment: blue  
  bottom garment: blue  
  background: white  
  metal or accessory: gold  
  ```
- **vision_stability** score=0.42 — jaccard vs temp0 = 0.42
  ```
  The image shows a detailed character design for an animated female figure. The character has dark skin and black hair styled in a short bob cut. She wears a blue dress with thin straps on the top, which extends into a flowing skirt. A brown necklace is visible around her neck. The image includes multiple views of the character: front view, three-quarter profile from both sides, and back view. Additionally, there are close-up illustrations showing various facial features such as eyes, nose, ear, lips, and fingers.
  
  Here is the JSON description:
  
  ```json
  {
    "shot_type": "character design sheet",
    "subjects": 1,
    "characters": ["female"],
    "weapon_visible": false,
    "weapon": "",
    "colors": {
      "skin": "brown",
      "hair": "black",
      "top": "blue",
      "bottom": "blue",
      "background": "white"
    },
    "camera": "multi-view layout",
    "style": "animated"
  }
  ```
  ```

### qwen3.8-flash-next@bf16
load_ok=False load_s=0.0 quant=BF16

### qwen3.8-flash-next@q8_0
load_ok=False load_s=0.0 quant=Q8_0

### gemma-4-26b-a4b-it-heretic
load_ok=True load_s=9.7 quant=Q4_K_S
- **echo_identifiers** score=0.0 — 0/12 exact
  ```
  
  ```
- **tool_call** score=1.0 — pull_render_outputs({'kind': 'video', 'run': 'S06', 'shot': 4})
  ```
  [{"type": "function", "id": "td3K709BoT3DYv0MIY0q5NluOdyMrgeB", "function": {"name": "pull_render_outputs", "arguments": "{\"kind\":\"video\",\"run\":\"S06\",\"shot\":4}"}}]
  ```
- **json_shape** score=0.0 — unparseable JSON
  ```
  
  ```
- **h3_3field** score=0.33 — all_three_fields=N, field_order=N, no_dead_video_ref=Y, no_shot1_timestamp=Y, single_camera_move=N, substantive=N [cams=[]]
  ```
  
  ```

### qwen3.8-27b-obliterated
load_ok=True load_s=16.9 quant=Q4_K_M
- **echo_identifiers** score=1.0 — 12/12 exact
  ```
  
  
  {"echo": ["E:\\FNI\\refs\\setups\\S06-A_plate.jpg", "qwen3.8-flash-next@q8_0", "delegation.fallback_providers[0].model", "shot_01243_f00059.jpg", "S05-c04_ref.mp4", "text-embedding-nomic-embed-text-v1.5", "100.104.7.72:8188", "graph_length_frames", "integrated_multimodal_description", "retention_analysis", "0.00-second", "<d>[English] By the frozen sea.</d>"]}
  ```
- **tool_call** score=0.0 — no tool_calls in reply
  ```
  
  
  ```json
  {
    "tool": "fetch_video",
    "parameters": {
      "chunk_id": "S06",
      "shot_number": 4,
      "source": "render_box"
    }
  }
  ```
  ```
- **json_shape** score=1.0 — array of 6, keys ok
  ```
  
  
  [
    {
      "shot_id": "S06_01",
      "setup_id": "S06A",
      "camera": "static wide shot",
      "action": "a man walks slowly down a dimly lit corridor",
      "soundscape": "muffled footsteps echo against concrete walls",
      "music": "a low, sustained cello note holds the silence"
    },
    {
      "shot_id": "S06_02",
      "setup_id": "S06B",
      "camera": "slow push-in",
      "action": "the man stops and turns his head toward a distant sound",
      "soundscape": "a faint metallic clanging grows louder",
      "music": "sparse piano chords enter quietly"
    },
    {
      "shot_id": "S06_03",
      "setup_id": "S06C",
      "camera": "handheld close-up",
      "action": "his hand grips the edge of a rusted door frame",
      "soundscape": "the sound of breathing is sharply audible",
      "music": "a single violin line rises and fades"
    },
    {
      "shot_id": "S06_04",
      "setup_id": "S06D",
      "camera": "static medium shot",
      "action": "he pushes the door open and steps into a bare room",
      "soundscape": "the heavy door slams against its frame",
      "music": "the piano returns with a brief, staccato phrase"
    },
    {
      "shot_id": "S06_05",
      "setup_id": "S06E",
      "camera": "slow pan to the right",
      "action": "he scans the empty space and lowers his gaze to the floor",
      "soundscape": "a thin, high-frequency hum fills the air",
      "music": "a soft, wordless vocal line lingers"
    },
    {
      "shot_id": "S06_06",
      "setup_id": "S06F",
      "camera": "static extreme close-up on his eyes",
      "action": "his jaw tightens and a single tear tracks down his cheek",
      "soundscape": "all ambient sound drops to near silence",
      "music": "a final, sustained string note fades out"
    }
  ]
  ```
- **h3_3field** score=0.83 — all_three_fields=Y, field_order=Y, no_dead_video_ref=Y, no_shot1_timestamp=Y, single_camera_move=N, substantive=Y [cams=[]]
  ```
  
  
  integrated_multimodal_description: Interior of an ice cavern, low camera angle. A warm pool of torchlight glows on the right wall while cold blue light fades into the background behind. DARKWOLF stands large and bare-chested with a black mane, war paint across his face, gripping an axe in his right hand; TEEGRA is tall with dark hair, wrapped in a light blue cloth, barefoot. The first frame holds on this plate image; by the last frame the two-shot has shifted to the cavern mouth. Duration 5 seconds.
  overall_soundscape: Sustained wind, distant cracking of ice, and a low drone underneath throughout.
  non_diegetic_music: A low, continuous drone underlies the entire shot.
  ```
- **vision_caption** score=1.0 — json_line=Y, has_colors=Y, has_subjects=Y, prose=Y
  ```
  
  
  This is a character reference/model sheet showing a single female figure in multiple views: a large front-facing head-and-shoulders portrait on the left, followed by full-body front, side-profile, and back views, and a column of circular detail close-ups (eye, mouth, ear, plus color swatch and scarred skin and belt details). The character has dark brown skin, short black bobbed hair, red lips, an amber/gold collar necklace, and light blue clothing. No weapon is present.
  
  {"shot_type": "character model sheet", "subjects": 1, "characters": ["woman with black bob hair"], "weapon_visible": false, "weapon": "", "colors": {"skin": "brown", "hair": "black", "top": "light blue", "bottom": "light blue", "background": "white"}, "camera": "front and multiple angles", "style": "cartoon illustration"}
  ```
- **vision_colors** score=1.0 — 6 regions
  ```
  
  
  hair: black
  skin: brown
  top garment: light blue
  bottom garment: light blue
  background: white
  any metal or accessory: gold
  ```
- **vision_stability** score=0.46 — jaccard vs temp0 = 0.46
  ```
  
  
  This is a character model sheet featuring an illustration of a female character with dark skin and short black hair. She is shown in multiple views: a large front-facing headshot, full-body front, side, and back views. The character wears a light blue top with lacing details on the chest, a gold necklace, a waist piece with circular ornaments, and a long light blue skirt that drapes to her ankles. On the right side of the image are several close-up reference circles detailing specific features: an eye with eyelashes, a mouth with dark red lips, an ear, a solid black circle, skin texture, and the waist ornament. The background is plain white.
  
  {"shot_type": "character model sheet", "subjects": 1, "characters": ["unidentified female"], "weapon_visible": false, "weapon": null, "colors": {"skin": "brown", "hair": "black", "top": "light blue", "bottom": "light blue", "background": "white"}, "camera": "frontal and multiple angles", "style": "digital illustration"}
  ```

### mistral-7b-instruct-v0.3-abliterated
load_ok=True load_s=9.1 quant=F16
- **echo_identifiers** score=1.0 — 12/12 exact
  ```
   {"echo": ["E:\\FNI\\refs\\setups\\S06-A_plate.jpg", "qwen3.8-flash-next@q8_0", "delegation.fallback_providers[0].model", "shot_01243_f00059.jpg", "S05-c04_ref.mp4", "text-embedding-nomic-embed-text-v1.5", "100.104.7.72:8188", "graph_length_frames", "integrated_multimodal_description", "retention_analysis", "0.00-second", "<d>[English] By the frozen sea.</d>"]}
  ```
- **tool_call** score=1.0 — pull_render_outputs({'run': 'S06', 'shot': 4, 'kind': 'video'})
  ```
  [{"type": "function", "id": "VTYDV2cVVoX3doG1PD5ehqPkkd653hXg", "function": {"name": "pull_render_outputs", "arguments": "{\"run\":\"S06\",\"shot\":4,\"kind\":\"video\"}"}}]
  ```
- **json_shape** score=1.0 — array of 6, keys ok
  ```
   [
  
  {
    "shot_id": "S06E01",
    "setup_id": "Setup01",
    "camera": "Close-up on protagonist's face, slow pan left to reveal antagonist",
    "action": "Protagonist confronts antagonist",
    "soundscape": "Tense background music, footsteps echoing",
    "music": "Dramatic orchestral score"
  },
  {
    "shot_id": "S06E02",
    "setup_id": "Setup02",
    "camera": "Medium shot of protagonist and antagonist, steady camera",
    "action": "Antagonist reveals a secret",
    "soundscape": "Low whispers, ominous ambient sounds",
    "music": "Suspenseful piano music"
  },
  {
    "shot_id": "S06E03",
    "setup_id": "Setup03",
    "camera": "Wide shot of the room, camera zooms in on a crucial object",
    "action": "Protagonist picks up the object",
    "soundscape": "Silence, except for the sound of the object being picked up",
    "music": "No music"
  },
  {
    "shot_id": "S06E04",
    "setup_id": "Setup04",
    "camera": "Close-up on the object, camera pans out to reveal a map",
    "action": "Protagonist studies the map",
    "soundscape": "Background noise of wind and rain",
    "music": "Melancholic violin music"
  },
  {
    "shot_id": "S06E05",
    "setup_id": "Setup05",
    "camera": "Aerial shot of the location marked on the map",
    "action": "Protagonist sets off towards the location",
    "soundscape": "Birds chirping, footsteps in the forest",
    "music": "Adventurous instrumental music"
  },
  {
    "shot_id": "S06E06",
    "setup_id": "Setup06",
    "camera": "Close-up on protagonist's face, camera pans out to reveal the destination",
    "action": "Protagonist reaches the destination",
    "soundscape": "Silence, except for the sound of wind",
    "music": "Dramatic orchestral music swells"
  }
  ]
  ```
- **h3_3field** score=0.83 — all_three_fields=Y, field_order=Y, no_dead_video_ref=Y, no_shot1_timestamp=Y, single_camera_move=N, substantive=Y [cams=[]]
  ```
   integrated_multimodal_description:
  In Scene S06, setup S06-A, we find ourselves in an icy cavern with a warm torch pool on the right wall and cold blue falloff behind. The camera is positioned low, providing a unique perspective. Two characters are present: Darkwolf, a large, bare-chested man with black mane and war paint, holding an axe; Teegra, tall with dark hair and light blue wrap, barefoot. The duration of the shot is 5.00 seconds, tasked to capture a two-shot at the cavern mouth during the FL2VA sequence. The audio includes wind, distant cracking ice, and a low drone under.
  
  overall_soundscape:
  Wind, distant cracking ice, low drone under
  
  non_diegetic_music:
  None specified in the prompt
  ```

### supergemma4-e4b-abliterated
load_ok=True load_s=6.5 quant=F16
- **echo_identifiers** score=1.0 — 12/12 exact
  ```
  ```json
  {
    "echo": [
      "E:\\FNI\\refs\\setups\\S06-A_plate.jpg",
      "qwen3.8-flash-next@q8_0",
      "delegation.fallback_providers[0].model",
      "shot_01243_f00059.jpg",
      "S05-c04_ref.mp4",
      "text-embedding-nomic-embed-text-v1.5",
      "100.104.7.72:8188",
      "graph_length_frames",
      "integrated_multimodal_description",
      "retention_analysis",
      "0.00-second",
      "<d>[English] By the frozen sea.</d>"
    ]
  }
  ```
  ```
- **tool_call** score=1.0 — pull_render_outputs({'kind': 'video', 'run': 'S06', 'shot': 4})
  ```
  [{"type": "function", "id": "eUFzc05ZDe4xGD0bpYhwABEYmDxRnJ3f", "function": {"name": "pull_render_outputs", "arguments": "{\"kind\":\"video\",\"run\":\"S06\",\"shot\":4}"}}]
  ```
- **json_shape** score=0.0 — unparseable JSON
  ```
  ```json
  [
    {
      "shot_id": "S06-1",
      "setup_id": "A",
      "camera": "Dolly out",
      "action": "Character enters frame from the left.",
      "soundscape": "City traffic hums loudly in the background.",
      "music": "Upbeat strings begin softly, setting a hopeful tone."
    },
    {
      "shot_id": "S06-2",
      "setup_id": "B",
      "camera": "Pan left",
      "action": "Character gestures emphatically toward the skyline.",
      "soundscape": "Footsteps echo sharply on the wet pavement.",
      "music": "Percussion drives the rhythm, building tension."
    },
    {
      "shot_id": "S06-3",
      "setup_id": "C",
      "camera": "Static shot",
      "action": "Character adjusts their collar nervously.",
      "soundscape": "Wind whistles through the narrow alleyway.",
      "music": "A melancholic piano chord rings out, lingering in the air."
    },
    {
      "shot_id": "S06-4",
      "setup_id": "D",
      "camera": "Steadicam follow",
      "action": "Character walks quickly toward the camera lens.",
      "soundscape": "Heavy breathing is audible, indicating urgency.",
      "music": "The tempo increases rapidly as they approach."
    },
    {
      "shot_id": "S06-5",
      "setup_id":
  ```
- **h3_3field** score=0.83 — all_three_fields=Y, field_order=Y, no_dead_video_ref=Y, no_shot1_timestamp=Y, single_camera_move=N, substantive=Y [cams=[]]
  ```
  integrated_multimodal_description:A low-angle shot inside a massive ice cavern. The scene is dramatically lit by a warm torch pool on the right wall, casting deep shadows and highlighting the rough texture of the glacial ice. Behind them, the environment falls away into cold, ethereal blue darkness. DARKWOLF, a large, bare-chested warrior with a black mane and war paint, stands ready, axe held in his right hand. TEEGRA, tall and lean, wears a light blue wrap and is barefoot. The camera slowly tracks or pans from a close focus on the cavern interior to reveal both characters framed by the mouth of the cavern, transitioning into a two-shot that emphasizes their position relative to the outside world.
  overall_soundscape:Wind howling through the ice cave, punctuated by the sharp, distant cracking sounds of fracturing glacial ice.
  non_diegetic_music:Low, resonant drone providing an underlying sense of tension and ancient power.
  ```

### qwen3-vl-8b-instruct-abliterated-v2.0@f16
load_ok=True load_s=16.0 quant=F16
- **echo_identifiers** score=1.0 — 12/12 exact
  ```
  {"echo": ["E:\\FNI\\refs\\setups\\S06-A_plate.jpg", "qwen3.8-flash-next@q8_0", "delegation.fallback_providers[0].model", "shot_01243_f00059.jpg", "S05-c04_ref.mp4", "text-embedding-nomic-embed-text-v1.5", "100.104.7.72:8188", "graph_length_frames", "integrated_multimodal_description", "retention_analysis", "0.00-second", "<d>[English] By the frozen sea.</d>"]}
  ```
- **tool_call** score=1.0 — pull_render_outputs({'run': 'S06', 'shot': 4, 'kind': 'video'})
  ```
  [{"type": "function", "id": "5qCQs6VxcF08Jim62M7gu5rq4pDcjmb7", "function": {"name": "pull_render_outputs", "arguments": "{\"run\":\"S06\",\"shot\":4,\"kind\":\"video\"}"}}]
  ```
- **json_shape** score=1.0 — array of 6, keys ok
  ```
  [{"shot_id":1,"setup_id":1,"camera":"dolly in","action":"man adjusts tie","soundscape":"soft footsteps on marble","music":"piano motif fades"},{"shot_id":2,"setup_id":2,"camera":"pan right","action":"woman enters frame","soundscape":"door creaks open","music":"strings swell gently"},{"shot_id":3,"setup_id":3,"camera":"tilt up","action":"clock ticks overhead","soundscape":"distant city hum","music":"orchestral crescendo begins"},{"shot_id":4,"setup_id":4,"camera":"zoom out","action":"couple embraces","soundscape":"breathless sighs","music":"melancholic violin solo"},{"shot_id":5,"setup_id":5,"camera":"handheld shake","action":"man drops phone","soundscape":"glass shatters","music":"dissonant chord strikes"},{"shot_id":6,"setup_id":6,"camera":"static wide","action":"silence falls","soundscape":"wind whispers through trees","music":"single sustained note fades to nothing"}]
  ```
- **h3_3field** score=0.83 — all_three_fields=Y, field_order=Y, no_dead_video_ref=Y, no_shot1_timestamp=Y, single_camera_move=N, substantive=Y [cams=[]]
  ```
  integrated_multimodal_description: Darkwolf, bare-chested with black mane and war paint, grips an axe as he stands in a cavernous ice chamber; Teegra, tall and barefoot in a light blue wrap, stands beside him. Warm torchlight pools on the right wall while cold blue shadows recede behind them. The camera starts low at plate level and slowly rises to a two-shot framing both characters near the cavern mouth as wind howls and distant ice cracks echo.
  
  overall_soundscape: Wind whistling through crevices, intermittent cracking of ice under pressure, deep subsonic drone vibrating beneath all sounds.
  
  non_diegetic_music: None — ambient natural sound only.
  ```
- **vision_caption** score=1.0 — json_line=Y, has_colors=Y, has_subjects=Y, prose=Y
  ```
  This image is a character design sheet for a female figure. It includes multiple views: a front-facing close-up portrait, full-body front view, side profile, and back view. The character has short black hair with bangs, dark brown skin, and wears a light blue top with lacing across the chest and a matching draped skirt or wrap. She also wears a gold-colored choker necklace. Additional panels show detailed close-ups of her eye (with long lashes), lips (dark red), ear, skin texture, and part of the belt/necklace detail.
  
  There is no visible weapon in any of the views.
  The camera perspective varies: portrait is frontal, full-body views are straight-on or side profile.
  The style is 2D cartoon animation with clean lines and flat color fills.
  
  {"shot_type": "character sheet", "subjects": 1, "characters": ["female"], "weapon_visible": false, "weapon": "", "colors": {"skin": "brown", "hair": "black", "top": "light blue", "bottom": "light blue", "background": "white"}, "camera": "frontal and side profile", "style": "2D cartoon"}
  ```
- **vision_colors** score=1.0 — 6 regions
  ```
  hair: black
  skin: brown
  top garment: blue
  bottom garment: blue
  background: white
  any metal or accessory: brown
  ```
- **vision_stability** score=0.55 — jaccard vs temp0 = 0.55
  ```
  This image is a character design sheet for a single female character shown from multiple angles: front view (large), three-quarter front, side profile, and back view. The character has dark brown skin, short black bob-style hair with bangs, and wears a light blue two-piece outfit consisting of a corset top with lacing details and a flowing skirt. She also wears a gold-colored choker necklace. Close-up panels show detailed facial features: an eye with long lashes, lips with red lipstick, an ear, a plain black circle (possibly representing skin tone or shadow), textured skin lines, and the edge of her necklace showing three circular gold elements.
  
  The character is standing barefoot against a white background. No weapons are visible in any view. The style is clean, stylized 2D animation with bold outlines and flat color fills. The camera perspective varies across views: frontal close-up, full-body front-three-quarters, profile side-view, and back three-quarter view.
  
  {"shot_type": "character design sheet", "subjects": 1, "characters": ["female"], "weapon_visible": false, "weapon": "", "colors": {"skin": "brown", "hair": "black", "top": "light blue", "bottom": "light blue", "background": "white"}, "camera": "multiple angles including front close-up and full-body views", "style": "stylized 2D animation"}
  ```

### qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s
load_ok=True load_s=6.0 quant=Q4_K_S
- **echo_identifiers** score=1.0 — 12/12 exact
  ```
  {"echo": ["E:\\FNI\\refs\\setups\\S06-A_plate.jpg", "qwen3.8-flash-next@q8_0", "delegation.fallback_providers[0].model", "shot_01243_f00059.jpg", "S05-c04_ref.mp4", "text-embedding-nomic-embed-text-v1.5", "100.104.7.72:8188", "graph_length_frames", "integrated_multimodal_description", "retention_analysis", "0.00-second", "<d>[English] By the frozen sea.</d>"]}
  ```
- **tool_call** score=1.0 — pull_render_outputs({'run': 'S06', 'shot': 4, 'kind': 'video'})
  ```
  [{"type": "function", "id": "Ebcfgb0jP8BlrU9xVDHOrSUNX1IAfP4G", "function": {"name": "pull_render_outputs", "arguments": "{\"run\":\"S06\",\"shot\":4,\"kind\":\"video\"}"}}]
  ```
- **json_shape** score=1.0 — array of 6, keys ok
  ```
  [{"shot_id":1,"setup_id":1,"camera":"dolly in","action":"character walks toward camera","soundscape":"footsteps on pavement","music":"piano melody begins"},{"shot_id":2,"setup_id":2,"camera":"pan right","action":"character turns to look at window","soundscape":"wind chimes faintly","music":"melody swells slightly"},{"shot_id":3,"setup_id":3,"camera":"tilt up","action":"character raises hand to adjust hat","soundscape":"bird chirps overhead","music":"strings enter softly"},{"shot_id":4,"setup_id":4,"camera":"handheld shake","action":"character stumbles and catches self","soundscape":"rustling leaves","music":"beat drops abruptly"},{"shot_id":5,"setup_id":5,"camera":"zoom out","action":"character steps back from wall","soundscape":"door creaks open","music":"melody fades to silence"},{"shot_id":6,"setup_id":6,"camera":"static wide","action":"character stands still facing camera","soundscape":"rain begins falling","music":"piano returns alone"}]
  ```
- **h3_3field** score=0.83 — all_three_fields=Y, field_order=Y, no_dead_video_ref=Y, no_shot1_timestamp=Y, single_camera_move=N, substantive=Y [cams=[]]
  ```
  integrated_multimodal_description: Darkwolf, bare-chested with black mane and war paint, grips an axe as he stands in a low-angle shot within a cold ice cavern; TEEGRA, tall with dark hair and light blue wrap, stands beside him. Warm torchlight pools on the right wall while icy blue falloff dominates behind them. The camera slowly transitions from a plate shot to a two-shot at the cavern mouth over 5 seconds. Wind, cracking ice, and low drone underpin the scene.
  
  overall_soundscape: wind, distant cracking ice, low drone
  
  non_diegetic_music: none
  ```
- **vision_caption** score=1.0 — json_line=Y, has_colors=Y, has_subjects=Y, prose=Y
  ```
  This image is a character design sheet for a female figure with dark skin and short black hair. It includes multiple views: front-facing close-up, full frontal view, side profile, and back view. The character wears a light blue top with lacing details and a matching long skirt or wrap, along with a brown collar necklace. Additional panels show facial features (eye, lips), an ear, skin texture, and the pattern of the necklace.
  
  There is no visible weapon. The camera perspective appears to be flat, illustrative, and designed for animation reference. The style is clean, stylized cartooning with bold outlines.
  
  {"shot_type": "character sheet", "subjects": 1, "characters": ["female"], "weapon_visible": false, "weapon": "", "colors": {"skin": "brown", "hair": "black", "top": "light blue", "bottom": "light blue", "background": "white"}, "camera": "flat illustration", "style": "stylized cartoon"}
  ```
- **vision_colors** score=1.0 — 6 regions
  ```
  hair: black
  skin: brown
  top garment: light blue
  bottom garment: light blue
  background: white
  any metal or accessory: brown
  ```
- **vision_stability** score=0.53 — jaccard vs temp0 = 0.53
  ```
  This image is a character design sheet for a female character with dark skin and short black hair. It shows the character from multiple angles: front-facing close-up, full frontal view, three-quarter side profile, and back view. She wears a light blue top with brown lacing details across the chest and a matching light blue skirt or wrap. Around her neck is a thick gold-colored collar necklace. The sheet also includes detail shots of her eye (with long lashes), lips (dark red), ear, skin texture, and decorative elements including circular patterns on her clothing.
  
  There are no visible weapons.
  The character has one subject shown in multiple views.
  No characters other than the main female figure are visible.
  
  {
    "shot_type": "concept sheet",
    "subjects": 1,
    "characters": ["female character"],
    "weapon_visible": false,
    "weapon": "",
    "colors": {
      "skin": "brown",
      "hair": "black",
      "top": "light blue",
      "bottom": "light blue",
      "background": "white"
    },
    "camera": "multiple angles including front, side, and back views",
    "style": "cartoon/animation design sheet"
  }
  ```

### q3.5-bluestar-v2-27b
load_ok=True load_s=12.8 quant=Q5_K_M
- **echo_identifiers** score=1.0 — 12/12 exact
  ```
  {"echo": ["E:\\FNI\\refs\\setups\\S06-A_plate.jpg", "qwen3.8-flash-next@q8_0", "delegation.fallback_providers[0].model", "shot_01243_f00059.jpg", "S05-c04_ref.mp4", "text-embedding-nomic-embed-text-v1.5", "100.104.7.72:8188", "graph_length_frames", "integrated_multimodal_description", "retention_analysis", "0.00-second", "<d>[English] By the frozen sea.</d>"]}
  ```
- **tool_call** score=1.0 — pull_render_outputs({'run': 'S06', 'shot': 4, 'kind': 'video'})
  ```
  [{"type": "function", "id": "fUyFoj7HjyPySphum5YQa8bX1q985khz", "function": {"name": "pull_render_outputs", "arguments": "{\"run\":\"S06\",\"shot\":4,\"kind\":\"video\"}"}}]
  ```
- **json_shape** score=0.0 — unparseable JSON
  ```
  
  ```
- **h3_3field** score=0.33 — all_three_fields=N, field_order=N, no_dead_video_ref=Y, no_shot1_timestamp=Y, single_camera_move=N, substantive=N [cams=[]]
  ```
  
  ```

### qwq-32b-arliai-rpr-v4
load_ok=True load_s=12.8 quant=Q4_K_S
- **echo_identifiers** score=1.0 — 12/12 exact
  ```
  
  
  {"echo": ["E:\\FNI\\refs\\setups\\S06-A_plate.jpg", "qwen3.8-flash-next@q8_0", "delegation.fallback_providers[0].model", "shot_01243_f00059.jpg", "S05-c04_ref.mp4", "text-embedding-nomic-embed-text-v1.5", "100.104.7.72:8188", "graph_length_frames", "integrated_multimodal_description", "retention_analysis", "0.00-second", "<d>[English] By the frozen sea.</d>"]}
  ```
- **tool_call** score=1.0 — pull_render_outputs({'run': 'S06', 'shot': 4, 'kind': 'video'})
  ```
  
  
  
  ```
- **json_shape** score=1.0 — array of 6, keys ok
  ```
  
  
  [
      {
          "shot_id": "S06-1",
          "setup_id": "S06-SETUP-1",
          "camera": "pan",
          "action": "crouching",
          "soundscape": "rustling leaves and a sudden gasp",
          "music": "subtle strings building tension"
      },
      {
          "shot_id": "S06-2",
          "setup_id": "S06-SETUP-1",
          "camera": "tilt",
          "action": "gasping",
          "soundscape": "rustling leaves and a sudden gasp",
          "music": "subtle strings building tension"
      },
      {
          "shot_id": "S06-3",
          "setup_id": "S06-SETUP-1",
          "camera": "dolly",
          "action": "running",
          "soundscape": "rustling leaves and a sudden gasp",
          "music": "subtle strings building tension"
      },
      {
          "shot_id": "S06-4",
          "setup_id": "S06-SETUP-1",
          "camera": "track",
          "action": "jumping",
          "soundscape": "rustling leaves and a sudden gasp",
          "music": "subtle strings building tension"
      },
      {
          "shot_id": "S06-5",
          "setup_id": "S06-SETUP-1",
          "camera": "crane",
          "action": "crouching",
          "soundscape": "rustling leaves and a sudden gasp",
          "music": "subtle strings building tension"
      },
      {
          "shot_id": "S06-6",
          "setup_id": "S06-SETUP-1",
          "camera": "close-up",
          "action": "gasping",
          "soundscape": "rustling leaves and a sudden gasp",
          "music": "subtle strings building tension"
      }
  ]
  ```
- **h3_3field** score=0.83 — all_three_fields=Y, field_order=Y, no_dead_video_ref=Y, no_shot1_timestamp=Y, single_camera_move=N, substantive=Y [cams=[]]
  ```
  
  
  integrated_multimodal_description: The camera starts at a low angle in an icy cavern with warm torch light on the right wall and cold blue falloff behind. Darkwolf stands bare-chested with a black mane and axe in hand, wearing war paint. Teeegra is tall with dark hair, a light blue wrap, and bare feet. Over 5 seconds, the camera moves from the first frame to a two-shot at the cavern mouth.
  overall_soundscape: The soundscape includes wind howling through the icy cavern, distant cracking ice like thunder in the distance, and a low drone under it all.
  non_diegetic_music: A haunting melody plays on non-diegetic music.
  ```

## Colour answers on the baseline image

- **qwen2.5-vl-32b-instruct-abliterated**: hair=black; skin=brown; top garment=blue; bottom garment=blue; background=white; metal or accessory=gold
- **qwen3.8-27b-obliterated**: hair=black; skin=brown; top garment=light blue; bottom garment=light blue; background=white; any metal or accessory=gold
- **qwen3-vl-8b-instruct-abliterated-v2.0@f16**: hair=black; skin=brown; top garment=blue; bottom garment=blue; background=white; any metal or accessory=brown
- **qwen3-vl-8b-instruct-abliterated-v2.0@q4_k_s**: hair=black; skin=brown; top garment=light blue; bottom garment=light blue; background=white; any metal or accessory=brown