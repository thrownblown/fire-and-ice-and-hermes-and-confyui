"""Motion-context chaining for FNI graphs.

Rewires a built FL2VA or REF2VA API graph into a single link of an H3 Motion
Context chain. Both fullrun.build_graph and refrun.build_ref_graph use the
same node ids (136 = conditioning node, 125 = sampler, 126 = guider, 121/122 =
audio/video decode, 130 = CreateVideo), so one function covers both.

Chain mechanics (from ComfyUI-H3-Motion-Context, which is already installed on
the 5090):
  - The previous clip's SAMPLER OUTPUT latent is saved to a numbered slot; this
    clip loads slot N-1 and pins its head frames as never-denoised conditioning
    rows, so the model reads REAL motion (and with context_latent, real sound)
    instead of guessing from a still.
  - The pinned head is trimmed off the delivered clip (picture + sound, same
    duration). A first_frame anchor is DROPPED by the node (the pinned head owns
    those frames); a last_frame anchor is kept.
  - clip_index on Load = the clip you continue FROM; on Save = the clip this IS.
    First clip of a chain: Load 0, Save 1 (Load 0 reads no file, passes
    conditioning through, trim_frames 0).

Settings (pack author's recommendation): context_length 22, audio_context_length
24 (1s, lands on the model's 40 Hz audio grid). Leave context_frames/context_audio
unwired — the latent path is lossless (no decode/re-encode round trip).
"""
import copy


def chainify(graph, clip_index, chain_name, clip_id=None, context_length="22",
             audio_context_length=24, save_untrimmed=True):
    """Return a copy of `graph` rewired as chain link `clip_index` (1-based).

    clip_id: per-link label used for the untrimmed-audio sidecar filename (so
    each link's seam-probe audio lands in its own file). Defaults to chain_name.
    """
    g = copy.deepcopy(graph)

    g["150"] = {
        "inputs": {
            "conditioning": ["136", 0],
            "vae": ["119", 0],
            "latent": ["136", 1],
            "context_latent": ["152", 0],
            "audio_vae": ["120", 0],
            "context_length": context_length,
            "audio_context_length": audio_context_length,
        },
        "class_type": "MiniMaxH3MotionContext",
        "_meta": {"title": "H3 Motion Context"},
    }

    # guider now reads the pinned-head conditioning, not the raw model output
    g["126"]["inputs"]["conditioning"] = ["150", 0]

    # save THIS clip's sampler-output latent into its slot (re-roll overwrites it)
    g["151"] = {
        "inputs": {
            "latent": ["125", 0],
            "filename_prefix": "h3_context/%s/clip" % chain_name,
            "clip_index": clip_index,
        },
        "class_type": "MiniMaxH3MotionContextSaveLatent",
        "_meta": {"title": "H3 Motion Context Save Latent"},
    }

    # load the PREVIOUS clip's latent (0 = none, first link)
    g["152"] = {
        "inputs": {
            "latent_path": "h3_context/%s" % chain_name,
            "clip_index": clip_index - 1,
        },
        "class_type": "MiniMaxH3MotionContextLoadLatent",
        "_meta": {"title": "H3 Motion Context Load Latent"},
    }

    # trim the pinned head off picture and sound before saving the clip
    g["153"] = {
        "inputs": {
            "images": ["122", 0],
            "audio": ["121", 0],
            "trim_frames": ["150", 1],
            "fps": 24.0,
            "match_tail": True,
        },
        "class_type": "MiniMaxH3MotionContextTrim",
        "_meta": {"title": "H3 Motion Context Trim"},
    }

    # CreateVideo consumes the trimmed streams
    g["130"]["inputs"]["images"] = ["153", 0]
    g["130"]["inputs"]["audio"] = ["153", 1]

    # branch the UNTRIMMED audio so the seam probe can measure this join against
    # the previous clip's tail (seam_probe.py: corr high + lag ~0 = clean)
    if save_untrimmed:
        g["154"] = {
            "inputs": {
                "audio": ["121", 0],
                "filename_prefix": "audio/%s_untrimmed" % (clip_id or chain_name),
            },
            "class_type": "SaveAudio",
            "_meta": {"title": "Save Untrimmed Audio (seam probe)"},
        }

    return g