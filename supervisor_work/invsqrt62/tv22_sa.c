// Supervisor 2026-11-12 04:xx UTC. SA in the transvection model WITH the wire-22 measurement (ext22.py / tv22_init.py).
// Network: K costly transvections (f, L, v) over W data wires (last one = wire 22, clean 0 at start), a split MU (gates >= MU run
// after the measurement) and S (free CX 22 -> S right before the HMR; then wire 22 = 0).  At MU, z_c = value of wire 22 must be
// fixable by outcome-conditioned Clifford gates: z_c = q0(c) ^ sum_w lam_w(c) s_c[w] (w != 22), lam_w affine in the case bits
// (CZ ctl-data, Z data), q0 quadratic in the case bits (CZ/Z among controls).
// cost = sum_{c,w} popcount(end ^ target)  +  ZW * (cases with z not in span  +  sum_w dist(lam_w, affine)  +  [q0 not quadratic]).
// Usage: ./tv22_sa in.txt K seed iters [restarts [init.txt|- [T0 [ZW]]]]   init: first line "MU mu 0xS", then "0xL 0xv f" lines
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define MW 32
#define MC 64
int W,NCT,NC,cm[MC],K,NF,Z; unsigned st[MC][MW],en[MC][MW];
unsigned gL[256],gv[256]; int gf[256]; int MU; unsigned SM;
unsigned affcw[64]; int naff; unsigned qb[32]; int nq;  // affine codewords over cases; quadratic code basis (echelon)
static unsigned long long rs; static inline unsigned long long rnd(){rs^=rs<<13;rs^=rs>>7;rs^=rs<<17;return rs;}
static inline int ok(unsigned L,unsigned v){return L&&v&&!(__builtin_popcount(L&v)&1);}
double ZW=2.0;
static inline void apg(unsigned*s,int t,int c){ if(!__builtin_parity(gf[t]&cm[c]))return; unsigned a=0,L=gL[t];while(L){int w=__builtin_ctz(L);L&=L-1;a^=s[w];}
  if(a){unsigned v=gv[t];while(v){int w=__builtin_ctz(v);v&=v-1;s[w]^=a;}}}
int zmiss; int zres;
// exact fixability: unknowns lam_{w,k} (w < Z, k = 0 const / 1..NCT case bit) and q0 monomials (quadratic in case bits);
// equations per case c and form bit t: sum lam_w(c) s_c[w]_t + [t==W] q0(c) = z_c,t.  Greedy over cases: a case whose
// equations make the system inconsistent counts 1 and is rolled back.  zres = number of such cases (0 <=> exactly fixable).
typedef struct { unsigned long long a[3]; } E3;
int NVAR, nmono2; int mono2[64][2];
E3 piv[192]; int haspiv[192]; int pstack[2048]; int np;
static inline int addeq(E3 e){ for(int v=0;v<NVAR;v++){ if(!(e.a[v>>6]>>(v&63)&1)) continue;
    if(haspiv[v]){ for(int i=0;i<3;i++) e.a[i]^=piv[v].a[i]; } else { piv[v]=e; haspiv[v]=1; pstack[np++]=v; return 0; } }
  return (e.a[2]>>63)&1; }
unsigned muS[MC][MW], muZ[MC];
int zfix(){ np=0; memset(haspiv,0,sizeof haspiv); int bad=0;
  for(int c=0;c<NC;c++){ int np0=np; int inc=0; int mon[8]; mon[0]=1; for(int i=0;i<NCT;i++) mon[i+1]=cm[c]>>i&1;
    for(int t=0;t<=W && !inc;t++){ E3 e={{0,0,0}}; int any=0;
      for(int w=0;w<Z;w++) if(muS[c][w]>>t&1) for(int k=0;k<=NCT;k++) if(mon[k]){int v=w*(NCT+1)+k; e.a[v>>6]^=1ULL<<(v&63); any=1;}
      if(t==W) for(int m=0;m<nmono2;m++){ int i=mono2[m][0],j=mono2[m][1]; if(mon[i]&mon[j]){int v=Z*(NCT+1)+m; e.a[v>>6]^=1ULL<<(v&63); any=1;} }
      int r=muZ[c]>>t&1; if(!any){ if(r) inc=1; continue; } if(r) e.a[2]^=1ULL<<63;
      if(addeq(e)) inc=1; }
    if(inc){ bad++; while(np>np0) haspiv[pstack[--np]]=0; } }
  return bad; }
