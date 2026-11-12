// Branch-and-prune search for u^T C_e w = rhs_e (all e), u,w in GF(2)^s in reduced echelon form (see minrank_block.py).
// Incremental version: the linear system over the unassigned (u_b, w_b) is kept in echelon form with pivot = highest bit,
// bits interleaved (w_b -> 2b, u_b -> 2b+1).  Assigning vertex m (the lowest unassigned) is a substitution that clears the
// lowest bits of every row, so the echelon form survives; rows whose pivot was vertex m become constants (must be 0).
// An equation e joins at depth lev[e] (all its entries touch an assigned vertex): its linear form is built from Su/Sw.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
typedef unsigned __int128 u128;
static int s, ne, *lev, *rhs; static uint64_t *C;   // C[e*s + a] = row a of equation e (bitmask over vertices)
static uint64_t *Su, *Sw, *SuP[66], *SwP[66];                            // per depth: Su[m*ne + e] = XOR_{a<m, u_a} C_e[a]
static long long nodes = 0, leaves = 0, found = 0, dnodes[65], LIMIT = 0;
static int U[64], W[64], *start;                     // start[m] = first equation with lev == m (eqs sorted by lev)
typedef struct { u128 row[130]; unsigned char c[130]; signed char has[130]; } Basis;  // indexed by pivot bit
static Basis B[66];
static inline int hibit(u128 x) { uint64_t h = (uint64_t)(x >> 64); return h ? 64 + 63 - __builtin_clzll(h) : 63 - __builtin_clzll((uint64_t)x); }
#include <immintrin.h>
static inline u128 spread(uint64_t m, int odd) {  // bit b -> bit 2b+odd (BMI2 pdep)
  const uint64_t M = 0x5555555555555555ULL << odd;
  return ((u128)_pdep_u64(m >> 32, M) << 64) | (u128)_pdep_u64(m & 0xffffffffULL, M);
}
static int insert(Basis *bs, u128 r, int c) {
  while (r) { int h = hibit(r); if (!bs->has[h]) { bs->has[h] = 1; bs->row[h] = r; bs->c[h] = c; return 1; } r ^= bs->row[h]; c ^= bs->c[h]; }
  return c == 0;
}
static void dfs(int m, int hasU, int hasW) {
  nodes++; dnodes[m]++; if (LIMIT && nodes > LIMIT) return;
  Basis *bs = &B[m];
  uint64_t Kmask = (m >= 64) ? ~0ULL : ((1ULL << m) - 1), Rmask = ~Kmask;
  uint64_t wK = 0; for (int a = 0; a < m; a++) if (W[a]) wK |= 1ULL << a;
  for (int e = start[m]; e < start[m + 1]; e++) {   // equations that become linear at depth m
    uint64_t su = SuP[m][e], sw = SwP[m][e];
    int c = __builtin_parityll(su & wK) ^ rhs[e];
    u128 r = spread(su & Rmask, 0) | spread(sw & Rmask, 1);
    if (!insert(bs, r, c)) return;
  }
  if (m == s) { leaves++; if (hasU && hasW) { found++; if (found <= 3) { printf("SOLUTION u="); for (int a = 0; a < s; a++) printf("%d", U[a]); printf(" w="); for (int a = 0; a < s; a++) printf("%d", W[a]); printf("\n"); } } return; }
  int ch[4][2], nc = 0;
  if (!hasU) { ch[nc][0] = 0; ch[nc][1] = 0; nc++; ch[nc][0] = 1; ch[nc][1] = 0; nc++; }
  else if (!hasW) { ch[nc][0] = 0; ch[nc][1] = 0; nc++; ch[nc][0] = 1; ch[nc][1] = 0; nc++; ch[nc][0] = 0; ch[nc][1] = 1; nc++; }
  else { for (int x = 0; x < 4; x++) { ch[nc][0] = x & 1; ch[nc][1] = x >> 1; nc++; } }
  // Shared per node: clearing bits 2m, 2m+1 gives the same rows for every child; only the constants differ.
  // Rows that become 0 give constraints c ^ (b_w & wm) ^ (b_u & um) = 0 on the child.
  u128 crow[130]; unsigned char cc[130], bw[130], bu[130]; int hl[130], nh = 0; int zmask_ok = 0xF;
  for (int h = 2 * m; h < 2 * s; h++) if (bs->has[h]) {
    u128 r = bs->row[h]; int c = bs->c[h];
    int a = (int)((r >> (2 * m)) & 1), b = (int)((r >> (2 * m + 1)) & 1);
    r &= ~((u128)3 << (2 * m));
    if (!r) { for (int x = 0; x < 4; x++) if ((c ^ (a & (x >> 1)) ^ (b & (x & 1)))) zmask_ok &= ~(1 << x); continue; }
    hl[nh] = hibit(r); crow[nh] = r; cc[nh] = c; bw[nh] = a; bu[nh] = b; nh++;
  }
  for (int ci = 0; ci < nc; ci++) {
    int um = ch[ci][0], wm = ch[ci][1]; U[m] = um; W[m] = wm;
    Basis *nb = &B[m + 1]; int ok = (zmask_ok >> (um | (wm << 1))) & 1;
    if (!ok) continue;
    for (int h = 2 * m; h < 2 * s; h++) nb->has[h] = 0;
    for (int i = 0; i < nh; i++) { int hh = hl[i]; nb->has[hh] = 1; nb->row[hh] = crow[i]; nb->c[hh] = cc[i] ^ (bw[i] & wm) ^ (bu[i] & um); }
    if (!ok) continue;
    // child arrays: share the parent's array when the bit is 0 (no copy); deeper levels only write their own buffers
    uint64_t *su0 = SuP[m], *sw0 = SwP[m];
    if (um) { uint64_t *su1 = Su + (size_t)(m + 1) * ne; for (int e = start[m + 1]; e < ne; e++) su1[e] = su0[e] ^ C[(size_t)e * s + m]; SuP[m + 1] = su1; } else SuP[m + 1] = su0;
    if (wm) { uint64_t *sw1 = Sw + (size_t)(m + 1) * ne; for (int e = start[m + 1]; e < ne; e++) sw1[e] = sw0[e] ^ C[(size_t)e * s + m]; SwP[m + 1] = sw1; } else SwP[m + 1] = sw0;
    dfs(m + 1, hasU || um, hasW || wm);
    if (found > 1000) return;
  }
}
int main(int argc, char **argv) {
  FILE *f = fopen(argv[1], "r"); if (!f) return 2;
  if (fscanf(f, "%d %d", &s, &ne) != 2) return 2;
  if (s > 64) { printf("RESULT SKIP s=%d>64\n", s); return 0; }
  lev = malloc(ne * sizeof(int)); rhs = malloc(ne * sizeof(int)); C = malloc((size_t)ne * s * 8);
  for (int e = 0; e < ne; e++) {
    if (fscanf(f, "%d %d", &lev[e], &rhs[e]) != 2) return 2;
    for (int a = 0; a < s; a++) { unsigned long long x; if (fscanf(f, "%llu", &x) != 1) return 2; C[(size_t)e * s + a] = x; }
  }
  start = calloc(s + 2, sizeof(int));
  for (int m = 0, e = 0; m <= s + 1; m++) { while (e < ne && lev[e] < m) e++; start[m] = e; }
  Su = calloc((size_t)(s + 1) * ne, 8); Sw = calloc((size_t)(s + 1) * ne, 8); SuP[0] = Su; SwP[0] = Sw;
  for (int h = 0; h < 130; h++) B[0].has[h] = 0;
  if (argc > 2) LIMIT = atoll(argv[2]);
  dfs(0, 0, 0);
  fprintf(stderr, "nodes by depth:"); for (int m = 0; m <= s; m++) fprintf(stderr, " %lld", dnodes[m]); fprintf(stderr, "\n");
  printf("RESULT %s%s s=%d ne=%d nodes=%lld leaves=%lld solutions=%lld\n", found ? "HIT" : "NONE(exact)", (LIMIT && nodes > LIMIT) ? " [LIMIT HIT - NOT EXACT]" : "", s, ne, nodes, leaves, found);
  return 0;
}
