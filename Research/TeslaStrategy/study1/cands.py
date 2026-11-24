import pandas as pd, numpy as np, itertools
from engine import *
df=load(); O,H,L,C=[df[k].values.astype(float) for k in ['open','high','low','close']]; c=df.close; idx=df.index; n=len(c)
NO=np.zeros(n,bool)
def B(x): return np.nan_to_num(np.asarray(x,dtype=float)).astype(bool)
def stream(entry,exitsig=NO,side=1,mh=10**6,stop=0.,tp=0.,mode=0,cost=COST):
    tr,daily,pos=sim(O,H,L,C,B(entry),B(exitsig),side,mh,stop,tp,mode,cost)
    return tr,pd.Series(daily,idx)
sma=lambda k:c.rolling(k).mean()
def cands(cost=COST):
    S={}
    for N,M in [(20,10),(20,5),(40,10),(40,20),(55,20),(100,20),(100,40)]:
        S[f'Donchian {N}/{M}']=stream(c>=c.rolling(N).max(), c<=c.rolling(M).min(),cost=cost)
    for f,s in [(5,20),(10,30),(10,50),(20,50),(50,200)]:
        S[f'SMA {f}/{s}']=stream(sma(f)>sma(s), sma(f)<sma(s),cost=cost)
    for k in [20,30,50,100,200]:
        S[f'C>SMA{k}']=stream(c>sma(k),c<sma(k),cost=cost)
    for lb in [21,63,126]:
        m=c/c.shift(lb)-1; S[f'TSMOM {lb}']=stream(m>0,m<0,cost=cost)
    r4=rsi(c,4); r5=rsi(c,5)
    S['RSI4<25&>SMA100 x50']=stream((r4<25)&(c>sma(100)), r4>50, mh=10,cost=cost)
    S['RSI5<30 x50 mh10']=stream(r5<30, r5>50, mh=10,cost=cost)
    S['Drop5d>=10% hold3']=stream(c/c.shift(5)-1<=-0.10, mh=3,cost=cost)
    # overnight streams (enter close, exit next open)
    on=(df.open.shift(-1)/c-1); intra=c/df.open-1; r1=c.pct_change()
    for nm,m in [('ON green',intra>0),('ON green>2%',intra>0.02),('ON up close',r1>0),('ON all',intra==intra)]:
        m=m.fillna(False)
        d=(on.where(m,0.0)-np.where(m,2*cost,0)).shift(1).fillna(0)   # realised on next day
        tr=np.column_stack([np.where(m)[0],np.where(m)[0]+1,(on[m]-2*cost).values,np.ones(m.sum())])
        tr=tr[~np.isnan(tr[:,2])]
        S[nm]=(tr,d)
    S['Buy&Hold']=(np.array([[0,n-1,C[-1]/C[0]-1,n]]),c.pct_change().fillna(0))
    return S
