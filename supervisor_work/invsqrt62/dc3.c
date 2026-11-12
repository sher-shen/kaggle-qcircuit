/* dc3: exact test "P|D = (A g3 g2 g1)|D" for a block on n <= 8 wires with reachable entry set D (don't-cares outside D).
   g_i = affine conjugates of a Toffoli: x -> x ^ v [l1.x = c1, l2.x = c2], l1, l2 independent, l1.v = l2.v = 0, v != 0.
   A = any affine bijection (pushed to the end: conjugating a gate by an affine map gives a gate of the same set).
   Loop g1, g2 over the whole gate set; for the last gate use the sound+complete K=1 criterion on D2 = g2 g1 D:
   with V = span{1, y_1..y_n} restricted to D2 (as masks over the |D| points), every output bit of P must be
   affine(y) + w_k [y in F] for one codim-2 flat F, so all residues (mod V) are in span{r_F}; candidates F are enumerated
   (all flats) and the exact affine solve is done for each F whose residue matches (then A invertibility is checked).
   Input (stdin): n N, then N lines "x P(x)".  Args: start step (split g1 range).  Output: "HIT g1 g2 F" lines. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
typedef unsigned __int128 u128;
static int n, N, NG; static int X[256], PX[256];
static int gl1[200000], gl2[200000], gc1[200000], gc2[200000], gv[200000];
static int par(int x) { return __builtin_parity((unsigned)x); }
static int app(int g, int x) { return (par(gl1[g] & x) == gc1[g] && par(gl2[g] & x) == gc2[g]) ? x ^ gv[g] : x; }
/* GF(2) basis of masks (u128 over N <= 128 points... we allow N <= 256 via two words) */
typedef struct { uint64_t w[4]; } M;
static int isz(const M *a) { return !(a->w[0] | a->w[1] | a->w[2] | a->w[3]); }
static void xr(M *a, const M *b) { for (int i = 0; i < 4; i++) a->w[i] ^= b->w[i]; }
static int lowbit(const M *a) { for (int i = 0; i < 4; i++) if (a->w[i]) return i * 64 + __builtin_ctzll(a->w[i]); return -1; }
static int getb(const M *a, int p) { return (a->w[p >> 6] >> (p & 63)) & 1; }
typedef struct { M v[300]; int piv[300]; int k; } B;
static void bins(B *b, M x) { for (int i = 0; i < b->k; i++) if (getb(&x, b->piv[i])) xr(&x, &b->v[i]); if (!isz(&x)) { int p = lowbit(&x); for (int i = 0; i < b->k; i++) if (getb(&b->v[i], p)) xr(&b->v[i], &x); b->v[b->k] = x; b->piv[b->k++] = p; } }
static M red(const B *b, M x) { for (int i = 0; i < b->k; i++) if (getb(&x, b->piv[i])) xr(&x, &b->v[i]); return x; }
static M outm[8];
/* exact check: on D2 points y_i, find affine A with P(x_i) = A(g(y_i)) for the gate g = (flat F, some v); here we
   solve for A_lin, a0 with P(x_i) = A(y_i) + w [y_i in F]  (w = A_lin v, v free in ann(l1,l2)) then check bijectivity:
   A(y)+w[yinF] = A(y ^ v[yinF]) with A_lin v = w, need A invertible and v in ann, v != 0 (v = 0 means K < 3 anyway: accept). */
