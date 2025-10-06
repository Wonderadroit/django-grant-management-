import os
from PIL import Image

BASE = os.path.dirname(os.path.dirname(__file__))
IMG_DIR = os.path.join(BASE, 'core', 'static', 'images')
OUT_META = os.path.join(IMG_DIR, 'metadata.json')

# Images to process and desired sizes (widths)
images = {
    'hero.jpg': [1400, 1000, 800],
    'testimonial1.jpg': [800, 400],
    'testimonial2.jpg': [800, 400],
    'testimonial3.jpg': [800, 400],
}

meta = {}

os.makedirs(IMG_DIR, exist_ok=True)

for name, sizes in images.items():
    src = os.path.join(IMG_DIR, name)
    if not os.path.exists(src):
        print('Skipping missing', src)
        continue
    try:
        with Image.open(src) as im:
            im = im.convert('RGB')
            w0, h0 = im.size
            meta[name] = {'original': {'width': w0, 'height': h0}}
            generated = []
            for w in sizes:
                if w >= w0:
                    # skip larger
                    continue
                ratio = w / w0
                h = int(h0 * ratio)
                out_name = f"{os.path.splitext(name)[0]}-{w}.jpg"
                out_path = os.path.join(IMG_DIR, out_name)
                im_resized = im.resize((w, h), Image.LANCZOS)
                im_resized.save(out_path, optimize=True, quality=85)
                generated.append({'file': out_name, 'width': w, 'height': h})
                # webp
                webp_name = f"{os.path.splitext(name)[0]}-{w}.webp"
                webp_path = os.path.join(IMG_DIR, webp_name)
                im_resized.save(webp_path, format='WEBP', quality=80)
                generated.append({'file': webp_name, 'width': w, 'height': h, 'webp': True})
            meta[name]['generated'] = generated
            print('Processed', name)
    except Exception as e:
        print('Error processing', name, e)

# write metadata
import json
with open(OUT_META, 'w', encoding='utf-8') as f:
    json.dump(meta, f, indent=2)

print('Wrote metadata to', OUT_META)
