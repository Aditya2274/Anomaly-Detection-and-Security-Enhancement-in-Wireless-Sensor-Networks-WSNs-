import os, numpy as np, time, warnings
warnings.filterwarnings('ignore')
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
import pandas as pd

RNG = np.random.default_rng(42)

# ===== 1. Synthetic Intel-Berkeley-style data =====
print("[1] Generate data...")
n = 800_000
t = np.linspace(0,24*(n/1800),n); day=np.mod(t,24)
temp  = 14+5*np.sin(2*np.pi*(day-6)/24)+RNG.normal(0,0.7,n)
hum   = 45+9*np.cos(2*np.pi*(day-6)/24)+RNG.normal(0,1.0,n)
light = np.where((day>7)&(day<19),400+150*np.sin(np.pi*(day-7)/12)+RNG.normal(0,40,n),5+RNG.normal(0,2,n))
volt  = 2.5-0.02*np.sin(2*np.pi*t/120)+RNG.normal(0,0.01,n)
X = np.column_stack([temp,hum,np.clip(light,0,None),volt])

train_n,test_n = 600000,200000
sc = StandardScaler()
Xtr = sc.fit_transform(X[:train_n])
Xte = sc.transform(X[train_n:train_n+test_n])[:200000]
trn, val = Xtr[:-50000], Xtr[-50000:]
print("  train",trn.shape,"val",val.shape,"test",Xte.shape)

# ===== 2. Autoencoder 4->8->3->8->4 =====
print("[2] Train autoencoder...")
t0=time.time()
ae = MLPRegressor(hidden_layer_sizes=(8,3),activation='relu',solver='adam',
                  alpha=1e-3,batch_size=512,learning_rate_init=1e-3,max_iter=25,
                  early_stopping=True,validation_fraction=0.1,random_state=0)
ae.fit(trn,trn)
train_t=time.time()-t0
vm = np.mean((ae.predict(val)-val)**2,axis=1)
thr = np.percentile(vm,99.5)
print("  thr=%.3f  train=%.1fs"%(thr,train_t))

# ===== 3. Faults =====
print("[3] Inject faults...")
Xinj=Xte.copy(); labels=np.zeros(Xte.shape[0],int); ft=np.full(Xte.shape[0],-1,int)
def inj(lo,hi,t): labels[lo:hi]=1; ft[lo:hi]=int(t)
lo,hi=5000,5500;   Xinj[lo:hi,0]+=14.0; inj(lo,hi,0)
lo,hi=7000,7500;   Xinj[lo:hi,0]+=np.linspace(0,20,500); inj(lo,hi,1)
lo,hi=9000,9500;   Xinj[lo:hi,2]=0.0;  inj(lo,hi,2)
lo,hi=11000,11500; Xinj[lo:hi,2]=np.nan; inj(lo,hi,3)
miss = np.isnan(Xinj); Ximp=np.where(miss,0.0,Xinj)

# ===== 4. Scoring =====
print("[4] Score...")
t0=time.time()
scores=(ae.predict(Ximp)-Ximp)**2; mse=scores.sum(1)
inf_t=time.time()-t0
ae_flag=(mse>thr)

def rstd(a,w):
    a=np.asarray(a,float); o=np.full(len(a),np.nan)
    for i in range(w,len(a)+1): o[i-1]=a[i-w:i].std()
    return o
ls=rstd(Ximp[:,2],25)
stuck=ls<0.5
mflag=miss[:,2]

# ===== 5. Decision layer =====
print("[5] Decision layer...")
state=np.array(['Normal']*Xte.shape[0],dtype=object)
persist=0
for i in range(Xte.shape[0]):
    s=0
    if mflag[i] or stuck[i]: s=2
    elif ae_flag[i]: s=1
    persist = persist+1 if s>0 else 0
    if s>=2 or persist>=4:  state[i]='Alert'
    elif persist>=2:        state[i]='Verify'
    elif persist>=1:        state[i]='Watch'
    else:                   state[i]='Normal'
det=(state!='Normal').astype(int)

def met(yt,yp):
    yt=np.asarray(yt); yp=np.asarray(yp)
    tp=((yp==1)&(yt==1)).sum(); fp=((yp==1)&(yt==0)).sum(); fn=((yp==0)&(yt==1)).sum(); tn=((yp==0)&(yt==0)).sum()
    p = tp/(tp+fp) if tp+fp else 0; r=tp/(tp+fn) if tp+fn else 0
    f1=2*p*r/(p+r) if p+r else 0; fpr=fp/(fp+tn) if fp+tn else 0
    return p,r,f1,fpr,tp

# ===== 6. Results =====
rows=[]
print("\n--- Per-fault detection (trained detector) ---")
for tt,nm in [(0,'spike'),(1,'drift'),(2,'stuck-at'),(3,'missing')]:
    sub=(labels==1)&(ft==tt)
    n_sub=int(sub.sum())
    yt=np.ones(n_sub); yp=det[sub]
    p,r,f1,fpr,tp = met(yt,yp)
    rows.append(dict(fault=nm,detected=int(tp),total=n_sub,recall=round(r,4),precision=round(p,4),f1=round(f1,4)))
    print(f"  {nm:8s}: {tp}/{n_sub}  rec={r:.3f} prec={p:.3f} f1={f1:.3f}")

norm=labels==0
fpr_norm=det[norm].mean()
print(f"\nFalse-positive rate on {int(norm.sum())} normal rows: {fpr_norm*100:.2f}%")

# state distribution
from collections import Counter
print("\nState distribution:", dict(Counter(state)))

out_dir = '/mnt/data/terf' if os.path.exists('/mnt/data/terf') and os.access('/mnt/data/terf', os.W_OK) else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results'))
os.makedirs(out_dir, exist_ok=True)
out_csv = os.path.join(out_dir, 'results.csv')
pd.DataFrame(rows).to_csv(out_csv,index=False)
print(f"Saved {out_csv}")
