
from PIL import Image
import os
B = r"E:\FNI\stills\boundary"
scenes = {"S02": [16,17,18,19,20,21,22,23,24,25,26,27],
          "S06": [197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220]}
for sc, nums in scenes.items():
    imgs = []
    for n in nums:
        p = os.path.join(B, f"shot_{n:05d}_first.jpg")
        im = Image.open(p).convert("RGB")
        im.thumbnail((260, 160))
        imgs.append(im)
    cols = 6
    rows = (len(imgs) + cols - 1)//cols
    W, H = 260*cols, 160*rows
    sheet = Image.new("RGB", (W, H), (20,20,20))
    for i, im in enumerate(imgs):
        sheet.paste(im, ((i%cols)*260, (i//cols)*160))
    # draw shot numbers
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(nums):
        d.text(((i%cols)*260+4, (i//cols)*160+4), f"{n}", fill=(255,255,0))
    out = os.path.join(r"E:\FNI\runs\setups_v2", f"contact_{sc}.jpg")
    sheet.save(out, quality=88)
    print(out)