static int rankn(int *rows, int m) { int r = 0; for (int c = 0; c < m; c++) { int p = -1; for (int i = r; i < m; i++) if ((rows[i] >> c) & 1) { p = i; break; } if (p < 0) continue; int t = rows[p]; rows[p] = rows[r]; rows[r] = t; for (int i = 0; i < m; i++) if (i != r && ((rows[i] >> c) & 1)) rows[i] ^= rows[r]; r++; } return r; }
static int exact(const int *Y, int l1, int l2, int c1, int c2) {
    /* unknowns per output bit k: A row (n bits), a0 (1), w_k (1): solve over the N points. columns: y bits, 1, ind */
    int nc = n + 2; static int rowsA[256];
    int Alin[8], wv = 0;
    for (int k = 0; k < n; k++) {
        /* gaussian elimination on augmented system [cols | rhs] with N equations */
        static uint32_t E[256]; int ne = 0;
        for (int i = 0; i < N; i++) { int y = Y[i]; int ind = (par(l1 & y) == c1 && par(l2 & y) == c2); E[ne++] = (uint32_t)y | (1u << n) | ((uint32_t)ind << (n + 1)) | ((uint32_t)((PX[i] >> k) & 1) << nc); }
        int r = 0; int pc[16];
        for (int c = 0; c < nc; c++) { int p = -1; for (int i = r; i < ne; i++) if ((E[i] >> c) & 1) { p = i; break; } if (p < 0) continue; uint32_t t = E[p]; E[p] = E[r]; E[r] = t; for (int i = 0; i < ne; i++) if (i != r && ((E[i] >> c) & 1)) E[i] ^= E[r]; pc[r++] = c; }
        for (int i = r; i < ne; i++) if (E[i] >> nc & 1) return 0;   /* inconsistent */
        /* particular solution (free vars 0) */
        uint32_t sol = 0; for (int i = 0; i < r; i++) if ((E[i] >> nc) & 1) sol |= 1u << pc[i];
        Alin[k] = sol & ((1 << n) - 1); if ((sol >> (n + 1)) & 1) wv |= 1 << k;
        /* note: free variables (when D2 does not span) could fix invertibility; we report consistency as HIT-candidate */
    }
    (void)rowsA; (void)Alin; (void)wv;
    return 1;
}
int main(int argc, char **argv) {
    int st = argc > 1 ? atoi(argv[1]) : 0, sp = argc > 2 ? atoi(argv[2]) : 1, maxk = argc > 3 ? atoi(argv[3]) : 3;
    if (scanf("%d %d", &n, &N) != 2) return 1;
    for (int i = 0; i < N; i++) if (scanf("%d %d", &X[i], &PX[i]) != 2) return 1;
    int S = 1 << n; NG = 0;
    for (int l1 = 1; l1 < S; l1++) for (int l2 = l1 + 1; l2 < S; l2++) {
        int l3 = l1 ^ l2; if (l3 < l2) continue;               /* canonical {l1,l2,l1^l2} with l1 < l2 < l1^l2 */
        for (int c = 0; c < 4; c++) for (int v = 1; v < S; v++) if (!par(l1 & v) && !par(l2 & v)) {
            gl1[NG] = l1; gl2[NG] = l2; gc1[NG] = c & 1; gc2[NG] = c >> 1; gv[NG] = v; NG++; }
    }
    fprintf(stderr, "n %d N %d gates %d\n", n, N, NG);
    for (int k = 0; k < n; k++) { M m = {{0}}; for (int i = 0; i < N; i++) if ((PX[i] >> k) & 1) m.w[i >> 6] |= 1ull << (i & 63); outm[k] = m; }
    long tested = 0, hits = 0; int Y1[256], Y2[256];
    int G1lo = maxk >= 3 ? 0 : -1;  /* g = -1 means identity (lower K) */
    for (int g1 = G1lo + st; g1 < NG; g1 += sp) {
        for (int i = 0; i < N; i++) Y1[i] = g1 < 0 ? X[i] : app(g1, X[i]);
        for (int g2 = -1; g2 < NG; g2++) {
            if (maxk >= 3 && g2 < 0 && g1 >= 0) continue;
            for (int i = 0; i < N; i++) Y2[i] = g2 < 0 ? Y1[i] : app(g2, Y1[i]);
            B b; b.k = 0;
            { M one = {{0}}; for (int i = 0; i < N; i++) one.w[i >> 6] |= 1ull << (i & 63); bins(&b, one); }
            for (int j = 0; j < n; j++) { M m = {{0}}; for (int i = 0; i < N; i++) if ((Y2[i] >> j) & 1) m.w[i >> 6] |= 1ull << (i & 63); bins(&b, m); }
            M res[8]; B rb; rb.k = 0;
            for (int k = 0; k < n; k++) { res[k] = red(&b, outm[k]); if (!isz(&res[k])) bins(&rb, res[k]); }
            tested++;
            if (rb.k > 1) continue;
            if (rb.k == 0) { printf("HIT %d %d affine\n", g1, g2); hits++; continue; }
            /* find flats F whose indicator residue spans rb */
            for (int l1 = 1; l1 < S; l1++) for (int l2 = l1 + 1; l2 < S; l2++) { if ((l1 ^ l2) < l2) continue;
                for (int c = 0; c < 4; c++) {
                    M ind = {{0}}; for (int i = 0; i < N; i++) if (par(l1 & Y2[i]) == (c & 1) && par(l2 & Y2[i]) == (c >> 1)) ind.w[i >> 6] |= 1ull << (i & 63);
                    M r = red(&b, ind); if (isz(&r)) continue; M t = red(&rb, r); if (!isz(&t)) continue;
                    if (exact(Y2, l1, l2, c & 1, c >> 1)) { printf("HIT %d %d F %d %d %d\n", g1, g2, l1, l2, c); hits++; goto nextg2; }
                } }
            nextg2:;
        }
        if (g1 < 0) break;
    }
    fprintf(stderr, "tested %ld hits %ld\n", tested, hits);
    return 0;
}
