// Supervisor 2026-11-12 03:xx UTC. Simulated annealing in the TRANSVECTION model (superset of the CSWAP model).
// Gate k = (f, L, v): in every case where parity(f & case) = 1, x -> x ^ <L,x> v  (L, v: masks over data wires, popcount(L&v) even).
// Each such gate is 1 CCX conjugated by a free unconditional CX network on the data wires (and free CX on the control wires
// for the form f); a CSWAP(a,b) is L = v = {a,b}. Values are affine masks over the case tokens (tv_prep.py).
// cost = sum over cases and wires of popcount(value ^ target).
// Usage: ./cswap_win_tv in.txt K seed iters [restarts [init.txt [T0 [pcswap]]]]   init lines: "a b form" (CSWAP) or "L v form" with L,v hex prefixed 0x
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define MW 32
#define MC 64
int W,NCT,NC,cm[MC],K,NF; unsigned st[MC][MW],en[MC][MW];
unsigned gL[256],gv[256]; int gf[256];
static unsigned long long rs; static inline unsigned long long rnd(){rs^=rs<<13;rs^=rs>>7;rs^=rs<<17;return rs;}
static inline int ok(unsigned L,unsigned v){return L&&v&&!(__builtin_popcount(L&v)&1);}
int cost(){int tot=0;for(int c=0;c<NC;c++){unsigned s[MW];memcpy(s,st[c],4*W);
  for(int t=0;t<K;t++) if(__builtin_parity(gf[t]&cm[c])){unsigned a=0,L=gL[t];while(L){int w=__builtin_ctz(L);L&=L-1;a^=s[w];}
    if(a){unsigned v=gv[t];while(v){int w=__builtin_ctz(v);v&=v-1;s[w]^=a;}}}
  for(int w=0;w<W;w++) tot+=__builtin_popcount(s[w]^en[c][w]);}return tot;}
double PCS=0.5;
void randcswap(int t){int a=rnd()%W,b;do b=rnd()%W;while(b==a);gL[t]=gv[t]=(1u<<a)|(1u<<b);gf[t]=1+rnd()%NF;}
void randgate(int t){ if((rnd()%1000)/1000.0<PCS){randcswap(t);return;}
  unsigned L,v; do{L=(rnd()&((1u<<W)-1))&(rnd()|rnd()&rnd()); v=1u<<(rnd()%W); if(rnd()&1) v|=1u<<(rnd()%W);}while(!ok(L,v)); gL[t]=L;gv[t]=v;gf[t]=1+rnd()%NF;}
int main(int argc,char**argv){FILE*F=fopen(argv[1],"r");if(fscanf(F,"%d %d %d",&W,&NCT,&NC)!=3)return 1;NF=(1<<NCT)-1;
  for(int c=0;c<NC;c++){fscanf(F,"%d",&cm[c]);for(int w=0;w<W;w++)fscanf(F,"%u",&st[c][w]);for(int w=0;w<W;w++)fscanf(F,"%u",&en[c][w]);}
  K=atoi(argv[2]);rs=atoll(argv[3])*2654435761ULL+12345;long long IT=atoll(argv[4]);int MR=argc>5?atoi(argv[5]):1<<30;
  double T0=argc>7?atof(argv[7]):1.0; if(argc>8) PCS=atof(argv[8]);
  int NI=0; unsigned iL[256],iv[256]; int iff[256];
  if(argc>6 && strcmp(argv[6],"-")){FILE*G=fopen(argv[6],"r");char a[64],b[64];int f;while(fscanf(G,"%63s %63s %d",a,b,&f)==3){
      if(a[0]=='0'&&a[1]=='x'){iL[NI]=strtoul(a,0,16);iv[NI]=strtoul(b,0,16);} else {iL[NI]=iv[NI]=(1u<<atoi(a))|(1u<<atoi(b));} iff[NI++]=f;} fclose(G);}
  int best=1<<30;
  for(int rest=0;rest<MR;rest++){
    if(NI){int keep[256];for(int i=0;i<NI;i++)keep[i]=1;for(int d=0;d<NI-K;d++){int i;do i=rnd()%NI;while(!keep[i]);keep[i]=0;}
      int t=0;for(int i=0;i<NI;i++)if(keep[i]){gL[t]=iL[i];gv[t]=iv[i];gf[t]=iff[i];t++;}for(;t<K;t++)randgate(t);}
    else for(int t=0;t<K;t++)randgate(t);
    int cur=cost();
    for(long long it=0;it<IT;it++){double T=T0*(1-(double)it/IT)+0.05;
      int t=rnd()%K,t2=-1;unsigned sL=gL[t],sv=gv[t];int sf=gf[t];int mv=rnd()%6;
      if(mv==0) randgate(t);
      else if(mv==1) gf[t]=1+rnd()%NF;
      else if(mv==2){unsigned L=gL[t]^(1u<<(rnd()%W)); if(!ok(L,gv[t])) L^=1u<<(rnd()%W); if(ok(L,gv[t])) gL[t]=L;}
      else if(mv==3){unsigned v=gv[t]^(1u<<(rnd()%W)); if(!ok(gL[t],v)) v^=1u<<(rnd()%W); if(ok(gL[t],v)) gv[t]=v;}
      else if(mv==4){unsigned b=1u<<(rnd()%W); unsigned L=gL[t]^b, v=gv[t]^b; if(ok(L,v)){gL[t]=L;gv[t]=v;}}
      else {t2=rnd()%K;unsigned x;x=gL[t];gL[t]=gL[t2];gL[t2]=x;x=gv[t];gv[t]=gv[t2];gv[t2]=x;int y=gf[t];gf[t]=gf[t2];gf[t2]=y;}
      int nc=cost();
      if(nc<=cur||exp((cur-nc)/T)>(rnd()%1000000)/1e6) cur=nc;
      else{ if(t2>=0){unsigned x;x=gL[t];gL[t]=gL[t2];gL[t2]=x;x=gv[t];gv[t]=gv[t2];gv[t2]=x;int y=gf[t];gf[t]=gf[t2];gf[t2]=y;} else{gL[t]=sL;gv[t]=sv;gf[t]=sf;} }
      if(cur==0)break;}
    if(cur<best){best=cur;printf("restart %d best %d\n",rest,best);fflush(stdout);}
    if(cur==0){for(int t=0;t<K;t++)printf("tv %d 0x%x 0x%x %d\n",t,gL[t],gv[t],gf[t]);fflush(stdout);return 0;}
  }return 2;}
