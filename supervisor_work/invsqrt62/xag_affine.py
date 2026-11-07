"""Parse lut_extract_xag.py Verilog into an AND-level affine form.
Every signal = const ^ XOR of {PIs, AND outputs}. Variables: bit 0..7 = x0..x7, bit 8+i = AND i.
Writes npz: A0,A1 (int objects as hex strings), C0,C1 (consts), Y (outputs), YC.
Usage: python3 xag_affine.py cl.v out.json"""
import re, sys, json
src = open(sys.argv[1]).read()
sig = {}
for i in range(8): sig[f'x{i}'] = (1 << i, 0)
ands = []
def val(t):
    t = t.strip(); neg = 0
    if t.startswith('~'): neg = 1; t = t[1:].strip()
    if t in ("1'b0", "0"): return (0, neg)
    if t in ("1'b1", "1"): return (0, 1 ^ neg)
    m, c = sig[t]; return (m, c ^ neg)
outs = {}
for line in src.splitlines():
    m = re.match(r'\s*assign\s+(\w+)\s*=\s*(.*);', line)
    if not m: continue
    lhs, rhs = m.group(1), m.group(2)
    if '&' in rhs:
        a, b = rhs.split('&'); va, vb = val(a), val(b)
        idx = len(ands); ands.append((va, vb)); r = (1 << (8 + idx), 0)
    elif '^' in rhs:
        a, b = rhs.split('^'); va, vb = val(a), val(b); r = (va[0] ^ vb[0], va[1] ^ vb[1])
    else:
        r = val(rhs)
    if lhs.startswith('y'): outs[int(lhs[1:])] = r
    else: sig[lhs] = r
json.dump({'ands': [[hex(a[0]), a[1], hex(b[0]), b[1]] for a, b in ands],
           'outs': [[hex(outs[k][0]), outs[k][1]] for k in sorted(outs)]}, open(sys.argv[2], 'w'))
print('ands', len(ands), 'outs', len(outs))
