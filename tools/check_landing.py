import time
import urllib.request

url = 'http://127.0.0.1:8000/'
max_attempts = 20
for i in range(max_attempts):
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='replace')
            print('STATUS', resp.status)
            print('LENGTH', len(html))
            print('\n-----SNIPPET-----\n')
            print(html[:800])
            raise SystemExit(0)
    except Exception as e:
        print(f'Attempt {i+1}/{max_attempts} failed: {e}')
        time.sleep(0.5)

print('Server did not respond in time')
raise SystemExit(2)
