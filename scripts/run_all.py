"""Run the whole analysis pipeline in order. Reads data/raw/, writes data/ and scripts/cache/."""
import subprocess, sys, os
here = os.path.dirname(os.path.abspath(__file__))
for step in ['01_point_pattern.py', '02_hex_hotspots.py', '03_river_distance.py', '04_build_web_data.py']:
    print('=' * 20, step, '=' * 20, flush=True)
    subprocess.run([sys.executable, os.path.join(here, step)], check=True, env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})
print('done: data/ rebuilt')
