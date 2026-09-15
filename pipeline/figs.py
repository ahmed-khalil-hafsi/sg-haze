import json, datetime as dt, numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.rcParams.update({'font.family':'serif','font.serif':['DejaVu Serif'],'mathtext.fontset':'dejavuserif','savefig.facecolor':'#ffffff'})
import matplotlib.dates as mdates
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

BG='#ffffff'; PANEL='#ffffff'; FG='#000000'; MUT='#555555'
EPOCH=dt.date(2003,1,1)
F=np.load('fit.npz'); S=np.load('sectors.npz'); J=json.load(open('fit.json'))
HPI,y,ymax,mask,seas,obs=F['HPI'],F['y'],F['ymax'],F['mask'],F['seas'],F['obs']
COEF=F['COEF']; L=int(F['L']); LAG=int(F['LAG']); P=float(F['P']); R=float(F['R'])
nd=len(HPI); dates=np.array([EPOCH+dt.timedelta(days=i) for i in range(nd)])
years=np.array([d.year for d in dates]); doy=np.array([d.timetuple().tm_yday for d in dates])
LASTD=dates[-1]

def style(ax):
    ax.set_facecolor(PANEL)
    for s in ax.spines.values(): s.set_color('#999999')
    ax.tick_params(colors=MUT, labelsize=9)
    ax.grid(color='#dcdcdc', lw=.6)

# ================= FIGURE 1 =================
SHOW=[2015,2019,2026]
D0,D1=152,334
fig=plt.figure(figsize=(15,11.4), dpi=125); fig.patch.set_facecolor(BG)
fig.text(.06,.975,'Distance-weighted wildfire emission index and observed 24-hour PSI, Singapore', color=FG, fontsize=20, fontweight='bold', va='top')
fig.text(.06,.936,'Filled area: wildfire emissions weighted by distance from Singapore (CAMS GFAS). Solid line: NEA 24-hr PSI,\n'
                  'island average; shading extends to the worst region. Dashed line: PSI implied by the index alone.',
         color='#333333', fontsize=12, va='top', linespacing=1.5)
ymaxH=HPI[(doy>=D0)&(doy<=D1)&(years>=2014)].max()*1.06
for i,yr in enumerate(SHOW):
    ax=fig.add_axes([.075,.652-i*.262,.875,.190]); style(ax)
    k=(years==yr)&(doy>=D0)&(doy<=D1)
    ref=np.array([dt.date(2000,d.month,d.day) for d in dates[k]])
    h=HPI[k]
    ax.fill_between(ref,0,h,color='#d95f02',alpha=.82,lw=0,zorder=3)
    ax.set_ylabel('haze pressure\n(kt-effective)',color='#d95f02',fontsize=9.5)
    ax.set_ylim(0,ymaxH); ax.set_xlim(dt.date(2000,6,1),dt.date(2000,11,30))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax2=ax.twinx(); ax2.set_facecolor('none')
    for s in ax2.spines.values(): s.set_color('#999999')
    ax2.tick_params(colors='#08519c',labelsize=9)
    yy=np.where(obs[k],y[k],np.nan); ym=np.where(obs[k],ymax[k],np.nan)
    ax2.fill_between(ref,yy,ym,color='#08519c',alpha=.18,lw=0,zorder=4)
    idx=np.where(k)[0]
    mp=np.array([COEF[0]+COEF[1]*max(HPI[i-LAG],0.0)**P for i in idx])
    ax2.plot(ref,mp,color='#7a7a7a',lw=1.4,ls='--',alpha=.85,zorder=4.5)
    ax2.plot(ref,yy,color='#08519c',lw=2.0,zorder=5)
    ax2.axhline(100,color='#7a7a7a',lw=.9,ls='--',alpha=.5,zorder=2)
    ax2.axhline(200,color='#a50f15',lw=.9,ls='--',alpha=.5,zorder=2)
    ax2.set_ylim(25,330); ax2.set_ylabel('24-hr PSI',color='#08519c',fontsize=9.5)
    if np.isfinite(np.nanmax(ym)):
        j=int(np.nanargmax(ym)); pv=ym[j]
        ax2.annotate(f'peak PSI {pv:.0f}',(ref[j],min(pv,300)),color='#a50f15',fontsize=10.5,fontweight='bold',
                     xytext=(10,-4 if pv>250 else 4),textcoords='offset points')
    if yr==2026:
        cur=dt.date(2000,LASTD.month,LASTD.day)
        ax.axvline(cur,color='#000000',lw=1,ls=':',alpha=.6,zorder=6)
        ax.annotate('today',(cur,ymaxH*.86),color='#000000',fontsize=9.5,xytext=(-34,0),textcoords='offset points')
    ax.text(.008,.90,f'{yr}'+('   (season to date)' if yr==2026 else ''),transform=ax.transAxes,
            color=FG,fontsize=18,fontweight='bold',va='top')
