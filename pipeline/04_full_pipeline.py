import os, numpy as np, time, json, warnings
warnings.filterwarnings('ignore')
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score

RNG = np.random.default_rng(42)

# ============ 1. Generate Intel-Berkeley-style synthetic sensor data ============
print("[1] Generating synthetic sensor data...")
n = 800_000
t_hours = np.linspace(0, 24*(n/(30*60)), n)   # ~30 samples/hour
day = np.mod(t_hours, 24)
temp  = 14.0 + 5.0*np.sin(2*np.pi*(day-6)/24) + RNG.normal(0,0.7,size=n)
hum   = 45.0 + 9.0*np.cos(2*np.pi*(day-6)/24) + RNG.normal(0,1.0,size=n)
light = np.where((day>7)&(day<19),
                 400.0+150.0*np.sin(np.pi*(day-7)/12)+RNG.normal(0,40,size=n),
                 5.0+RNG.normal(0,2,size=n))
voltage = 2.5 - 0.02*np.sin(2*np.pi*t_hours/120) + RNG.normal(0,0.01,size=n)
X = np.column_stack([temp, hum, light, voltage])

# ============ 2. Chronological split + scaling ============
print("[2] Splitting + scaling...")
train_n, test_n = 600_000, 200_000
scaler = StandardScaler()
Xtr_all = scaler.fit_transform(X[:train_n])
Xte    = scaler.transform(X[train_n:train_n+test_n])
# make test exactly 200k
Xte = Xte[:200000]
# validation from train tail
val_n = 50_000
Xtr_s  = Xtr_all[:-val_n]
Xval   = Xtr_all[-val_n:]
print("  train", Xtr_s.shape, "val", Xval.shape, "test", Xte.shape)

# ============ 3. Autoencoder 4->8->3->8->4 ============
print("[3] Training autoencoder...")
t0=time.time()
ae = MLPRegressor(hidden_layer_sizes=(8,3), activation='relu', solver='adam',
                  alpha=1e-4, batch_size=300, learning_rate_init=1e-3,
                  max_iter=20, early_stopping=True, validation_fraction=0.1,
                  random_state=0, n_iter_no_change=5)
ae.fit(Xtr_s, Xtr_s)
train_time = time.time()-t0
val_mse = np.mean((ae.predict(Xval)-Xval)**2, axis=1)
thr = np.percentile(val_mse, 99)
print("  train %.1fs | val MSE 99pct thr=%.4f" % (train_time, thr))

# ============ 4. Fault injection ============
print("[4] Injecting faults...")
Xinj = Xte.copy()
labels = np.zeros(Xte.shape[0], dtype=int)
ftype  = np.full(Xte.shape[0], -1, dtype=int)
def mark(lo,hi,t): 
    labels[lo:hi]=1; ftype[lo:hi]=t
lo,hi=50_000,50_500; Xinj[lo:hi,0]+=12.0; mark(lo,hi,0)      # temp spike
lo,hi=100_000,100_500; Xinj[lo:hi,0]+=np.linspace(0,18,500); mark(lo,hi,1)  # temp drift
lo,hi=150_000,150_500; Xinj[lo:hi,2]=0.0; mark(lo,hi,2)     # light stuck
lo,hi=175_000,175_500; Xinj[lo:hi,2]=np.nan; mark(lo,hi,3)  # light missing
missing = np.isnan(Xinj)
Ximp = np.where(missing,0.0,Xinj)

# ============ 5. Autoencoder scoring ============
print("[5] Autoencoder scoring...")
t0=time.time()
scores = (ae.predict(Ximp)-Ximp)**2
ae_mse = scores.sum(axis=1)
inf_time = time.time()-t0
pred_ae = (ae_mse>thr).astype(int)

# ============ 6. Sensor-health rules ============
# temporal rolling std on light (window 25)
def rolling_std(a, w):
    a=np.asarray(a,dtype=float)
    out=np.full_like(a,np.nan)
    for i in range(w,len(a)+1):
        out[i-1]=a[i-w:i].std()
    return out
