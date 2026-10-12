# T0010 — motion-context chain vs frame anchoring

Same six S02 segments, seeds, and anchors as T0009; only the chaining
mechanism differs (context_latent pinned head vs first/last stills).

Note: links 2-6 are each 22 frames (0.92s) shorter than their sampled
length — the pinned head replaces the previous clip's tail, so total
video runs ~4.6s short vs T0009. The master-audio overlay starts at the
same source timecode either way.

Compare: T0010/S02_chain_audioA.mp4  vs  T0010/S02_anchored_audioA.mp4

Look for: joins playing as continuous MOTION (no restart), setup B
holding on return, and whether the 22-frame pinned head reads as a
seam or as a held beat. SeamProbe (seam_probe.py) quantifies the audio
joins from the *_untrimmed sidecars.
