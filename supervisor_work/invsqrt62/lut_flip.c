// GF(2) flip-graph search for tensor rank (Kauers-Moosbauer style)
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
typedef uint64_t u64;
#define MAXT 4096
u64 T[MAXT][3]; int n;
static u64 rs=88172645463325252ULL;
static inline u64 rnd(){rs^=rs<<13;rs^=rs>>7;rs^=rs<<17;return rs;}
void del(int i){ T[i][0]=T[n-1][0];T[i][1]=T[n-1][1];T[i][2]=T[n-1][2]; n--; }
// try reductions involving term i; return 1 if something changed
int reduce(int i){
  for(int j=0;j<n;j++){ if(j==i) continue;
    for(int t=0;t<3;t++){ int u=(t+1)%3,v=(t+2)%3;
      if(T[i][u]==T[j][u]&&T[i][v]==T[j][v]){ T[j][t]^=T[i][t]; del(i); 
         if(T[j>=n?i:j][t]==0){} return 1; }
    }
  }
  return 0;
}
void cleanup(){ int ch=1; while(ch){ch=0; for(int i=0;i<n;i++){ if(!T[i][0]||!T[i][1]||!T[i][2]){del(i);ch=1;i--;continue;} if(reduce(i)){ch=1;break;} } } }
int main(int argc,char**argv){
  FILE*f=fopen(argv[1],"r"); fscanf(f,"%d",&n); for(int i=0;i<n;i++) fscanf(f,"%lu %lu %lu",&T[i][0],&T[i][1],&T[i][2]); fclose(f);
  long iters=atol(argv[2]); rs^=atol(argv[3])*2654435761ULL; long plat=atol(argv[4]); const char*outp=argv[5];
  int target=argc>6?atoi(argv[6]):0;
  cleanup(); int best=n; long last=0; printf("start %d\n",n); fflush(stdout);
  static u64 B[MAXT][3]; int bn=n; memcpy(B,T,sizeof(u64)*3*n);
  for(long it=0;it<iters;it++){
    int i=rnd()%n, t=rnd()%3, j=-1;
    // find random j with T[j][t]==T[i][t]
    int start=rnd()%n;
    for(int k=0;k<n;k++){int jj=(start+k)%n; if(jj!=i&&T[jj][t]==T[i][t]){j=jj;break;}}
    if(j<0) continue;
    int u=(t+1)%3,v=(t+2)%3; if(rnd()&1){int w=u;u=v;v=w;}
    // (x,bi,ci)+(x,bj,cj) -> (x,bi+bj,ci)+(x,bj,cj+ci)
    T[i][u]^=T[j][u]; T[j][v]^=T[i][v];
    if(!T[i][u]){del(i); cleanup();}
    else if(!T[j][v]){del(j); cleanup();}
    else { int ch=0; for(int k=0;k<n;k++){ if(k==i) continue; for(int s=0;s<3;s++){int p=(s+1)%3,q=(s+2)%3; if(T[i][p]==T[k][p]&&T[i][q]==T[k][q]){ch=1;}} } 
           int ch2=0; for(int k=0;k<n;k++){ if(k==j) continue; for(int s=0;s<3;s++){int p=(s+1)%3,q=(s+2)%3; if(T[j][p]==T[k][p]&&T[j][q]==T[k][q]){ch2=1;}} }
           if(ch||ch2) cleanup(); }
    if(n<best){best=n;last=it;memcpy(B,T,sizeof(u64)*3*n);bn=n;printf("it %ld rank %d\n",it,n);fflush(stdout);
      FILE*o=fopen(outp,"w");fprintf(o,"%d\n",n);for(int k=0;k<n;k++)fprintf(o,"%lu %lu %lu\n",T[k][0],T[k][1],T[k][2]);fclose(o);
      if(n<=target) break;}
    if(it-last>plat){ // plus transition from best
      memcpy(T,B,sizeof(u64)*3*bn); n=bn;
      int a=rnd()%n,b=rnd()%n; if(a==b) continue; int t2=rnd()%3; int u2=(t2+1)%3,v2=(t2+2)%3;
      // x_a⊗y_a⊗z_a + x_b⊗y_b⊗z_b = x_a⊗y_a⊗z_a + x_a⊗y_b⊗z_b + (x_a+x_b)⊗y_b⊗z_b  (t2 is the 'x' slot)
      if(n<MAXT-1){ T[n][t2]=T[a][t2]; T[n][u2]=T[b][u2]; T[n][v2]=T[b][v2]; T[b][t2]^=T[a][t2]; n++; if(!T[b][t2]){del(b);} }
      last=it;
    }
  }
  printf("best %d\n",best);
}
