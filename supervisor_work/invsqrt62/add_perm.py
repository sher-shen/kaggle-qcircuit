"""Add 'perm' (the block permutation on 2^n patterns, block_extract2.perm_bits) to every block of a blocks json.
Usage: add_perm.py ops.json blocks.json out.json"""
import json, sys
here = __file__.rsplit('/', 1)[0] + '/'
opsf, bf, outf = sys.argv[1:4]
sys.argv = ['x', opsf, '0', '0', '/dev/null']
exec(open(here + 'block_extract2.py').read().split('seen = {}')[0])
B = json.load(open(bf))
for b in B: b['perm'] = perm_bits(b['W'], b['ops'])[1].tolist()
json.dump(B, open(outf, 'w'))
