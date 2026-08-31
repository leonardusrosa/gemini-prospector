import os
import pathlib
import subprocess

# Load environment variable without exposing or printing secrets
groq_key = os.environ.get('GROQ_API_KEY') or os.environ.get('AI_PROVIDER_API_KEY')
if not groq_key:
    for loc in ['E:/Antigravity/autocora/.env', 'E:/Antigravity/prospector/.env']:
        p = pathlib.Path(loc)
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith('GROQ_API_KEY='):
                    groq_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                    break

env = dict(os.environ)
if groq_key:
    env['GROQ_API_KEY'] = groq_key
    print('[RUNNER] GROQ_API_KEY loaded into test runner environment.')
else:
    print('[RUNNER] No AI provider key found in local environment.')

res = subprocess.run(['node', 'test_assistant_node.mjs'], cwd='E:/Antigravity/prospector-sites', env=env, capture_output=True, text=True)
print(res.stdout)
if res.stderr:
    print('STDERR:', res.stderr)