fig.text(.075,.048,
 f'Index = sum over every 0.1° fire cell of daily carbon emissions × exp(−distance / {L} km), lagged {LAG} day, within 1800 km of Singapore.\n'
 f'Season fit (Jun–Nov, 2014–2026):  PSI ≈ {COEF[0]:.1f} + {COEF[1]:.2f} × index^{P:g},   r = {R:.2f}.   Dashed lines: PSI 100 (unhealthy), 200 (very unhealthy).\n'
 'Sources: CAMS GFAS v2 daily wildfire carbon emissions (2003–present); NEA / data.gov.sg historical 24-hr PSI (Apr 2014–present).',
 color='#555555',fontsize=9.2,va='bottom')
fig.savefig('fig1_haze_index_vs_psi.png',facecolor=BG); plt.close(fig); print('fig1 ok')

# ================= FIGURE 2 =================
C=S['C']; RINGS=S['rings']; lags=S['lags']; NSEC=int(S['nsec'])
fig=plt.figure(figsize=(16.5,8.2),dpi=125); fig.patch.set_facecolor(BG)
fig.text(.035,.968,'Fitted source apportionment and transport lag (in-sample), Singapore', color=FG,fontsize=20,fontweight='bold',va='top')
fig.text(.035,.918,'Non-negative least-squares weights, June-November 2014-2026. Season-block bootstrap intervals are given in the text.',
         color='#333333',fontsize=12,va='top')

fig.text(.030,.868,'Contribution to Singapore PSI by source bearing and distance',
         color=FG,fontsize=11.5,fontweight='bold',ha='left',va='bottom')
ax=fig.add_axes([.030,.225,.29,.615],projection='polar'); ax.set_facecolor(PANEL)
ax.set_theta_zero_location('N'); ax.set_theta_direction(-1)
cmap=plt.get_cmap('YlOrRd'); vmax=C.max(); width=2*np.pi/NSEC
for r in range(C.shape[0]):
    for s_ in range(NSEC):
        ax.bar(s_*width, RINGS[r+1]-RINGS[r], width=width*.97, bottom=RINGS[r],
               color=cmap(0.06+0.94*C[r,s_]/vmax), edgecolor=PANEL, lw=.9, zorder=3)
ax.set_ylim(0,RINGS[-1]); ax.set_yticks(RINGS[1:]); ax.set_rlabel_position(8)
import matplotlib.patheffects as pe
ax.set_yticklabels([])
for v in RINGS[1:]:
    ax.text(np.deg2rad(8), v, f'{v} km', color='#000000', fontsize=7.5, ha='center', va='bottom',
            zorder=12, path_effects=[pe.withStroke(linewidth=2.6, foreground='#ffffff')])
ax.set_xticks(np.arange(NSEC)*width)
ax.set_xticklabels(['N','NE','E','SE','S','SW','W','NW'],color=FG,fontsize=12,fontweight='bold')
ax.grid(color='#aaaaaa',lw=.5)
cax=fig.add_axes([.048,.165,.25,.016])
cb=fig.colorbar(ScalarMappable(norm=Normalize(0,vmax),cmap=cmap),cax=cax,orientation='horizontal')
cb.set_label('PSI points contributed, seasonal average',color=MUT,fontsize=8.5,labelpad=2)
cb.ax.tick_params(colors=MUT,labelsize=7.5); cb.outline.set_edgecolor('#999999')
fig.text(.030,.078,'Largest fitted weights lie in the S and SE sectors\nat 250-1200 km. Bootstrap share: 65% (95% CI 24-81%);\nthe ranking of individual bins is not stable\nunder resampling.',
         color='#333333',fontsize=9,va='top')

ax2=fig.add_axes([.405,.225,.25,.615]); style(ax2)
prov=J['prov']; top=sorted(prov.items(), key=lambda kv:-max([c for c in kv[1][0] if c is not None] or [0]))[:6]
cols=plt.get_cmap('turbo')(np.linspace(.08,.92,len(top)))
for (k,(curve,tot)),c in zip(top,cols):
    cu=[np.nan if v is None else v for v in curve]
    ax2.plot(range(len(cu)),cu,color=c,lw=2.2,marker='o',ms=4,label=k.split(' (')[0])
ax2.set_xlabel('days between the fire and Singapore’s PSI',color=MUT,fontsize=10)
ax2.set_ylabel('correlation with PSI',color=MUT,fontsize=10)
ax2.set_title('Correlation with PSI as a function of lag',color=FG,fontsize=13,fontweight='bold',pad=10)
ax2.legend(fontsize=8.5,facecolor=PANEL,edgecolor='#999999',labelcolor=FG,loc='lower left')

