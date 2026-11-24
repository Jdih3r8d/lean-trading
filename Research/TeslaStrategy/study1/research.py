import numpy as np, pandas as pd, itertools, sys
from engine import *
df = load()
O,H,L,C = [df[c].values.astype(float) for c in ['open','high','low','close']]
c = df.close; idx = df.index.values
SPLIT = np.datetime64('2019-01-01')
n = len(c)
sma = {k: c.rolling(k).mean() for k in [5,10,20,30,50,100,150,200]}
rs = {k: rsi(c,k) for k in [2,3,4,5,14]}
ibs = ((df.close-df.low)/(df.high-df.low)).fillna(0.5)
NO = np.zeros(n,bool)
rows=[]
def run(name, params, entry, exitsig=NO, side=1, max_hold=10**6, stop=0., tp=0., mode=0):
    entry = np.nan_to_num(np.asarray(entry,dtype=float)).astype(bool)
    exitsig = np.nan_to_num(np.asarray(exitsig,dtype=float)).astype(bool)
    tr, daily, pos = sim(O,H,L,C,entry,exitsig,side,max_hold,stop,tp,mode,COST)
    a = stats(tr,daily,idx,None,SPLIT); b = stats(tr,daily,idx,SPLIT,None)
    row = dict(fam=name, params=params, side=side, mode=mode)
    for p,s in (('is',a),('oos',b)):
        for k,v in s.items(): row[f'{p}_{k}']=v
    rows.append(row)

filters = {'none': np.ones(n,bool), 'sma200': (c>sma[200]).values, 'sma100': (c>sma[100]).values, 'sma50': (c>sma[50]).values}

for mode in (0,1):
  # MR1 RSI
  for rn,x,fk,ex,mh in itertools.product([2,3,4,5],[5,10,15,20,25,30],filters,['rsi50','rsi65','rsi75','sma5','hold'],[3,5,10,20]):
    e = (rs[rn]<x).values & filters[fk]
    exs = {'rsi50':rs[rn]>50,'rsi65':rs[rn]>65,'rsi75':rs[rn]>75,'sma5':c>sma[5],'hold':NO}[ex]
    run('RSI_MR', f'rsi{rn}<{x} f={fk} exit={ex} mh={mh}', e, np.asarray(exs), max_hold=mh, mode=mode)
  # MR2 consecutive down closes
  dn = (c<c.shift()).astype(int)
  for k,fk,ex,mh in itertools.product([2,3,4,5],filters,['upclose','sma5','hold'],[1,3,5,10]):
    e = (dn.rolling(k).sum()==k).values & filters[fk]
    exs = {'upclose':(c>c.shift()).values,'sma5':(c>sma[5]).values,'hold':NO}[ex]
    run('DownDays', f'{k}down f={fk} exit={ex} mh={mh}', e, exs, max_hold=mh, mode=mode)
  # MR3 drop over k days
  for k,x,fk,mh in itertools.product([1,2,3,5,10],[0.05,0.08,0.10,0.15,0.20,0.25],filters,[1,2,3,5,10,20]):
    e = (c/c.shift(k)-1 <= -x).values & filters[fk]
    run('Drop', f'drop{k}d>={x:.0%} f={fk} mh={mh}', e, max_hold=mh, mode=mode)
  # MR4 Bollinger
  for z,fk,mh in itertools.product([1.5,2.0,2.5],filters,[5,10,20]):
    m20=sma[20]; sd=c.rolling(20).std()
    run('Boll', f'z={z} f={fk} mh={mh}', ((c<m20-z*sd)).values & filters[fk], (c>m20).values, max_hold=mh, mode=mode)
  # IBS
  for x,fk,mh in itertools.product([0.1,0.15,0.2,0.25],filters,[1,3,5]):
    run('IBS', f'ibs<{x} f={fk} mh={mh}', (ibs<x).values & filters[fk], (ibs>0.7).values, max_hold=mh, mode=mode)
  # Big up day continuation / reversal
  r1 = c.pct_change()
  for x,mh in itertools.product([0.05,0.08,0.10,0.15],[1,3,5,10,20]):
    run('BigUp_long', f'up>={x:.0%} mh={mh}', (r1>=x).values, max_hold=mh, mode=mode)
    run('BigUp_short', f'up>={x:.0%} mh={mh}', (r1>=x).values, side=-1, max_hold=mh, mode=mode)
  # Overbought shorts
  for rn,x,mh in itertools.product([2,3,5],[90,95,98],[1,3,5,10]):
    run('RSI_short', f'rsi{rn}>{x} mh={mh}', (rs[rn]>x).values & (c<sma[200]).values, (rs[rn]<50).values, side=-1, max_hold=mh, mode=mode)
  # Trend: close above SMA
  for k in [20,30,50,100,150,200]:
    run('SMA_trend', f'c>sma{k}', (c>sma[k]).values, (c<sma[k]).values, mode=mode)
    run('SMA_trend_short', f'c<sma{k}', (c<sma[k]).values, (c>sma[k]).values, side=-1, mode=mode)
  for f_,s_ in [(5,20),(10,30),(10,50),(20,50),(20,100),(50,100),(50,200),(100,200)]:
    fa=c.rolling(f_).mean(); sl=c.rolling(s_).mean()
    run('SMA_cross', f'{f_}/{s_}', (fa>sl).values, (fa<sl).values, mode=mode)
  # Donchian
  for N,M,st in itertools.product([10,20,40,55,100,252],[5,10,20,40],[0,0.1,0.15,0.2]):
    if M>=N: continue
    hiN = c.rolling(N).max(); loM = c.rolling(M).min()
    run('Donchian', f'N={N} M={M} stop={st}', (c>=hiN).values, (c<=loM).values, stop=st, mode=mode)
  # TS momentum
  for lb in [21,63,126,252]:
    m = c/c.shift(lb)-1
    run('TSMOM', f'lb={lb}', (m>0).values, (m<0).values, mode=mode)

res = pd.DataFrame(rows)
res.to_pickle('grid.pkl')
print(len(res),'configs')
# buy and hold
for lo,hi,lab in [(None,SPLIT,'IS'),(SPLIT,None,'OOS')]:
    e=np.zeros(n,bool); 
    s = df.index.searchsorted(pd.Timestamp(lo)) if lo is not None else 0
    e[s]=True
    tr,daily,pos = sim(O,H,L,C,e,NO,1,10**6,0.,0.,1,COST)
    if hi is not None:
        pass
    print(lab,'B&H', {k:round(v,4) for k,v in stats(tr,daily,idx,lo,hi).items() if k in ('cagr','mdd','sharpe','tot')})
