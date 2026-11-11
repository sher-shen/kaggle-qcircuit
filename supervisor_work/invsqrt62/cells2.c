/* cells2: enumerate 2-dim spaces H = span{h1,h2} of linear forms on F2^m (h1 < h2 < h1^h2 canonical, plus 1-dim H = {h1})
   and print those for which no violating quad is inside one coset of H^perp, i.e. there is no quad i with
   h.s1_i = h.s2_i = 0 for all h in H.  Input: m nq, then nq lines "s1 s2" (ints).  Output: surviving "h1 h2" (h2 = 0: 1-dim).
   Args: [start step] to split the h1 range over processes. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
static inline int dot(uint32_t a, uint32_t b) { return __builtin_popcount(a & b) & 1; }
int main(int argc, char **argv) {
  int m, nq; if (scanf("%d %d", &m, &nq) != 2) return 1;
  uint32_t *s1 = malloc(4 * nq), *s2 = malloc(4 * nq), *t1 = malloc(4 * nq), *t2 = malloc(4 * nq);
  for (int i = 0; i < nq; i++) if (scanf("%u %u", &s1[i], &s2[i]) != 2) return 1;
  uint32_t st = argc > 1 ? atoi(argv[1]) : 0, step = argc > 2 ? atoi(argv[2]) : 1, N = 1u << m;
  long surv = 0;
  for (uint32_t h1 = 1 + st; h1 < N; h1 += step) {
    int k = 0;
    for (int i = 0; i < nq; i++) if (!dot(h1, s1[i]) && !dot(h1, s2[i])) { t1[k] = s1[i]; t2[k] = s2[i]; k++; }
    if (k == 0) { printf("%u 0\n", h1); surv++; continue; }
    for (uint32_t h2 = h1 + 1; h2 < N; h2++) {
      if ((h1 ^ h2) < h2) continue;
      int ok = 1;
      for (int i = 0; i < k; i++) {
        /* H inside s^perp iff h2 also orthogonal (h1 already is, hence h1^h2 too) */
        if (!dot(h2, t1[i]) && !dot(h2, t2[i])) { ok = 0; break; }
      }
      if (ok) { printf("%u %u\n", h1, h2); surv++; }
    }
  }
  fprintf(stderr, "survivors %ld\n", surv);
  return 0;
}
