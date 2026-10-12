import cv2
import numpy as np
from pathlib import Path

BOUND = Path(r"E:\FNI\stills\boundary")
W = 256

def gray_small(sid):
    p = BOUND / ("shot_%05d_first.jpg" % sid)
    img = cv2.imread(str(p))
    if img is None:
        return None
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h = int(g.shape[0] * W / g.shape[1])
    return cv2.resize(g, (W, h)).astype(np.float32)

def ssim(a, b):
    if a is None or b is None or a.shape != b.shape:
        return 0.0
    C1, C2 = (0.01*255)**2, (0.03*255)**2
    mu_a = cv2.GaussianBlur(a, (11,11), 1.5)
    mu_b = cv2.GaussianBlur(b, (11,11), 1.5)
    sa = cv2.GaussianBlur(a*a, (11,11),1.5) - mu_a*mu_a
    sb = cv2.GaussianBlur(b*b, (11,11),1.5) - mu_b*mu_b
    sab = cv2.GaussianBlur(a*b, (11,11),1.5) - mu_a*mu_b
    m = ((2*mu_a*mu_b+C1)*(2*sab+C2)) / ((mu_a**2+mu_b**2+C1)*(sa+sb+C2))
    return float(m.mean())

pairs_same = [(199,203),(199,205),(203,205),(202,204),(198,206),(207,209),(210,211),(17,18)]
pairs_diff = [(200,202),(200,204),(201,199),(201,203),(24,25),(23,26)]

print("SAME setup (should be HIGH SSIM):")
for a,b in pairs_same:
    print("  %d-%d: %.3f" % (a,b, ssim(gray_small(a), gray_small(b))))

print("DIFFERENT / reverse-angle (should be LOW SSIM):")
for a,b in pairs_diff:
    print("  %d-%d: %.3f" % (a,b, ssim(gray_small(a), gray_small(b))))