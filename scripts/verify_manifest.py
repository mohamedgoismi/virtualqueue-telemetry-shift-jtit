"""Verify all archived non-manifest files against recorded SHA-256 hashes."""
from pathlib import Path
import hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
manifest=ROOT/'MANIFEST_SHA256.txt'
errors=[];count=0
for l in manifest.read_text().splitlines():
    if not l or l.startswith('#'): continue
    expected,rel=l.split('  ',1)
    p=ROOT/rel
    if not p.is_file(): errors.append('MISSING '+rel);continue
    actual=hashlib.sha256(p.read_bytes()).hexdigest()
    if expected!=actual: errors.append('CHANGED '+rel)
    count+=1
if errors:
    print('\n'.join(errors));sys.exit(1)
print('PASS verified',count,'files')