double cost(){int tot=0; zmiss=0;
  for(int c=0;c<NC;c++){unsigned s[MW];memcpy(s,st[c],4*W);
    for(int t=0;t<=K;t++){ if(t==MU){unsigned z=s[Z]; for(int w=0;w<W;w++) if(SM>>w&1) s[w]^=z; s[Z]=0; memcpy(muS[c],s,4*W); muZ[c]=z; }
      if(t<K) apg(s,t,c);}
    for(int w=0;w<W;w++) tot+=__builtin_popcount(s[w]^en[c][w]);}
  zres=zfix(); return tot+ZW*zres;}
double PCS=0.5;
void randcswap(int t){int a=rnd()%W,b;do b=rnd()%W;while(b==a);gL[t]=gv[t]=(1u<<a)|(1u<<b);gf[t]=1+rnd()%NF;}
void randgate(int t){ if((rnd()%1000)/1000.0<PCS){randcswap(t);return;}
  unsigned L,v; do{L=(rnd()&((1u<<W)-1))&(rnd()|rnd()&rnd()); v=1u<<(rnd()%W); if(rnd()&1) v|=1u<<(rnd()%W);}while(!ok(L,v)); gL[t]=L;gv[t]=v;gf[t]=1+rnd()%NF;}
int main(int argc,char**argv){FILE*F=fopen(argv[1],"r");if(fscanf(F,"%d %d %d",&W,&NCT,&NC)!=3)return 1;NF=(1<<NCT)-1;Z=W-1;
  for(int c=0;c<NC;c++){unsigned zz;fscanf(F,"%d",&cm[c]);for(int w=0;w<W;w++)fscanf(F,"%u",&st[c][w]);for(int w=0;w<W;w++)fscanf(F,"%u",&en[c][w]);fscanf(F,"%u",&zz);}
  // codes over the case points
  naff=0; for(int a=0;a<(1<<(NCT+1));a++){unsigned cw=0; for(int c=0;c<NC;c++){int b=(a&1); for(int i=0;i<NCT;i++) if(a>>(i+1)&1) b^=cm[c]>>i&1; if(b) cw|=1u<<c;} affcw[naff++]=cw;}
  nq=0; for(int i=0;i<=NCT;i++) for(int j=i;j<=NCT;j++){ unsigned cw=0;  // monomial b_{i-1} b_{j-1}, index 0 = constant 1
      for(int c=0;c<NC;c++){int bi= i==0?1:(cm[c]>>(i-1)&1), bj= j==0?1:(cm[c]>>(j-1)&1); if(bi&bj) cw|=1u<<c;}
      unsigned x=cw; for(int k=0;k<nq;k++) if(x>>(31-__builtin_clz(qb[k]))&1) x^=qb[k];
      if(x){ for(int k=0;k<nq;k++) if(qb[k]>>(31-__builtin_clz(x))&1) qb[k]^=x; qb[nq++]=x; } }
  nmono2=0; for(int i=0;i<=NCT;i++) for(int j=i;j<=NCT;j++){ if(i==0&&j>0) continue; mono2[nmono2][0]=i; mono2[nmono2][1]=j; nmono2++; }
  NVAR=Z*(NCT+1)+nmono2; if(NVAR>191){printf("too many vars\n");return 1;}
  K=atoi(argv[2]);rs=atoll(argv[3])*2654435761ULL+12345;long long IT=atoll(argv[4]);int MR=argc>5?atoi(argv[5]):1<<30;
  double T0=argc>7?atof(argv[7]):1.0; if(argc>8) ZW=atof(argv[8]); if(argc>9) PCS=atof(argv[9]);
  int NI=0; unsigned iL[256],iv[256]; int iff[256]; int imu=0; unsigned ism=0;
  if(argc>6 && strcmp(argv[6],"-")){FILE*G=fopen(argv[6],"r");char a[64],b[64];int f; char hs[64]; if(fscanf(G,"MU %d %63s",&imu,hs)==2) ism=strtoul(hs,0,16);
    while(fscanf(G,"%63s %63s %d",a,b,&f)==3){iL[NI]=strtoul(a,0,16);iv[NI]=strtoul(b,0,16);iff[NI++]=f;} fclose(G);}
  if(NI && NI==K){ for(int t=0;t<K;t++){gL[t]=iL[t];gv[t]=iv[t];gf[t]=iff[t];} MU=imu;SM=ism; double c0=cost(); printf("init cost %.1f zres %d zmiss %d\n",c0,zres,zmiss); fflush(stdout);}
  double best=1e18;
  for(int rest=0;rest<MR;rest++){
    if(NI){int keep[256];for(int i=0;i<NI;i++)keep[i]=1;int dropped_before=0;for(int d=0;d<NI-K;d++){int i;do i=rnd()%NI;while(!keep[i]);keep[i]=0;}
      int t=0;for(int i=0;i<NI;i++){ if(i==imu) MU=t; if(keep[i]){gL[t]=iL[i];gv[t]=iv[i];gf[t]=iff[i];t++;}} if(imu>=NI) MU=t; for(;t<K;t++)randgate(t); SM=ism; (void)dropped_before;}
    else {for(int t=0;t<K;t++)randgate(t); MU=rnd()%(K+1); SM=0;}
    double cur=cost();
    for(long long it=0;it<IT;it++){double T=T0*(1-(double)it/IT)+0.05;
      int t=rnd()%K,t2=-1;unsigned sL=gL[t],sv=gv[t];int sf=gf[t]; int smu=MU; unsigned ssm=SM; int mv=rnd()%8; if(PCS>=1.0 && mv>=2 && mv<=4){ if(gL[t]==gv[t] && __builtin_popcount(gL[t])==2){ int a=__builtin_ctz(gL[t]); unsigned rest=gL[t]&~(1u<<a); int b; do b=rnd()%W; while(rest>>b&1); gL[t]=gv[t]=rest|(1u<<b); if(__builtin_popcount(gL[t])!=2){gL[t]=sL;gv[t]=sv;} } mv=99; }
      if(mv==0) randgate(t);
      else if(mv==1) gf[t]=1+rnd()%NF;
      else if(mv==2){unsigned L=gL[t]^(1u<<(rnd()%W)); if(!ok(L,gv[t])) L^=1u<<(rnd()%W); if(ok(L,gv[t])) gL[t]=L;}
      else if(mv==3){unsigned v=gv[t]^(1u<<(rnd()%W)); if(!ok(gL[t],v)) v^=1u<<(rnd()%W); if(ok(gL[t],v)) gv[t]=v;}
      else if(mv==4){unsigned b=1u<<(rnd()%W); unsigned L=gL[t]^b, v=gv[t]^b; if(ok(L,v)){gL[t]=L;gv[t]=v;}}
      else if(mv==5){ int d=(rnd()&1)?1:-1; MU+=d; if(MU<0||MU>K) MU=smu; }
      else if(mv==6){ SM^=1u<<(rnd()%(W-1)); }
      else if(mv==7){t2=rnd()%K;unsigned x;x=gL[t];gL[t]=gL[t2];gL[t2]=x;x=gv[t];gv[t]=gv[t2];gv[t2]=x;int y=gf[t];gf[t]=gf[t2];gf[t2]=y;}
      double nc=cost();
      if(nc<=cur||exp((cur-nc)/T)>(rnd()%1000000)/1e6) cur=nc;
      else{ if(t2>=0){unsigned x;x=gL[t];gL[t]=gL[t2];gL[t2]=x;x=gv[t];gv[t]=gv[t2];gv[t2]=x;int y=gf[t];gf[t]=gf[t2];gf[t2]=y;} else{gL[t]=sL;gv[t]=sv;gf[t]=sf;} MU=smu; SM=ssm; }
      if(cur==0)break;}
    if(cur<best){best=cur;printf("restart %d best %.1f\n",rest,best);fflush(stdout);}
    if(cur==0){printf("MU %d 0x%x\n",MU,SM); for(int t=0;t<K;t++)printf("tv %d 0x%x 0x%x %d\n",t,gL[t],gv[t],gf[t]);fflush(stdout);return 0;}
  }return 2;}
