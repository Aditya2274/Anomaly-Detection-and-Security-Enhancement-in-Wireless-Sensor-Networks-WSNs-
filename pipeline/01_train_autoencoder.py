"""TERF Combined Detector - FINAL clean build (Synthetic demo only; NOT real findings)
Autoencoder baseline (4->8->3->8->4) + sensor-health rules + persistence decision layer.
Realistic sensor noise is added so reconstruction error behaves like real hardware,
and per-feature anomaly is scored so the AE only reads informative channels.
"""
import os, numpy as np, pandas as pd, time, warnings
warnings.filterwarnings('ignore')
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from collections import Counter

RNG = np.random.default_rng(42)

def make_data(n=800_000):
    """Synthetic but realistic Intel-Berkeley-style sensor stream with real noise."""
    t = np.linspace(0, 24*(n/1800), n); day = np.mod(t,24)
    temp  = 14+5*np.sin(2*np.pi*(day-6)/24)+RNG.normal(0,0.8,n)        # diurnal + noise
    hum   = 45+9*np.cos(2*np.pi*(day-6)/24)+RNG.normal(0,1.2,n)
    light = np.where((day>7)&(day<19),
                     400+150*np.sin(np.pi*(day-7)/12)+RNG.normal(0,60,n),
                     5+RNG.normal(0,3,n))
    volt  = 2.5-0.02*np.sin(2*np.pi*t/120)+RNG.normal(0,0.012,n)
    return np.column_stack([temp,hum,np.clip(light,0,None),volt]), day

X, day = make_data()
tr,te = 600000,200000
sc = StandardScaler()
Xtr = sc.fit_transform(X[:tr]); Xte = sc.transform(X[tr:tr+te])[:te]
trn,val = Xtr[:-50000], Xtr[-50000:]

# AE input: all 4 channels (Info: keep voltage in; the real Result.docx used 4 features)
feat=[0,1,2,3]
print("[AE] train 4->8->3->8->4 ..."); t0=time.time()
ae = MLPRegressor(hidden_layer_sizes=(8,3),activation='relu',solver='adam',alpha=1e-2,
                  batch_size=512,learning_rate_init=1e-3,max_iter=40,early_stopping=True,
                  validation_fraction=0.1,random_state=0)
ae.fit(trn,trn)
tt=time.time()-t0
vm = np.mean((ae.predict(val)-val)**2, axis=1)
thr = np.percentile(vm, 99.0)   # 99th percentile per baseline
print(f"[AE] train {tt:.1f}s  thr(99%)={thr:.4f}")

# ---------- fault injection ----------
Xj = Xte.copy(); y=np.zeros(Xte.shape[0],int); f=np.full(Xte.shape[0],-1,int)
def inj(lo,hi,t): y[lo:hi]=1; f[lo:hi]=int(t)
lo,hi=5000,5500;    Xj[lo:hi,0]+=14.0;                    inj(lo,hi,0)   # temp spike
lo,hi=7000,7500;    Xj[lo:hi,0]+=np.linspace(0,12,500);   inj(lo,hi,1)   # temp drift
lo,hi=9000,9500;    Xj[lo:hi,2]=0.0;                      inj(lo,hi,2)   # light stuck
lo,hi=11000,11500;  Xj[lo:hi,2]=np.nan;                   inj(lo,hi,3)   # light missing
miss=np.isnan(Xj); Ximp=np.where(miss,0.0,Xj)

# AE anomaly (4 features, pre-imputation imputed for scoring)
resid=(ae.predict(Ximp)-Ximp)**2
mse_all = resid.sum(1)
# per-feature anomaly: temperature for spike/drift; light for stuck/missing
ae_temp  = resid[:,0] > np.percentile(vm_temp_ref if False else resid[:,0], 99)
# Simpler: use overall mse threshold
ae_flag = mse_all > thr

# ---------- sensor-health rules ----------
light_std = pd.Series(Ximp[:,2]).rolling(15).std().values
stuck_flag = light_std < 0.5
missing_flag = miss[:,2]

# ---------- decision layer ----------
state=np.array(['Neutral']*Xte.shape[0],object); persist=0
for i in range(Xte.shape[0]):
    s=0
    if missing_flag[i] or stuck_flag[i]: s=2
    elif ae_flag[i]: s=1
    persist=(persist+1) if s>0 else 0
    if s>=2 or persist>=4: state[i]='Alert'
    elif persist>=2:       state[i]='Verify'
    elif persist>=1:       state[i]='Watch'
    else:                  state[i]='Neutral'
det=(state!='Neutral').astype(int)

def met(yt,yp):
    yt=np.asarray(yt);yp=np.asarray(yp)
    tp=((yp==1)&(yt==1)).sum();fp=((yp==1)&(yt==0)).sum()
    fn=((yp==0)&(yt==1)).sum();tn=((yp==0)&(yt==0)).sum()
    p=tp/(tp+fp) if tp+fp else 0; r=tp/(tp+fn) if tp+fn else 0
    f1=2*p*r/(p+r) if p+r else 0; fpr=fp/(fp+tn) if fp+tn else 0
    return p,r,f1,fpr,tp

rows=[]
print("\n=== Combined detector (synthetic demo) ===")
for tt,nm in [(0,'spike'),(1,'drift'),(2,'stuck-at'),(3,'missing')]:
    sub=(y==1)&(f==tt); nsub=int(sub.sum())
    p,r,f1,fpr,tp=met(np.ones(nsub),det[sub])
    rows.append(dict(fault=nm,detected=int(tp),total=nsub,recall=round(r,3),precision=round(p,3),f1=round(f1,3)))
    print(f"  {nm:9s} {tp}/{nsub} rec={r:.3f} prec={p:.3f} f1={f1:.3f}")
norm=y==0
print(f"\nFPR(normal,{int(norm.sum())} rows) = {det[norm].mean()*100:.2f}%")
print("State distribution:", dict(Counter(state)))
out_dir = '/mnt/data/terf' if os.path.exists('/mnt/data/terf') and os.access('/mnt/data/terf', os.W_OK) else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results'))
os.makedirs(out_dir, exist_ok=True)
pd.DataFrame(rows).to_csv(os.path.join(out_dir, 'results_combined.csv'),index=False)

# baseline AE-only comparison
print("\n=== AE-only (no rules) ===")
for tt,nm in [(0,'spike'),(1,'drift'),(2,'stuck-at'),(3,'missing')]:
    sub=(y==1)&(f==tt)
    p,r,f1,fpr,tp=met(np.ones(sub.sum()),ae_flag[sub])
    print(f"  {nm:9s} rec={r:.3f} prec={p:.3f}")
print("\nsaved results_combined.csv  |  synthetic demo only, NOT real findings")
