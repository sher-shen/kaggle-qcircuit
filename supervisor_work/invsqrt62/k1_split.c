/* K=1 on don't-care set D: r|D = L + a*b (a, b, L affine)  <=>  some affine hyperplane a splits D into two parts on each of
   which r is affine.  Brute force over all linear masks a (2^n).  Input (stdin): n m, then m lines "pattern rbit".
   Output: number of masks that work (0 => no 1-Toffoli rewrite of the residue on D). */
#include <stdio.h>
#include <stdint.h>
static int aff(const uint32_t *x, const int *r, int m, int n) {
  uint32_t B[34]; int R[34], nb = 0;  /* basis rows over (x bits, const bit n) with r tag */
  for (int i = 0; i < m; i++) {
    uint32_t v = x[i] | (1u << n); int t = r[i];
    for (int k = 0; k < nb; k++) if ((v ^ B[k]) < v) { v ^= B[k]; t ^= R[k]; }
    if (v) { B[nb] = v; R[nb] = t; nb++;
      for (int a = nb - 1; a > 0 && B[a] > B[a-1]; a--) { uint32_t tv = B[a]; B[a] = B[a-1]; B[a-1] = tv; int tr = R[a]; R[a] = R[a-1]; R[a-1] = tr; } }
    else if (t) return 0;
  }
  return 1;
}
int main(void) {
  int n, m; if (scanf("%d %d", &n, &m) != 2) return 1;
  static uint32_t X[1 << 16], X0[1 << 16], X1[1 << 16]; static int Rr[1 << 16], R0[1 << 16], R1[1 << 16];
  for (int i = 0; i < m; i++) scanf("%u %d", &X[i], &Rr[i]);
  if (aff(X, Rr, m, n)) { printf("affine already\n"); return 0; }
  long hits = 0;
  for (uint32_t a = 1; a < (1u << n); a++) {
    int m0 = 0, m1 = 0;
    for (int i = 0; i < m; i++) { if (__builtin_parity(X[i] & a)) { X1[m1] = X[i]; R1[m1++] = Rr[i]; } else { X0[m0] = X[i]; R0[m0++] = Rr[i]; } }
    if (aff(X0, R0, m0, n) && aff(X1, R1, m1, n)) { if (hits < 5) printf("hit a=%u\n", a); hits++; }
  }
  printf("hits %ld\n", hits); return 0;
}
