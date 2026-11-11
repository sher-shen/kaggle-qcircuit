/* ab_enum: given m and the parity-check columns H[(i,j)] (rho bits, i<j) of the space Z of alternating forms c with
   sum c_ij red(y_i y_j) = 0, print every a in [1,2^m) whose kernel {b : H(a ^ b) = 0} has dim >= 2, as "a k1 k2 ..." (basis).
   Input: m rho, then m(m-1)/2 lines of rho '0'/'1' chars in order (0,1),(0,2),..,(m-2,m-1). */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#define W 4
typedef struct { uint64_t w[W]; } bs;
static bs H[32][32];
int main(void) {
  int m, rho; if (scanf("%d %d", &m, &rho) != 2) return 1;
  char buf[512];
  for (int i = 0; i < m; i++) for (int j = i + 1; j < m; j++) {
    if (scanf("%s", buf) != 1) return 1; bs v; memset(&v, 0, sizeof v);
    for (int k = 0; k < rho; k++) if (buf[k] == '1') v.w[k >> 6] |= 1ULL << (k & 63);
    H[i][j] = v; H[j][i] = v;
  }
  for (uint32_t a = 1; a < (1u << m); a++) {
    bs col[32]; uint32_t comb[32];
    for (int j = 0; j < m; j++) {
      memset(&col[j], 0, sizeof(bs)); comb[j] = 1u << j;
      for (int i = 0; i < m; i++) if (i != j && ((a >> i) & 1)) for (int t = 0; t < W; t++) col[j].w[t] ^= H[i][j].w[t];
    }
    /* find dependencies among columns: gaussian elimination */
    bs piv[256]; uint32_t pc[256]; int pk[256]; int np = 0; uint32_t ker[32]; int nk = 0;
    for (int j = 0; j < m; j++) {
      bs v = col[j]; uint32_t c = comb[j];
      for (int p = 0; p < np; p++) if ((v.w[pk[p] >> 6] >> (pk[p] & 63)) & 1) { for (int t = 0; t < W; t++) v.w[t] ^= piv[p].w[t]; c ^= pc[p]; }
      int lead = -1; for (int t = 0; t < W && lead < 0; t++) if (v.w[t]) lead = t * 64 + __builtin_ctzll(v.w[t]);
      if (lead < 0) ker[nk++] = c; else { piv[np] = v; pc[np] = c; pk[np] = lead; np++; }
    }
    if (nk >= 2) { printf("%u", a); for (int k = 0; k < nk; k++) printf(" %u", ker[k]); printf("\n"); }
  }
  return 0;
}