ax3=fig.add_axes([.735,.225,.215,.615]); style(ax3)
m=mask.copy()
sc=ax3.scatter(np.clip(HPI[m],.5,None), y[m], c=years[m], cmap='viridis', s=11, alpha=.6, lw=0)
k26=m&(years==2026)
ax3.scatter(np.clip(HPI[k26],.5,None), y[k26], facecolor='none', edgecolor='#a50f15', s=44, lw=1.5, zorder=5, label='2026')
xs=np.logspace(np.log10(.5), np.log10(max(HPI[m].max(),1)), 200)
ax3.plot(xs, COEF[0]+COEF[1]*xs**P, color='#7a7a7a', lw=2.4, zorder=6)
ax3.set_xscale('log'); ax3.set_xlabel('haze pressure index (kt-effective, log)',color=MUT,fontsize=10)
ax3.set_ylabel('24-hr PSI',color=MUT,fontsize=10)
ax3.set_title(f'every Jun–Nov day since 2014   (r = {R:.2f})',color=FG,fontsize=12,fontweight='bold',pad=10)
ax3.legend(fontsize=9,facecolor=PANEL,edgecolor='#999999',labelcolor=FG,loc='upper left')
cb2=fig.colorbar(sc,ax=ax3,fraction=.045,pad=.03); cb2.ax.tick_params(colors=MUT,labelsize=8)
cb2.outline.set_edgecolor('#999999')
fig.text(.44,.078,'Left: non-negative least-squares weights on 40 distance x bearing bins, each fitted at its own transport lag.\n'
                   'Middle: correlation of one province\u2019s daily emissions with Singapore PSI, by lag.   Right: colour = year.\n'
                   'Sources: CAMS GFAS v2 daily wildfire carbon emissions; NEA / data.gov.sg 24-hr PSI.',
         color='#555555',fontsize=9,va='top')
fig.savefig('fig2_sources_and_lag.png',facecolor=BG); plt.close(fig); print('fig2 ok')

# ================= FIGURE 3 =================
fig=plt.figure(figsize=(14,8.2),dpi=125); fig.patch.set_facecolor(BG)
fig.text(.06,.965,'Cumulative seasonal haze pressure, 2003-2026', color=FG,fontsize=20,fontweight='bold',va='top')
fig.text(.06,.918,'Cumulative distance-weighted wildfire emissions from 1 June, every burning season since 2003.',
         color='#333333',fontsize=12.5,va='top')
ax=fig.add_axes([.075,.115,.885,.755]); style(ax)
end=LASTD.timetuple().tm_yday
tot={}
for yr in range(2003,2027):
    k=(years==yr)&(doy>=152)
    cs=np.cumsum(HPI[k])/1e3   # Mt-effective
    dd=doy[k]
    tot[yr]=(dd,cs)
for yr,(dd,cs) in tot.items():
    if yr in (2015,2019,2026): continue
    ax.plot(dd,cs,color='#c4c4c4',lw=1.1,alpha=.75,zorder=2)
for yr,col,lw in [(2019,'#7a7a7a',2.4),(2015,'#a50f15',2.8),(2026,'#1b7837',3.2)]:
    dd,cs=tot[yr]; ax.plot(dd,cs,color=col,lw=lw,zorder=5,label=str(yr))
ax.axvline(end,color='#000000',ls=':',lw=1.2,alpha=.7,zorder=6)
ax.annotate(f'{LASTD.strftime("%d %b")}',(end,ax.get_ylim()[1]*.02),color='#000000',fontsize=10,
            xytext=(6,0),textcoords='offset points')
def at(yr):
    dd,cs=tot[yr]; j=np.searchsorted(dd,end); return float(cs[min(j,len(cs)-1)])
rank=sorted(((at(yr),yr) for yr in tot),reverse=True)
pos={yr:i+1 for i,(v,yr) in enumerate(rank)}
for yr,col in [(2015,'#a50f15'),(2019,'#7a7a7a'),(2026,'#1b7837')]:
    v=at(yr)
    ax.scatter([end],[v],color=col,s=60,zorder=7)
    ax.annotate(f'{yr}: {v:.2f} Mt-eff  (#{pos[yr]} of 24)',(end,v),color=col,fontsize=11,fontweight='bold',
                xytext=(10,-3),textcoords='offset points')
ax.set_xlim(152,366); ax.set_xlabel('day of year',color=MUT,fontsize=10.5)
ax.set_ylabel('cumulative haze pressure (Mt-effective)',color=MUT,fontsize=10.5)
ax.set_xticks([152,182,213,244,274,305,335,366]); ax.set_xticklabels(['1 Jun','1 Jul','1 Aug','1 Sep','1 Oct','1 Nov','1 Dec','31 Dec'])
ax.legend(fontsize=11,facecolor=PANEL,edgecolor='#999999',labelcolor=FG,loc='upper left')
fig.text(.075,.035,'Grey lines: all other years 2003-2025. "Mt-effective" = megatonnes of carbon after the exp(-distance/900 km) weighting, so it measures pressure on Singapore, not raw regional burning.',
         color='#555555',fontsize=9,va='bottom')
fig.savefig('fig3_season_ranking.png',facecolor=BG); plt.close(fig)
print('fig3 ok; rank 2026 =',pos[2026],'of',len(rank))
