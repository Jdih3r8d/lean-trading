import pandas as pd, numpy as np, json
from cands import *
A_e,A_x=sma(10)>sma(30),sma(10)<sma(30)
drop=c/c.shift(5)-1
trA,dA=stream(A_e,A_x); trB,dB=stream(drop<=-0.12,mh=3); trB10,dB10=stream(drop<=-0.10,mh=3)
comb=0.5*dA+0.5*dB; bh=c.pct_change().fillna(0)
def perf(d):
    eq=(1+d).cumprod(); return dict(CAGR=eq.iloc[-1]**(252/len(d))-1, Sharpe=d.mean()/d.std()*np.sqrt(252), MDD=(eq/eq.cummax()-1).min(), Total=eq.iloc[-1]-1)
P={}
for lab,lo,hi in (('2010-2018','2010','2018'),('2019-2026','2019','2026'),('2023-2026','2023','2026'),('2026 YTD','2026','2026'),('Todo','2010','2026')):
    P[lab]={k:{m:round(float(v),3) for m,v in perf(s[lo:hi]).items()} for k,s in (('Sistema A+B',comb),('A Tendencia',dA),('B Capitulacion',dB),('Buy&Hold',bh))}
for k,v in P.items(): print(k, v)
def trades(tr,name):
    t=pd.DataFrame(tr,columns=['sig','xi','ret','hold']).astype({'sig':int,'xi':int})
    t['modulo']=name; t['senal']=idx[t.sig]; t['entrada']=idx[np.minimum(t.sig+1,len(idx)-1)]; t['salida']=idx[t.xi]
    t['px_in']=df.open.values[np.minimum(t.sig+1,len(idx)-1)]; t['px_out']=np.where(t.xi>t.sig+1, df.open.values[t.xi], np.nan)
    return t[['modulo','senal','entrada','salida','px_in','px_out','hold','ret']]
T=pd.concat([trades(trA,'A'),trades(trB,'B')]).sort_values('entrada')
T.to_csv('trades.csv',index=False)
for m in 'AB':
    r=T[T.modulo==m]
    for lab,lo in (('todo','2010'),('2019+','2019'),('2023+','2023')):
        x=r[r.senal>=lo].ret; print(m,lab,'n=%d avg=%.2f%% med=%.2f%% win=%.0f%% avgwin=%.2f%% avgloss=%.2f%% hold=%.1f PF=%.2f'%(len(x),x.mean()*100,x.median()*100,(x>0).mean()*100,x[x>0].mean()*100,x[x<0].mean()*100,r[r.senal>=lo].hold.mean(),x[x>0].sum()/-x[x<0].sum()))
print(T.tail(12).to_string())
# current state
last=idx[-1]; print('last date',last, 'close',c.iloc[-1],'SMA10',round(sma(10).iloc[-1],2),'SMA30',round(sma(30).iloc[-1],2),'drop5d',round(drop.iloc[-1],4))
print('drop threshold price for tomorrow-ish: close needed <= %.2f (12%% below close 4 sessions ago at %s %.2f)'%(c.iloc[-5]*0.88, idx[-5].date(), c.iloc[-5]))
print(pd.DataFrame({'c':c,'s10':sma(10),'s30':sma(30),'drop5':drop}).tail(12).round(3))
yr=pd.DataFrame({'Sistema':(1+comb).groupby(comb.index.year).prod()-1,'B&H':(1+bh).groupby(bh.index.year).prod()-1})
print((yr*100).round(1).T.to_string())
json.dump(dict(perf=P,yearly=(yr*100).round(1).to_dict()),open('summary.json','w'),default=str,indent=1)
pd.DataFrame({'sistema':(1+comb).cumprod(),'bh':(1+bh).cumprod(),'A':(1+dA).cumprod(),'B':(1+dB).cumprod()}).to_csv('equity.csv')
