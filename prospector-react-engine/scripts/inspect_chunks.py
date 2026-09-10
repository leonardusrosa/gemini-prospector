import glob, re

for f in glob.glob('out/_next/static/chunks/*.js'):
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        c = fp.read()
    # Find package names or node_modules paths
    node_mods = set(re.findall(r'node_modules/([a-zA-Z0-9_\-@/]+)', c))
    sample = list(node_mods)[:8]
    print(f, 'len:', len(c), 'sample node_modules:', sample)
