// Supervisor 2026-11-12. Simulated annealing: K CSWAPs on data-wire pairs, control = nonzero linear form f over NCTL control bits
// (active in case c iff parity(f&c)). Find a network mapping start->end tokens in every case. cost = #mismatched wires summed.
// Input from cswap_win_extract.py. Usage: ./cswap_win_sa in.txt K seed iters_per_restart [max_restarts]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define MW 64
#define MC 64
int W, NCT, NC, cm[MC], st[MC][MW], en[MC][MW], K, NF;
int ga[256], gb[256], gf[256];
static unsigned long long rs;
static inline unsigned long long rnd(){ rs^=rs<<13; rs^=rs>>7; rs^=rs<<17; return rs; }
int cost(){
  int tot=0;
  for(int c=0;c<NC;c++){ int s[MW]; memcpy(s,st[c],sizeof(int)*W);
    for(int t=0;t<K;t++) if(__builtin_parity(gf[t]&cm[c])){ int x=s[ga[t]]; s[ga[t]]=s[gb[t]]; s[gb[t]]=x; }
    for(int w=0;w<W;w++) tot+= s[w]!=en[c][w]; }
  return tot;
}
void randgate(int t){ int a=rnd()%W,b; do b=rnd()%W; while(b==a); if(a>b){int x=a;a=b;b=x;} ga[t]=a; gb[t]=b; gf[t]=1+rnd()%NF; }
int main(int argc,char**argv){
  FILE*F=fopen(argv[1],"r"); if(fscanf(F,"%d %d %d",&W,&NCT,&NC)!=3) return 1; NF=(1<<NCT)-1;
  for(int c=0;c<NC;c++){ if(fscanf(F,"%d",&cm[c])!=1) return 1;
    for(int w=0;w<W;w++) if(fscanf(F,"%d",&st[c][w])!=1) return 1; for(int w=0;w<W;w++) if(fscanf(F,"%d",&en[c][w])!=1) return 1; }
  K=atoi(argv[2]); rs=atoll(argv[3])*2654435761ULL+12345; long long IT=atoll(argv[4]); int MR=argc>5?atoi(argv[5]):1<<30;
  int best=1<<30;
  for(int rest=0;rest<MR;rest++){
    for(int t=0;t<K;t++) randgate(t);
    int cur=cost(); double T0=3.0;
    for(long long it=0;it<IT;it++){
      double T=T0*(1-(double)it/IT)+0.05;
      int t=rnd()%K, sa=ga[t],sb=gb[t],sf=gf[t]; int mv=rnd()%4; int t2=-1;
      if(mv==0) randgate(t);
      else if(mv==1) gf[t]=1+rnd()%NF;
      else if(mv==2){ int w=rnd()%W; if(rnd()&1){ if(w!=gb[t]) ga[t]=w; } else { if(w!=ga[t]) gb[t]=w; } if(ga[t]>gb[t]){int x=ga[t];ga[t]=gb[t];gb[t]=x;} }
      else { t2=rnd()%K; int x; x=ga[t];ga[t]=ga[t2];ga[t2]=x; x=gb[t];gb[t]=gb[t2];gb[t2]=x; x=gf[t];gf[t]=gf[t2];gf[t2]=x; }
      int nc=cost();
      if(nc<=cur || exp((cur-nc)/T) > (rnd()%1000000)/1e6) cur=nc;
      else { if(t2>=0){ int x; x=ga[t];ga[t]=ga[t2];ga[t2]=x; x=gb[t];gb[t]=gb[t2];gb[t2]=x; x=gf[t];gf[t]=gf[t2];gf[t2]=x; } else { ga[t]=sa; gb[t]=sb; gf[t]=sf; } }
      if(cur==0) break;
    }
    if(cur<best){ best=cur; printf("restart %d best %d\n",rest,best); fflush(stdout); }
    if(cur==0){ for(int t=0;t<K;t++) printf("gate %d pair %d %d form %d\n",t,ga[t],gb[t],gf[t]); fflush(stdout); return 0; }
  }
  return 2;
}
