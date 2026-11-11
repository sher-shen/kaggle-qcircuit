/* cells2b: cells2 + the exact per-cell test in C (no Python survivor loop; needed at m = 20 where ~1.6M H survive the quad prune).
   Input: m nq, nq lines "s1 s2", then np, np lines "y f" (hull coords y < 2^m, residue bit f).
   For each surviving H = span{h1,h2} (h2 = 0: 1-dim) test whether f is affine on each of the 4 cells (h1.y, h2.y):
   incremental GF(2) elimination of (1,y,f); a vector reducing to the bare f bit means a dependency with odd f-sum.
   Output: "HIT h1 h2" lines; stderr: survivors / hits.  Args: [start step]. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
static inline int dot(uint32_t a, uint32_t b) { return __builtin_popcount(a & b) & 1; }
static int np_; static uint32_t *py; static int *pf; static int M;
static int cell_affine(uint32_t h1, uint32_t h2) {
  uint64_t basis[4][64]; int nb[4] = {0, 0, 0, 0};
  for (int p = 0; p < np_; p++) {
    int c = dot(h1, py[p]) | (h2 ? dot(h2, py[p]) << 1 : 0);
    /* vector: bit0 = f, bits 1..M = y, bit M+1 = const 1 */
    uint64_t v = (uint64_t)pf[p] | ((uint64_t)py[p] << 1) | (1ull << (M + 1));
    for (int i = 0; i < nb[c]; i++) { uint64_t b = basis[c][i]; uint64_t hb = 1ull << (63 - __builtin_clzll(b)); if (v & hb) v ^= b; }
    if (v == 1) return 0;
    if (v) {
      /* keep basis sorted by leading bit descending for a single pass reduction */
      int i = nb[c]++; while (i > 0 && (63 - __builtin_clzll(basis[c][i - 1])) < (63 - __builtin_clzll(v))) { basis[c][i] = basis[c][i - 1]; i--; }
      basis[c][i] = v;
    }
  }
  return 1;
}
int main(int argc, char **argv) {
  int m, nq; if (scanf("%d %d", &m, &nq) != 2) return 1; M = m;
  uint32_t *s1 = malloc(4 * nq + 4), *s2 = malloc(4 * nq + 4), *t1 = malloc(4 * nq + 4), *t2 = malloc(4 * nq + 4);
  for (int i = 0; i < nq; i++) if (scanf("%u %u", &s1[i], &s2[i]) != 2) return 1;
  if (scanf("%d", &np_) != 1) return 1; py = malloc(4 * np_); pf = malloc(sizeof(int) * np_);
  for (int i = 0; i < np_; i++) if (scanf("%u %d", &py[i], &pf[i]) != 2) return 1;
  uint32_t st = argc > 1 ? atoi(argv[1]) : 0, step = argc > 2 ? atoi(argv[2]) : 1, N = 1u << m;
  long surv = 0, hits = 0;
  for (uint32_t h1 = 1 + st; h1 < N; h1 += step) {
    int k = 0;
    for (int i = 0; i < nq; i++) if (!dot(h1, s1[i]) && !dot(h1, s2[i])) { t1[k] = s1[i]; t2[k] = s2[i]; k++; }
    if (k == 0) { surv++; if (cell_affine(h1, 0)) { printf("HIT %u 0\n", h1); hits++; } continue; }
    for (uint32_t h2 = h1 + 1; h2 < N; h2++) {
      if ((h1 ^ h2) < h2) continue;
      int ok = 1;
      for (int i = 0; i < k; i++) if (!dot(h2, t1[i]) && !dot(h2, t2[i])) { ok = 0; break; }
      if (ok) { surv++; if (cell_affine(h1, h2)) { printf("HIT %u %u\n", h1, h2); hits++; } }
    }
  }
  fprintf(stderr, "survivors %ld hits %ld\n", surv, hits);
  return 0;
}
