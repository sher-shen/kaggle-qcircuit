// Simulated annealing for normalize 44+45 CSWAP network (same model as n4445_sat2.py with skip000):
// K gates, each (pair a<b of wires 0..21, form mask f in 1..7 over (r43,r44,r45)); active on case c iff parity(f & c) = 1.
// cost = sum over cases of #wires whose token != target. Usage: ./sa cases.txt K seed iters
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define W 22
int NC, cm[8], st[8][W], en[8][W], K;
int ga[64], gb[64], gf[64];
static unsigned long long rs;
static inline unsigned long long rnd(){ rs^=rs<<13; rs^=rs>>7; rs^=rs<<17; return rs; }
int act(int f,int c){ return __builtin_parity(f & cm[c]); }
int cost(){
  int tot=0;
  for(int c=0;c<NC;c++){ int s[W]; memcpy(s,st[c],sizeof s);
    for(int t=0;t<K;t++) if(act(gf[t],c)){ int x=s[ga[t]]; s[ga[t]]=s[gb[t]]; s[gb[t]]=x; }
    for(int w=0;w<W;w++) tot+= s[w]!=en[c][w]; }
  return tot;
}
void randgate(int t){ int a=rnd()%W,b; do b=rnd()%W; while(b==a); if(a>b){int x=a;a=b;b=x;} ga[t]=a; gb[t]=b; gf[t]=1+rnd()%7; }
int main(int argc,char**argv){
  FILE*F=fopen(argv[1],"r"); fscanf(F,"%d",&NC);
  for(int c=0;c<NC;c++){ int a,b,d; fscanf(F,"%d %d %d",&a,&b,&d); cm[c]=a|(b<<1)|(d<<2);
    for(int w=0;w<W;w++) fscanf(F,"%d",&st[c][w]); for(int w=0;w<W;w++) fscanf(F,"%d",&en[c][w]); }
  K=atoi(argv[2]); rs=atoll(argv[3])*2654435761ULL+12345; long long IT=atoll(argv[4]);
  int best=1<<30;
  for(int rest=0;;rest++){
    for(int t=0;t<K;t++) randgate(t);
    int cur=cost(); double T0=3.0;
    for(long long it=0;it<IT;it++){
      double T=T0*(1-(double)it/IT)+0.05;
      int t=rnd()%K, sa=ga[t],sb=gb[t],sf=gf[t]; int mv=rnd()%4; int t2=-1;
      if(mv==0) randgate(t);
      else if(mv==1) gf[t]=1+rnd()%7;
      else if(mv==2){ int w=rnd()%W; if(rnd()&1){ if(w!=gb[t]) ga[t]=w; } else { if(w!=ga[t]) gb[t]=w; } if(ga[t]>gb[t]){int x=ga[t];ga[t]=gb[t];gb[t]=x;} }
      else { t2=rnd()%K; int x; x=ga[t];ga[t]=ga[t2];ga[t2]=x; x=gb[t];gb[t]=gb[t2];gb[t2]=x; x=gf[t];gf[t]=gf[t2];gf[t2]=x; }
      int nc=cost();
      if(nc<=cur || exp((cur-nc)/T) > (rnd()%1000000)/1e6){ cur=nc; }
      else { if(t2>=0){ int x; x=ga[t];ga[t]=ga[t2];ga[t2]=x; x=gb[t];gb[t]=gb[t2];gb[t2]=x; x=gf[t];gf[t]=gf[t2];gf[t2]=x; } else { ga[t]=sa; gb[t]=sb; gf[t]=sf; } }
      if(cur==0) break;
    }
    if(cur<best){ best=cur; printf("restart %d best %d\n",rest,best); fflush(stdout); }
    if(cur==0){ for(int t=0;t<K;t++) printf("gate %d pair %d %d form %d\n",t,ga[t],gb[t],gf[t]); fflush(stdout); return 0; }
  }
}