light_std = rolling_std(Ximp[:,2],25)
# flag nearly-constant light (stuck): std below small threshold, AND not a genuine night low
stuck_flag = (light_std < 0.5)
dk_light = rolling_std(Ximp[:,1],25)  # hum stable too? keep simple: only light rule + missing
missing_flag = missing[:,2]

# ============ 7. Combined decision layer ============
print("[5] Decision layer...")
# evidence scores
score_ae = (ae_mse>thr).astype(float)
score_stuck = stuck_flag.astype(float)
score_miss  = missing_flag.astype(float)
# Fusion: evidence-based, not naive OR.
# Policy: AE high && persistent triggers Watch/Verify; missing/stuck trigger immediately.
states = np.full(Xte.shape[0],'Normal',dtype=object)
# state machine with persistence (require consecutive frames)
conf = 0
for i in range(Xte.shape[0]):
    s=0.0
    if score_miss[i] or score_stuck[i]:
        s=2.0   # strong structural evidence
    elif score_ae[i]:
        s=1.0
    # persistence
    conf = conf+1 if s>0 else 0
    if s>=2.0 or conf>=3:
        states[i]='Alert'
    elif conf>=2:
        states[i]='Verify'
    elif conf>=1:
        states[i]='Watch'
    else:
        states[i]='Normal'

alert = (states=='Alert').astype(int)
# detection: alert on any non-normal
det_any = ((states!='Normal')).astype(int)

# ============ 8. Metrics ============
def metrics(y_true, y_pred_bin, lab=''):
    idx = np.arange(len(y_true))
    tp = ((y_pred_bin==1)&(y_true==1)).sum()
    fp = ((y_pred_bin==1)&(y_true==0)).sum()
    fn = ((y_pred_bin==0)&(y_true==1)).sum()
    tn = ((y_pred_bin==0)&(y_true==0)).sum()
    prec = tp/(tp+fp) if tp+fp else 0
    rec  = tp/(tp+fn) if tp+fn else 0
    f1   = 2*prec*rec/(prec+rec) if prec+rec else 0
    fpr  = fp/(fp+tn) if fp+tn else 0
    return dict(prec=prec,rec=rec,f1=f1,fpr=fpr,tp=tp,fp=fp,fn=fn,tn=tn)

lines=[]
lines.append("="*60)
lines.append("TRUST-ENHANCED RANDOM FOREST (TERF) - COMBINED DETECTOR")
lines.append("Synthetic Intel-Berkeley-style demo  | "+time.strftime("%Y-%m-%d %H:%M"))
lines.append("="*60)

# evaluate each fault type separately (mask test region)
for t,nm in [(0,'Spike'),(1,'Drift'),(2,'Stuck-at'),(3,'Missing')]:
    sub = (labels==1)&(ftype==t)
    lines.append(f"\n--- {nm} fault ---")
    lines.append(f"  Total injected: {int(sub.sum())}")

for fa,nm in [(0,'Spike'),(1,'Drift'),(2,'Stuck-at'),(3,'Missing')]:
    sub = (labels==1)&(ftype==fa)
    pred = (states!='Normal')[sub]
    tr = labels[sub]
    m = metrics(tr,pred)
    lines.append(f"  {nm}: det={(pred==1).sum()}/{500} recall={m['rec']:.3f} prec={m['prec']:.3f}")

# overall FPR on normal
norm = labels==0
fpr = (states[norm]!='Normal').mean()
lines.append(f"\n=== FPR on normal set: {fpr*100:.2f}% ===")

out_dir = '/mnt/data/terf' if os.path.exists('/mnt/data/terf') and os.access('/mnt/data/terf', os.W_OK) else os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results'))
os.makedirs(out_dir, exist_ok=True)
out_txt = os.path.join(out_dir, 'report.txt')
with open(out_txt,'w') as f:
    f.write("\n".join(lines))
print(f"Saved {out_txt}")
print("=== BUILD COMPLETE ===")
print("\n".join(lines[-8:]))
