"""Thermometer flags (10, flag k = [s > k]) <-> binary s (4 bits), s in 0..10.

`pack(b, flags, sb)`: sb (clean) := binary s, flags := 0.  `unpack` is its exact inverse.
Clifford CX network for sb, then ~10 Toffolis to clear the flags (relies on s <= 10).
"""
import kickmix as km

SB = {0: range(10), 1: (1, 3, 5, 7, 9), 2: (3, 7), 3: (7,)}


def _load_sb(b, flags, sb):
    for r, idx in SB.items():
        for i in idx:
            b.cx(flags[i], sb[r])


def _xor_preds(b, flags, sb):
    """flags[k] ^= [s > k] for every k (self-inverse given sb)."""
    s0, s1, s2, s3 = sb[0], sb[1], sb[2], sb[3]
    f = flags
    b.cx(s3, f[7])                                   # s>7  <=> s3
    b.cx(s2, f[3]); b.cx(s3, f[3])                   # s>3  <=> s2 xor s3 (exclusive)
    b.ccx(s3, s1, f[9])                              # s>9  <=> s=10
    b.cx(s0, s1); b.ccx(s3, s1, f[8]); b.cx(s0, s1)  # s>8  <=> s3 & (s0 xor s1)
    b.cx(s3, f[5]); b.ccx(s2, s1, f[5])              # s>5  <=> s3 | (s2 & s1)
    a = b.alloc_qubits(1)[0]
    b.init_and(s1, s0, a)                            # a = s0 & s1
    b.cx(s3, f[6]); b.ccx(s2, a, f[6])               # s>6  <=> s3 | (s2 & s1 & s0)
    b.cx(s3, s2)                                     # s2' = s2 xor s3 = [s>3]
    b.cx(s2, f[2]); b.cx(a, f[2]); b.ccx(s2, a, f[2])  # s>2 <=> s2' | a
    o = b.alloc_qubits(1)[0]
    b.cx(s0, o); b.cx(s1, o); b.cx(a, o)             # o = s0 | s1
    b.cx(s3, s2)                                     # restore s2
    b.cx(s3, f[4]); b.ccx(s2, o, f[4])               # s>4  <=> s3 | (s2 & (s0|s1))
    b.cx(s0, o); b.cx(s1, o); b.cx(a, o); b.free(o)
    b.del_and(s1, s0, a); b.free(a)
    b.cx(s3, s2)                                     # s2' = [s>3]
    b.cx(s1, f[1]); b.cx(s2, f[1]); b.ccx(s1, s2, f[1])  # s>1 <=> s1 | s2'
    u = b.alloc_qubits(1)[0]
    v = b.alloc_qubits(1)[0]
    b.init_and(s1, s2, v)
    b.cx(s1, u); b.cx(s2, u); b.cx(v, u)             # u = s1 | s2' = [s>1]
    b.cx(s0, f[0]); b.cx(u, f[0]); b.ccx(s0, u, f[0])  # s>0 <=> s0 | u
    b.cx(s1, u); b.cx(s2, u); b.cx(v, u); b.free(u)
    b.del_and(s1, s2, v); b.free(v)
    b.cx(s3, s2)                                     # restore s2


def pack(b, flags, sb):
    _load_sb(b, flags, sb)
    _xor_preds(b, flags, sb)


def unpack(b, flags, sb):
    _xor_preds(b, flags, sb)
    _load_sb(b, flags, sb)


if __name__ == '__main__':
    b = km.CircuitBuilder()
    flags = b.create_quantum_register(10, name='flags'); sb = b.create_quantum_register(4, name='sb')
    pack(b, flags, sb)
    mid = b.create_quantum_register(1, name='m')
    c1 = b.finish_circuit()
    print('toffolis', c1.operation_statistics().num_toffoli_like)
    for s in range(11):
        th = (1 << s) - 1
        sim = km.Simulator(batch_size=64); sim.use_same_registers_as(c1)
        for shot in range(64): sim.write_within_shot('flags', shot, th)
        sim.do(c1)
        fl = {sim.read_within_shot('flags', i, out=int) for i in range(64)}
        sv = {sim.read_within_shot('sb', i, out=int) for i in range(64)}
        assert fl == {0} and sv == {s}, (s, fl, sv)
    b = km.CircuitBuilder()
    flags = b.create_quantum_register(10, name='flags'); sb = b.create_quantum_register(4, name='sb')
    unpack(b, flags, sb); c2 = b.finish_circuit()
    for s in range(11):
        sim = km.Simulator(batch_size=64); sim.use_same_registers_as(c2)
        for shot in range(64): sim.write_within_shot('sb', shot, s)
        sim.do(c2)
        fl = {sim.read_within_shot('flags', i, out=int) for i in range(64)}
        sv = {sim.read_within_shot('sb', i, out=int) for i in range(64)}
        assert fl == {(1 << s) - 1} and sv == {0}, (s, fl, sv)
    print('pack/unpack OK for s=0..10')
