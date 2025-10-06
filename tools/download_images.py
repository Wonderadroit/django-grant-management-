import os
import sys
import urllib.request

BASE = os.path.dirname(os.path.dirname(__file__))
DEST = os.path.join(BASE, 'core', 'static', 'images')
urls = [
    ('https://images.unsplash.com/photo-1509475826633-fed577a2c71b?auto=format&fit=crop&w=1400&q=80', 'hero.jpg'),
    ('https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=800&q=80', 'testimonial1.jpg'),
    ('https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=800&q=80', 'testimonial2.jpg'),
    ('https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=800&q=80', 'testimonial3.jpg'),
]

os.makedirs(DEST, exist_ok=True)

headers = {'User-Agent': 'Mozilla/5.0 (compatible; ImageDownloader/1.0)'}

failed = []
for url, fname in urls:
    dest_path = os.path.join(DEST, fname)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(dest_path, 'wb') as out:
                out.write(resp.read())
        print('Saved', dest_path)
    except Exception as e:
        print('Failed to download', url, '->', dest_path, '(', e, ')')
        failed.append((url, str(e)))

if failed:
    print('\nSome downloads failed:')
    for u, e in failed:
        print('-', u, e)
    sys.exit(2)

print('\nAll images downloaded successfully.')
