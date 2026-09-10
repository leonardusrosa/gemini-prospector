import glob

for f in sorted(glob.glob('out/_next/static/chunks/*.js')):
    with open(f, 'r', encoding='utf-8', errors='ignore') as fp:
        c = fp.read(400)
    print("=== " + f + " ===")
    print(c[:300])
    print()
