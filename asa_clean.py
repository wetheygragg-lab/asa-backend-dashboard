#!/usr/bin/env python3
"""ASA Backend Report - Single Clean Script"""
import json, os, pandas as pd

# ══════════════════════════════════════════════════════════════
# STEP 1 — Generate JSON
# ══════════════════════════════════════════════════════════════
print("Step 1: Excel → JSON ...")
file = '/Users/benny/Desktop/听脑ai/广告数据/asa后端数据/asa广告后端分析.xlsx'
ad  = pd.read_excel(file, sheet_name='广告端数据')
be  = pd.read_excel(file, sheet_name='后端数据')

ad['df'] = ad['日期'].apply(lambda x: x[5:7]+'-'+x[8:10] if isinstance(x,str) and len(x)>=10 else '')
be['df'] = be['row_id'].apply(lambda x: x[5:7]+'-'+x[8:10] if isinstance(x,str) and len(x)>=10 else '')
ad = ad.rename(columns={'安装次数（总计）':'安装次数','广告系列名称':'cs'})

be_lu = be.groupby(['df','广告系列名称']).agg({
    '激活数':'sum','注册人数':'sum','总充值金额':'sum','支出':'sum'
}).reset_index()
be_lu.columns = ['df','cs','激活数_b','注册人数_b','充值_b','支出_b']

# OUTER JOIN: 保留广告端和后端全部记录
m = ad.merge(be_lu, on=['df','cs'], how='outer')

# 填充 NaN
for c in ['激活数_b','注册人数_b','充值_b','支出_b']:
    m[c] = m[c].fillna(0)
for c in ['支出','展示次数','点击次数','安装次数']:
    m[c] = m[c].fillna(0)

# 广告端有的行：用广告端支出/展示/点击/安装，后端数据补充
m['激活数']     = m.apply(lambda r: r['激活数_b'] if r['激活数_b'] else r['激活数'], axis=1)
m['注册人数']   = m.apply(lambda r: r['注册人数_b'] if r['注册人数_b'] else r['注册人数'], axis=1)
m['总充值金额'] = m.apply(lambda r: r['充值_b'] if r['充值_b'] else r['总充值金额'], axis=1)
m['支出']       = m.apply(lambda r: r['支出_b'] if r['支出_b'] and r['支出'] == 0 else r['支出'], axis=1)
m['安装次数']   = m.apply(lambda r: r['安装次数'] if r['安装次数'] > 0 else 0, axis=1)

def rate(a,b): return float(a)/float(b) if float(b)!=0 else 0.0
def jnum(v):
    """Convert to JSON-safe number: NaN/inf → 0"""
    try:
        f = float(v)
        if v != v or abs(f) == float('inf'):  # NaN or inf
            return 0.0
        return f
    except:
        return 0.0
m['点击率'] = [rate(r['点击次数'],r['展示次数']) for _,r in m.iterrows()]
m['安装率'] = [rate(r['安装次数'],r['点击次数']) for _,r in m.iterrows()]
m['激活率'] = [rate(r['激活数'],r['安装次数']) for _,r in m.iterrows()]
m['注册率'] = [rate(r['注册人数'],r['激活数']) for _,r in m.iterrows()]
m['roi']    = [rate(r['总充值金额'],r['支出']) for _,r in m.iterrows()]
m['词类']   = m['cs'].apply(lambda x: '品牌词' if isinstance(x,str) and '品牌' in x else '非品牌词')

def btot(df, lb):
    s = df[df['词类']==lb]
    sp = s['支出'].sum(); rg = s['注册人数'].sum()
    return dict(支出=jnum(sp), 展示次数=jnum(s['展示次数'].sum()),
        点击次数=jnum(s['点击次数'].sum()), 安装次数=jnum(s['安装次数'].sum()),
        激活数=jnum(s['激活数'].sum()), 注册人数=jnum(rg),
        总充值金额=jnum(s['总充值金额'].sum()),
        点击率=jnum(s['点击率'].mean()), 安装率=jnum(s['安装率'].mean()),
        激活率=jnum(s['激活率'].mean()), 注册率=jnum(s['注册率'].mean()),
        roi=jnum(rate(s['总充值金额'].sum(), sp)))

tot = dict(支出=jnum(m['支出'].sum()), 展示次数=jnum(m['展示次数'].sum()),
    点击次数=jnum(m['点击次数'].sum()), 安装次数=jnum(m['安装次数'].sum()),
    激活数=jnum(m['激活数'].sum()), 注册人数=jnum(m['注册人数'].sum()),
    总充值金额=jnum(m['总充值金额'].sum()),
    点击率=jnum(m['点击率'].mean()), 安装率=jnum(m['安装率'].mean()),
    激活率=jnum(m['激活率'].mean()), 注册率=jnum(m['注册率'].mean()),
    roi=jnum(rate(m['总充值金额'].sum(), m['支出'].sum())))

# daily
gr = m.groupby('df')
daily = []
for d, g in gr:
    t支出=jnum(g['支出'].sum()); t点击=jnum(g['点击次数'].sum())
    t展示=jnum(g['展示次数'].sum()); t安装=jnum(g['安装次数'].sum())
    t激活=jnum(g['激活数'].sum()); t注册=jnum(g['注册人数'].sum())
    t充值=jnum(g['总充值金额'].sum())
    daily.append(dict(date=d, 支出=t支出, 展示次数=t展示, 点击次数=t点击,
        安装次数=t安装, 激活数=t激活, 注册人数=t注册, 总充值金额=t充值,
        点击率=jnum(rate(t点击,t展示)), 安装率=jnum(rate(t安装,t点击)),
        激活率=jnum(rate(t激活,t安装)), 注册率=jnum(rate(t注册,t激活)),
        roi=jnum(rate(t充值,t支出))))
daily.sort(key=lambda x: x['date'])

# campaigns
cam = []
for _, r in m.iterrows():
    cam.append(dict(
        date=r['df'], 广告系列名称=r['cs'], 词类=r['词类'],
        支出=jnum(r['支出']), 展示次数=jnum(r['展示次数']),
        点击次数=jnum(r['点击次数']), 安装次数=jnum(r['安装次数']),
        激活数=jnum(r['激活数']), 注册人数=jnum(r['注册人数']),
        总充值金额=jnum(r['总充值金额']),
        点击率=jnum(r['点击率']), 安装率=jnum(r['安装率']),
        激活率=jnum(r['激活率']), 注册率=jnum(r['注册率']), roi=jnum(r['roi'])))

data = dict(total=tot, brand=btot(m,'品牌词'), nonbrand=btot(m,'非品牌词'),
            daily=daily, campaigns=cam)

JSON_OUT = '/Users/benny/Desktop/听脑ai/广告数据/asa后端数据/asa_backend_data.json'
with open(JSON_OUT,'w',encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"  JSON: {JSON_OUT} ({os.path.getsize(JSON_OUT)//1024} KB, {len(cam)} 条)")
print(f"  总支出 ¥{tot['支出']:,.2f} | 总注册 {tot['注册人数']:,.0f} | ROI {tot['roi']:.2f}")

# ══════════════════════════════════════════════════════════════
# STEP 2 — Write CSS
# ══════════════════════════════════════════════════════════════
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0d1117;color:#e6edf3;font-size:13px;min-height:100vh;padding:20px}
h1{font-size:18px;font-weight:600;color:#fff;margin-bottom:6px}
.sub{color:#71767b;font-size:12px;margin-bottom:20px}
.kpi-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px}
.kpi{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px}
.kpi .label{color:#71767b;font-size:11px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
.kpi .value{font-size:22px;font-weight:700;color:#fff}
.kpi .sub{margin:4px 0 0;font-size:11px;color:#71767b}
.kpi.blue  .value{color:#58a6ff}
.kpi.yellow.value{color:#d29922}
.kpi.green .value{color:#3fb950}
.kpi.red   .value{color:#f85149}
.charts{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px}
.chart-box{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px}
.chart-box h3{font-size:13px;color:#e6edf3;margin-bottom:12px;font-weight:600}
canvas{max-height:220px!important}
.brand-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px}
.brand-card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:18px}
.brand-card h3{font-size:13px;margin-bottom:14px;font-weight:600}
.brand-card.brand h3{color:#3fb950}
.brand-card.nonbrand h3{color:#8b5cf6}
.brow{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #21262d;font-size:13px}
.brow:last-child{border:none}
.bl{color:#71767b}
.bv{font-weight:600}
.bv.g{color:#3fb950}
.bv.y{color:#d29922}
.toolbar{display:flex;align-items:center;gap:8px;margin-bottom:14px;flex-wrap:wrap}
.btn{background:#21262d;border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:5px 12px;font-size:12px;cursor:pointer;transition:all .15s}
.btn:hover{background:#30363d;border-color:#8b949e}
.btn.active{background:#238636;border-color:#238636;color:#fff}
.dp-wrap{position:relative;display:inline-block}
.dp-btn{background:#21262d;border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:5px 12px;font-size:12px;cursor:pointer;min-width:120px;text-align:left;display:inline-block}
.dp-btn::after{content:' \\25be';float:right}
.dp-drop{display:none;position:absolute;top:calc(100%+4px);left:0;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;z-index:200;min-width:300px;box-shadow:0 8px 24px rgba(0,0,0,.4)}
.dp-drop.open{display:block}
.dp-chips{display:flex;gap:6px;margin-bottom:10px}
.dp-chip{background:#21262d;border:1px solid #30363d;color:#c9d1d9;border-radius:4px;padding:3px 10px;font-size:11px;cursor:pointer;display:inline-block}
.dp-chip:hover,.dp-chip.sel{background:#238636;border-color:#238636;color:#fff}
.dates-grid{display:flex;flex-wrap:wrap;gap:5px;max-height:200px;overflow-y:auto;margin-bottom:10px}
.dcb{background:#21262d;border:1px solid #30363d;color:#c9d1d9;border-radius:4px;padding:4px 8px;font-size:11px;cursor:pointer;min-width:36px;text-align:center;display:inline-block}
.dcb:hover{background:#30363d}
.dcb.sel{background:#238636;border-color:#238636;color:#fff}
.dp-foot{display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#71767b;margin-top:10px;padding-top:10px;border-top:1px solid #2f3847}
.dp-foot button{background:#238636;border:none;color:#fff;border-radius:4px;padding:4px 12px;font-size:11px;cursor:pointer}
.dp-foot button.clr{background:#21262d;border:1px solid #30363d;color:#c9d1d9;margin-right:auto}
.dp-note{font-size:11px;color:#71767b;margin-left:8px;white-space:nowrap}
.dp-note.chosen{color:#3fb950}
.dp-wrap2{position:relative;display:inline-block;margin-left:auto}
.dp-btn2{background:#21262d;border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:5px 12px;font-size:12px;cursor:pointer;min-width:140px;text-align:left;display:inline-block}
.dp-btn2::after{content:' \\25be';float:right}
.dp-drop2{display:none;position:absolute;top:calc(100%+4px);right:0;background:#161b22;border:1px solid #30363d;border-radius:8px;padding:8px;z-index:200;min-width:160px;box-shadow:0 8px 24px rgba(0,0,0,.4)}
.dp-drop2.open{display:block}
.droption{padding:6px 10px;border-radius:4px;cursor:pointer;color:#c9d1d9;font-size:12px}
.droption:hover{background:#21262d}
.droption.sel{background:#238636;color:#fff}
.table-wrap{background:#161b22;border:1px solid #30363d;border-radius:10px;overflow:hidden;margin-bottom:20px}
.table-head{padding:12px 16px;border-bottom:1px solid #21262d;display:flex;align-items:center;gap:12px;font-size:12px;color:#71767b}
.table-head b{color:#3fb950}
.pg-wrap{padding:10px 16px;border-top:1px solid #21262d;display:flex;justify-content:space-between;align-items:center;font-size:12px;color:#71767b}
.pg-btn{background:#21262d;border:1px solid #30363d;color:#c9d1d9;border-radius:4px;padding:3px 10px;font-size:11px;cursor:pointer}
.pg-btn:disabled{opacity:.4;cursor:not-allowed}
table{width:100%;border-collapse:collapse;font-size:12px}
thead{background:#21262d;position:sticky;top:0;z-index:10}
tfoot{position:sticky;bottom:0;z-index:9}
th{padding:9px 10px;text-align:left;color:#71767b;font-weight:500;cursor:pointer;white-space:nowrap;user-select:none}
th:hover{color:#e6edf3}
th .si{margin-left:4px;opacity:.4;font-size:10px}
th .si.on{opacity:1;color:#3fb950}
td{padding:8px 10px;border-bottom:1px solid #21262d;color:#c9d1d9;white-space:nowrap}
tr:hover td{background:#1c2128}
.bdg{display:inline-block;border-radius:3px;padding:1px 6px;font-size:10px;font-weight:600}
.bdg.b{background:rgba(63,185,80,.15);color:#3fb950}
.bdg.nb{background:rgba(139,92,246,.15);color:#8b5cf6}
.num{text-align:right;font-variant-numeric:tabular-nums}
.loading{padding:40px;text-align:center;color:#71767b}
.kpi-section{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px;margin-bottom:20px}
.kpi-section-hd{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.kpi-section-title{font-size:14px;font-weight:600;color:#e6edf3}
.month-sel{background:#21262d;border:1px solid #30363d;color:#e6edf3;border-radius:6px;padding:4px 8px;font-size:12px;cursor:pointer;margin-left:4px}
.month-sel:focus{outline:none;border-color:#58a6ff}
.kpi-section-body{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.kpi-item{background:#21262d;border:1px solid #30363d;border-radius:8px;padding:14px}
.kpi-item .ki-label{font-size:11px;color:#71767b;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px}
.kpi-item .ki-row{display:flex;align-items:baseline;gap:6px;margin-bottom:6px}
.kpi-item .ki-current{font-size:20px;font-weight:700;color:#e6edf3}
.kpi-item .ki-target{font-size:12px;color:#71767b}
.kpi-item .ki-bar{height:6px;background:#30363d;border-radius:3px;overflow:hidden;margin-top:6px}
.kpi-item .ki-fill{height:100%;border-radius:3px;background:#238636;transition:width .3s}
.kpi-item .ki-fill.danger{background:#f85149}
.kpi-item .ki-fill.warning{background:#d29922}
.kpi-item .ki-pct{font-size:11px;color:#71767b;margin-top:4px}
.kpi-item .ki-pct.done{color:#3fb950;font-weight:600}
.kpi-item .ki-pct.danger{color:#f85149;font-weight:600}
.kpi-item .ki-pct.warning{color:#d29922;font-weight:600}
.kpi-modal{display:none;position:fixed;inset:0;z-index:1000;background:rgba(0,0,0,.6);align-items:center;justify-content:center}
.kpi-modal.open{display:flex}
.kpi-modal-box{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:24px;min-width:340px;max-width:480px;width:90%}
.kpi-modal-box h3{font-size:15px;color:#e6edf3;margin-bottom:16px;font-weight:600}
.kpi-modal-box .form-row{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.kpi-modal-box .form-row label{flex:0 0 100px;font-size:12px;color:#71767b}
.kpi-modal-box .form-row input{flex:1;background:#21262d;border:1px solid #30363d;color:#e6edf3;border-radius:6px;padding:6px 10px;font-size:13px}
.kpi-modal-box .form-row input:focus{outline:none;border-color:#58a6ff}
.kpi-modal-box .form-foot{display:flex;gap:8px;justify-content:flex-end;margin-top:16px}
.kpi-modal-box .btn-ok{background:#238636;border:none;color:#fff;border-radius:6px;padding:7px 18px;font-size:13px;cursor:pointer}
.kpi-modal-box .btn-cancel{background:#21262d;border:1px solid #30363d;color:#c9d1d9;border-radius:6px;padding:7px 18px;font-size:13px;cursor:pointer}
"""


# ══════════════════════════════════════════════════════════════
# STEP 3 — Write JavaScript (app.js)
# ══════════════════════════════════════════════════════════════
JS = r"""
(function(){
  var $ = document.getElementById.bind(document);
  var D = null, T, BR, NBR, DY, CAMS;
  var STATE = {filter:'all', dates:new Set(), sortCol:'\u652f\u51fa', sortAsc:false, page:1, PAGE_SIZE:50};
  var allDates = [];
  var lc0 = null, lc1 = null;
  var AVAIL_MONTHS = [];
  var SEL_MONTH = null;

  function n(v){ return v == null ? 0 : +v; }
  function fmt(v, d){
    if(v == null || isNaN(+v)) return '\u2014';
    return (+v).toLocaleString('en-US',{maximumFractionDigits:d||2});
  }
  function pct(v, d){ if(v == null || isNaN(+v)) return '\u2014'; return (v*100).toFixed(d||2)+'%'; }
  function cny(v){ if(v == null || isNaN(+v)) return '\u2014'; return '\u00a5'+(+v).toLocaleString('en-US',{maximumFractionDigits:2}); }
  function s(id,h){ $(id).innerHTML = h; }

  function rnd(v,d){ return Math.round(v*Math.pow(10,d))/Math.pow(10,d); }

  function renderKPIs(){
    s('k1', cny(T.\u652f\u51fa));
    s('k1s', '\u5c55\u793a '+fmt(T.\u5c55\u793a\u6b21\u6570,0)+' | \u70b9\u51fb '+fmt(T.\u70b9\u51fb\u6b21\u6570,0)+' | \u5b89\u88c5 '+fmt(T.\u5b89\u88c5\u6b21\u6570,0));
    s('k5', fmt(T.\u5b89\u88c5\u6b21\u6570,0));
    s('k5r', pct(T.\u5b89\u88c5\u7387));
    s('k2', fmt(T.\u6ce8\u518c\u4eba\u6570,0));
    s('k2r', pct(T.\u6ce8\u518c\u7387));
    s('k3', cny(T.\u603b\u5145\u503c\u91d1\u989d));
    s('k3r', pct(T.roi));
    var rc = T.\u652f\u51fa / n(T.\u6ce8\u518c\u4eba\u6570);
    s('k4', isFinite(rc) ? cny(rc) : '\u2014');
    var bc = n(BR.\u652f\u51fa)/n(BR.\u6ce8\u518c\u4eba\u6570);
    var nbc = n(NBR.\u652f\u51fa)/n(NBR.\u6ce8\u518c\u4eba\u6570);
    s('k4s', '\u54c1\u724c \u00a5'+(isFinite(bc)?bc.toFixed(2):'\u2014')+' | \u975e\u54c1\u724c \u00a5'+(isFinite(nbc)?nbc.toFixed(2):'\u2014'));
    var matched = CAMS.filter(function(c){ return n(c.\u6fc0\u6d3b\u6570)>0 || n(c.\u6ce8\u518c\u4eba\u6570)>0; }).length;
    s('mRate', matched+'/'+CAMS.length+' ('+(matched/CAMS.length*100).toFixed(1)+'%)');
    var ds = DY.map(function(d){return d.date;}).sort();
    s('dUntil', ds.length ? ds[ds.length-1] : '\u2014');
  }

  function renderBrand(){
    function cv(id,sp,reg,rr,roi){
      s(id+'sp', cny(sp));
      s(id+'reg', fmt(reg,0));
      var rc = n(sp)/n(reg);
      s(id+'rc', isFinite(rc) ? cny(rc) : '\u2014');
      s(id+'rr', pct(rr));
      s(id+'roi', isFinite(roi) ? roi.toFixed(3) : '\u2014');
    }
    var mk = getMonthKey();
    var monthCams = CAMS.filter(function(c){
      var m = '2026-' + c.date.split('-')[0];
      return m === mk;
    });
    var bSp=0, bReg=0, bRev=0, bAct=0, nbSp=0, nbReg=0, nbRev=0, nbAct=0;
    monthCams.forEach(function(c){
      if(c.\u8bcd\u7c7b === '\u54c1\u724c\u8bcd'){
        bSp  += n(c.\u652f\u51fa);
        bReg += n(c.\u6ce8\u518c\u4eba\u6570);
        bRev += n(c.\u603b\u5145\u503c\u91d1\u989d);
        bAct += n(c.\u6fc0\u6d3b\u6570);
      } else {
        nbSp  += n(c.\u652f\u51fa);
        nbReg += n(c.\u6ce8\u518c\u4eba\u6570);
        nbRev += n(c.\u603b\u5145\u503c\u91d1\u989d);
        nbAct += n(c.\u6fc0\u6d3b\u6570);
      }
    });
    cv('b',  bSp, bReg, bAct>0?bReg/bAct:0, bSp>0?bRev/bSp:0);
    cv('nb', nbSp, nbReg, nbAct>0?nbReg/nbAct:0, nbSp>0?nbRev/nbSp:0);
  }

  function renderCharts(){
    var lb = DY.map(function(d){return d.date;}).sort();
    var sp = DY.map(function(d){return rnd(d.\u652f\u51fa||0,2);});
    var rv = DY.map(function(d){return rnd(d.\u603b\u5145\u503c\u91d1\u989d||0,2);});
    var ctr= DY.map(function(d){return rnd((d.\u70b9\u51fb\u7387||0)*100,3);});
    var roi= DY.map(function(d){return rnd(d.roi||0,3);});
    var o = {responsive:true,interaction:{mode:'index',intersect:false},
      plugins:{legend:{labels:{color:'#71767b',font:{size:11}}}},
      scales:{x:{ticks:{color:'#71767b',font:{size:10}},grid:{color:'#21262d'}},
              y:{position:'left',ticks:{color:'#58a6ff',font:{size:10}},grid:{color:'#21262d'}},
              y1:{position:'right',ticks:{color:'#d29922',font:{size:10}},grid:{drawOnChartArea:false}}}};
    if(lc0){lc0.destroy();lc0=null;}
    if(lc1){lc1.destroy();lc1=null;}
    lc0 = new Chart($('c0'),{type:'line',
      data:{labels:lb,datasets:[
        {label:'\u652f\u51fa',data:sp,borderColor:'#58a6ff',backgroundColor:'rgba(88,166,255,0.1)',tension:0.3,yAxisID:'y'},
        {label:'\u5145\u503c',data:rv,borderColor:'#3fb950',backgroundColor:'rgba(63,185,80,0.1)',tension:0.3,yAxisID:'y1'}
      ]},options:o});
    lc1 = new Chart($('c1'),{type:'line',
      data:{labels:lb,datasets:[
        {label:'\u70b9\u51fb\u7387%',data:ctr,borderColor:'#f85149',backgroundColor:'rgba(248,81,73,0.1)',tension:0.3,yAxisID:'y'},
        {label:'ROI',data:roi,borderColor:'#d29922',backgroundColor:'rgba(210,153,34,0.1)',tension:0.3,yAxisID:'y1'}
      ]},options:o});
  }

  function renderDatesGrid(){
    var g = $('dGrid');
    g.innerHTML = allDates.map(function(d){
      return '<span class="dcb'+(STATE.dates.has(d)?' sel':'')+'" data-d="'+d+'">'+d+'</span>';
    }).join('');
    var n = STATE.dates.size;
    s('dNote', n===0 ? '\u5df2\u9009 0 \u5929' : '\u5df2\u9009 '+n+' \u5929');
  }

  function getFilt(){
    var r = CAMS;
    if(STATE.dates.size > 0)
      r = r.filter(function(c){ return STATE.dates.has(c.date); });
    if(STATE.filter === 'brand')
      r = r.filter(function(c){ return c.\u8bcd\u7c7b === '\u54c1\u724c\u8bcd'; });
    else if(STATE.filter === 'nonbrand')
      r = r.filter(function(c){ return c.\u8bcd\u7c7b === '\u975e\u54c1\u724c\u8bcd'; });
    else if(STATE.filter === 'month'){
      var dates30 = allDates.slice(-30);
      r = r.filter(function(c){ return dates30.indexOf(c.date) !== -1; });
    }
    else if(STATE.filter === '7d'){
      var d7 = allDates.slice(-7);
      r = r.filter(function(c){ return d7.indexOf(c.date) !== -1; });
    }
    return r;
  }

  function getSorted(r){
    var col = STATE.sortCol, asc = STATE.sortAsc;
    return r.slice().sort(function(a,b){
      var va=n(a[col]), vb=n(b[col]);
      return va===vb ? 0 : asc ? va-vb : vb-va;
    });
  }

  function renderTable(){
    var rows = getFilt();
    var sorted = getSorted(rows);
    var total = Math.ceil(sorted.length / STATE.PAGE_SIZE);
    if(STATE.page > total) STATE.page = Math.max(1,total);
    var start = (STATE.page-1)*STATE.PAGE_SIZE;
    var page = sorted.slice(start, start+STATE.PAGE_SIZE);

    s('camCount', sorted.length);
    s('pgInfo', STATE.page+' / '+Math.max(1,total)+' \u9875');

    document.querySelectorAll('th[data-col]').forEach(function(th){
      var si = th.querySelector('.si');
      if(STATE.sortCol === th.dataset.col){
        si.classList.add('on');
        si.textContent = STATE.sortAsc ? '\u2191' : '\u2193';
      } else {
        si.classList.remove('on');
        si.textContent = '\u2195';
      }
    });

    if(page.length === 0){
      $('camBody').innerHTML = '<tr><td colspan="17" style="text-align:center;padding:32px;color:#71767b">\u6682\u65e0\u6570\u636e</td></tr>';
      $('pgPrev').disabled = $('pgNext').disabled = true;
      s('pgLabel','');
      return;
    }

    // Compute totals from filtered+sorted (all filtered rows, not just page)
    var tSp=0, tIm=0, tCl=0, tIn=0, tAc=0, tRg=0, tRv=0;
    sorted.forEach(function(c){
      tSp+=n(c.\u652f\u51fa); tIm+=n(c.\u5c55\u793a\u6b21\u6570);
      tCl+=n(c.\u70b9\u51fb\u6b21\u6570); tIn+=n(c.\u5b89\u88c5\u6b21\u6570);
      tAc+=n(c.\u6fc0\u6d3b\u6570); tRg+=n(c.\u6ce8\u518c\u4eba\u6570); tRv+=n(c.\u603b\u5145\u503c\u91d1\u989d);
    });
    var tCTR=tIm>0?tCl/tIm:0, tIPR=tCl>0?tIn/tCl:0;
    var tACR=tIn>0?tAc/tIn:0, tRGR=tAc>0?tRg/tAc:0;
    var tROI=tSp>0?tRv/tSp:0;
    var tIC=tIn>0?tSp/tIn:0;
    var tRC=tRg>0?tSp/tRg:0;

    var totalRow = '<tr style="background:#1c2d1e;font-weight:700;color:#3fb950">'+
      '<td>\u5408\u8ba1</td>'+
      '<td>\u5171 '+sorted.length+' \u6761</td>'+
      '<td></td>'+
      '<td class="num" style="color:#3fb950">'+cny(tSp)+'</td>'+
      '<td class="num" style="color:#3fb950">'+fmt(tIm,0)+'</td>'+
      '<td class="num" style="color:#3fb950">'+fmt(tCl,0)+'</td>'+
      '<td class="num" style="color:#3fb950">'+fmt(tIn,0)+'</td>'+
      '<td class="num" style="color:#3fb950">'+fmt(tAc,0)+'</td>'+
      '<td class="num" style="color:#3fb950">'+fmt(tRg,0)+'</td>'+
      '<td class="num" style="color:#3fb950">'+cny(tRv)+'</td>'+
      '<td class="num" style="color:#3fb950">'+(tIC>0?cny(tIC):'\u2014')+'</td>'+
      '<td class="num" style="color:#3fb950">'+(tRC>0?cny(tRC):'\u2014')+'</td>'+
      '<td class="num" style="color:#3fb950">'+pct(tCTR)+'</td>'+
      '<td class="num" style="color:#3fb950">'+pct(tIPR)+'</td>'+
      '<td class="num" style="color:#3fb950">'+pct(tACR)+'</td>'+
      '<td class="num" style="color:#3fb950">'+pct(tRGR)+'</td>'+
      '<td class="num" style="color:'+(tROI>=1?'#3fb950':'#f85149')+'">'+tROI.toFixed(3)+'</td>'+
    '</tr>';

    $('camBody').innerHTML = page.map(function(c){
      var roi = n(c.\u652f\u51fa)>0 ? n(c.\u603b\u5145\u503c\u91d1\u989d)/n(c.\u652f\u51fa) : 0;
      var roiColor = roi>=1 ? '#3fb950' : '#f85149';
      var badge = c.\u8bcd\u7c7b==='\u54c1\u724c\u8bcd'
        ? '<span class="bdg b">\u54c1\u724c</span>'
        : '<span class="bdg nb">\u975e\u54c1\u724c</span>';
      var ic = n(c.\u5b89\u88c5\u6b21\u6570)>0 ? n(c.\u652f\u51fa)/n(c.\u5b89\u88c5\u6b21\u6570) : 0;
      var rc = n(c.\u6ce8\u518c\u4eba\u6570)>0 ? n(c.\u652f\u51fa)/n(c.\u6ce8\u518c\u4eba\u6570) : 0;
      return '<tr>'+
        '<td>'+c.date+'</td>'+
        '<td style="max-width:200px;overflow:hidden;text-overflow:ellipsis">'+c.\u5e7f\u544a\u7cfb\u5217\u540d\u79f0+'</td>'+
        '<td>'+badge+'</td>'+
        '<td class="num">'+cny(c.\u652f\u51fa)+'</td>'+
        '<td class="num">'+fmt(c.\u5c55\u793a\u6b21\u6570,0)+'</td>'+
        '<td class="num">'+fmt(c.\u70b9\u51fb\u6b21\u6570,0)+'</td>'+
        '<td class="num">'+fmt(c.\u5b89\u88c5\u6b21\u6570,0)+'</td>'+
        '<td class="num">'+fmt(c.\u6fc0\u6d3b\u6570,0)+'</td>'+
        '<td class="num" style="color:#3fb950">'+fmt(c.\u6ce8\u518c\u4eba\u6570,0)+'</td>'+
        '<td class="num">'+cny(c.\u603b\u5145\u503c\u91d1\u989d)+'</td>'+
        '<td class="num">'+(ic>0?cny(ic):'\u2014')+'</td>'+
        '<td class="num">'+(rc>0?cny(rc):'\u2014')+'</td>'+
        '<td class="num">'+pct(c.\u70b9\u51fb\u7387)+'</td>'+
        '<td class="num">'+pct(c.\u5b89\u88c5\u7387)+'</td>'+
        '<td class="num">'+pct(c.\u6fc0\u6d3b\u7387)+'</td>'+
        '<td class="num">'+pct(c.\u6ce8\u518c\u7387)+'</td>'+
        '<td class="num" style="color:'+roiColor+'">'+roi.toFixed(3)+'</td>'+
      '</tr>';
    }).join('');

    $('camBody').innerHTML += totalRow;

    $('pgPrev').disabled = STATE.page <= 1;
    $('pgNext').disabled = STATE.page >= total;
    s('pgLabel','\u5171 '+sorted.length+' \u6761\uff0c\u6bcf\u9875 '+STATE.PAGE_SIZE+' \u6761');
  }

  function setFiltBtns(){
    document.querySelectorAll('[data-f]').forEach(function(b){
      b.classList.toggle('active', b.dataset.f === STATE.filter);
    });
    document.querySelectorAll('.dp-chip[data-qf]').forEach(function(c){
      c.classList.toggle('sel', c.dataset.qf === STATE.filter);
    });
  }

  function updSortBtn(){
    $('sortBtn').textContent = '\u6309'+STATE.sortCol+'\u6392\u5e8f \u25be';
    document.querySelectorAll('.droption').forEach(function(o){
      o.classList.toggle('sel', o.dataset.sort === STATE.sortCol);
    });
  }

  function render(){
    renderKPIs();
    renderBrand();
    renderDatesGrid();
    renderTable();
    setFiltBtns();
    updSortBtn();
    var tag = $('dateTag');
    if(STATE.dates.size === 0) tag.textContent = '';
    else if(STATE.dates.size === allDates.length) tag.textContent = '(\u5df2\u9009\u5168\u90e8\u65e5\u671f)';
    else tag.textContent = '(\u5df2\u9009 '+STATE.dates.size+' \u5929)';
  }

  function setSelMonth(v){
    SEL_MONTH = v === 'all' ? null : v;
    STATE.dates.clear();
    if(SEL_MONTH){
      CAMS.forEach(function(c){
        var m = '2026-' + c.date.split('-')[0];
        if(m === SEL_MONTH) STATE.dates.add(c.date);
      });
    }
    var labelMap = {};
    AVAIL_MONTHS.forEach(function(m){
      var parts = m.split('-');
      labelMap[m] = parseInt(parts[0]) === 2026 ? parts[1] + '\u6708' : m;
    });
    $('kpiMonthLabel').textContent = !SEL_MONTH ? '\u672c\u6708' : (labelMap[SEL_MONTH] || SEL_MONTH);
    STATE.page = 1;
    render();
    renderKPI();
  }

  function init(){
    T=D.total; BR=D.brand; NBR=D.nonbrand; DY=D.daily; CAMS=D.campaigns;
    var ds={};
    CAMS.forEach(function(c){ ds[c.date]=1; });
    allDates = Object.keys(ds).sort();

    // Discover available months from data
    var monthSet = {};
    CAMS.forEach(function(c){
      var parts = c.date.split('-');
      var m = '2026-' + parts[0];
      monthSet[m] = true;
    });
    AVAIL_MONTHS = Object.keys(monthSet).sort();
    var curMonth = new Date().getFullYear() + '-' + String(new Date().getMonth()+1).padStart(2,'0');
    if(AVAIL_MONTHS.indexOf(curMonth) === -1) curMonth = AVAIL_MONTHS[AVAIL_MONTHS.length - 1];
    var labelMap = {};
    AVAIL_MONTHS.forEach(function(m){
      var parts = m.split('-');
      labelMap[m] = parseInt(parts[0]) === 2026 ? parts[1] + '\u6708' : m;
    });
    $('monthSel').innerHTML = AVAIL_MONTHS.map(function(m){
      return '<option value="'+m+'"'+(m===curMonth?' selected':'')+'>'+labelMap[m]+'</option>';
    }).join('');
    $('monthSel').onchange = function(){ setSelMonth(this.value); };

    s('loadingMsg','');
    renderCharts();
    render();
    loadKPI();
    renderKPI();
  }

  // ── Monthly KPI ─────────────────────────────────────────────────────────────
  var MONTHLY = {};

  function getMonthKey(){
    if(SEL_MONTH) return SEL_MONTH;
    var now = new Date();
    var cur = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0');
    if(AVAIL_MONTHS.length && AVAIL_MONTHS.indexOf(cur) === -1){
      return AVAIL_MONTHS[AVAIL_MONTHS.length - 1];
    }
    return cur;
  }

  function loadKPI(){
    try {
      var stored = localStorage.getItem('asa_monthly_kpi');
      if(stored) MONTHLY = JSON.parse(stored);
    } catch(e){}
    var mk = getMonthKey();
    if(!MONTHLY[mk]){
      MONTHLY[mk] = {spend:0, reg:0, installs:0, nbReg:0, nbRegCost:0};
    }
  }

  function openKpiModal(){
    var mk = getMonthKey();
    var t = MONTHLY[mk] || {};
    $('kpiSpend').value = t.spend || '';
    $('kpiReg').value   = t.reg || '';
    $('kpiInstalls').value  = t.installs || '';
    $('kpiNbReg').value     = t.nbReg || '';
    $('kpiNbRegCost').value = t.nbRegCost || '';
    $('kpiModal').classList.add('open');
  }

  function saveKPI(){
    var mk = getMonthKey();
    MONTHLY[mk] = {
      spend: parseFloat($('kpiSpend').value) || 0,
      reg:   parseFloat($('kpiReg').value)   || 0,
      installs:  parseFloat($('kpiInstalls').value)  || 0,
      nbReg:     parseFloat($('kpiNbReg').value)     || 0,
      nbRegCost: parseFloat($('kpiNbRegCost').value) || 0,
    };
    try { localStorage.setItem('asa_monthly_kpi', JSON.stringify(MONTHLY)); } catch(e){}
    $('kpiModal').classList.remove('open');
    renderKPI();
  }

  function renderKPI(){
    var mk = getMonthKey();
    var t = MONTHLY[mk] || {spend:0,reg:0,installs:0,nbReg:0,nbRegCost:0};

    // Compute brand/nonbrand from filtered campaigns
    var filtCams = getFilt();
    var nbSp=0, nbReg=0, totalInstalls=0;
    filtCams.forEach(function(c){
      totalInstalls += n(c.\u5b89\u88c5\u6b21\u6570);
      if(c.\u8bcd\u7c7b === '\u54c1\u724c\u8bcd'){
        // brand — not tracked in KPI items
      } else {
        nbSp  += n(c.\u652f\u51fa);
        nbReg += n(c.\u6ce8\u518c\u4eba\u6570);
      }
    });
    var nbRegCost = nbReg > 0 ? nbSp / nbReg : 0;

    var now = new Date();
    var y = now.getFullYear(), m = now.getMonth();
    var daysInMonth = new Date(y,m+1,0).getDate();
    var dayOfMonth = now.getDate();
    var remaining = daysInMonth - dayOfMonth;

    var items = [
      {label:'\u652f\u51fa',       unit:'\u00a5', actual:filtCams.reduce(function(s,c){return s+n(c.\u652f\u51fa);},0),                         target:t.spend,     fmt:'cny'},
      {label:'\u6ce8\u518c\u4eba\u6570', unit:'\u4eba', actual:filtCams.reduce(function(s,c){return s+n(c.\u6ce8\u518c\u4eba\u6570);},0),             target:t.reg,       fmt:'int'},
      {label:'\u603b\u5b89\u88c5\u91cf', unit:'\u6b21', actual:totalInstalls,                                                             target:t.installs,  fmt:'int'},
      {label:'\u975e\u54c1\u724c\u6ce8\u518c', unit:'\u4eba', actual:nbReg,                                                               target:t.nbReg,     fmt:'int'},
      {label:'\u975e\u54c1\u724c\u6ce8\u518c\u6210\u672c', unit:'\u00a5', actual:nbRegCost,                                                      target:t.nbRegCost, fmt:'cny'},
    ];

    $('kpiBody').innerHTML = items.map(function(item){
      var actual = item.fmt==='cny' ? cny(item.actual) : (item.fmt==='int' ? fmt(item.actual,0) : item.actual.toFixed(3));
      var pct = 0, pctTxt = '\u2014', fillCls = '', barWidth = '0%';
      if(item.target > 0){
        pct = Math.min(100, item.actual/item.target*100);
        pctTxt = pct.toFixed(1)+'%';
        barWidth = pct.toFixed(1)+'%';
        fillCls = pct >= 100 ? '' : (pct >= 70 ? ' warning' : ' danger');
      } else {
        barWidth = '0%';
      }
      var targetTxt = item.target > 0
        ? ' / ' + (item.fmt==='cny' ? cny(item.target) : (item.fmt==='int' ? fmt(item.target,0) : item.target.toFixed(3)))
        : ' (\u672a\u8bbe\u5b9a\u76ee\u6807)';
      var pctCls = pct >= 100 ? ' done' : (pct >= 70 ? ' warning' : ' danger');
      var note = '';
      if(item.target > 0 && pct < 100 && remaining > 0){
        var dailyNeeded = (item.target - item.actual) / remaining;
        if(dailyNeeded > 0){
          note = '\u6bcf\u65e5\u9700 ' + (item.fmt==='cny' ? cny(dailyNeeded) : (item.fmt==='int' ? fmt(dailyNeeded,0) : dailyNeeded.toFixed(2)));
        }
      } else if(pct >= 100) {
        note = '\u2705 \u5df2\u5b8c\u6210';
      }
      return '<div class="kpi-item">'+
        '<div class="ki-label">'+(item.label+' TARGET')+'</div>'+
        '<div class="ki-row">'+
          '<span class="ki-current">'+actual+'</span>'+
          '<span class="ki-target">'+targetTxt+'</span>'+
        '</div>'+
        '<div class="ki-bar"><div class="ki-fill'+fillCls+'" style="width:'+barWidth+'"></div></div>'+
        '<div class="ki-pct'+pctCls+'">'+pctTxt+' '+note+'</div>'+
      '</div>';
    }).join('');
  }

  // Edit modal
  $('editKpiBtn').onclick = openKpiModal;
  $('kpiCancelBtn').onclick = function(){ $('kpiModal').classList.remove('open'); };
  $('kpiSaveBtn').onclick = saveKPI;
  $('kpiModal').addEventListener('click', function(e){
    if(e.target === $('kpiModal')) $('kpiModal').classList.remove('open');
  });

  document.addEventListener('click', function(e){
    var t = e.target;

    var btn = t.closest('[data-f]');
    if(btn){
      var f = btn.dataset.f;
      STATE.filter = f;
      if(f === 'brand' || f === 'nonbrand'){
        if(SEL_MONTH){
          STATE.dates.clear();
          CAMS.forEach(function(c){
            if('2026-'+c.date.split('-')[0] === SEL_MONTH) STATE.dates.add(c.date);
          });
        } else {
          STATE.dates.clear();
        }
      } else {
        STATE.dates.clear();
      }
      STATE.page = 1;
      render();
      renderKPI();
      return;
    }

    var chip = t.closest('.dp-chip[data-qf]');
    if(chip){
      if(chip.dataset.qf === 'clear') STATE.dates.clear();
      else {
        STATE.filter = chip.dataset.qf;
        if((chip.dataset.qf === 'brand' || chip.dataset.qf === 'nonbrand') && SEL_MONTH){
          STATE.dates.clear();
          CAMS.forEach(function(c){
            if('2026-'+c.date.split('-')[0] === SEL_MONTH) STATE.dates.add(c.date);
          });
        } else {
          STATE.dates.clear();
        }
      }
      render(); renderKPI(); return;
    }

    var dcb = t.closest('.dcb[data-d]');
    if(dcb){
      var d = dcb.dataset.d;
      if(STATE.dates.has(d)) STATE.dates.delete(d);
      else STATE.dates.add(d);
      renderDatesGrid();
      STATE.page = 1;
      render();
      renderKPI();
      return;
    }

    if(t.id === 'dpOk'){ $('dpDrop').classList.remove('open'); STATE.filter='all'; STATE.page=1; render(); renderKPI(); return; }
    if(t.id === 'dpClr'){ STATE.dates.clear(); renderDatesGrid(); render(); renderKPI(); return; }

    var th = t.closest('th[data-col]');
    if(th){
      var col = th.dataset.col;
      if(STATE.sortCol === col) STATE.sortAsc = !STATE.sortAsc;
      else { STATE.sortCol = col; STATE.sortAsc = false; }
      STATE.page = 1; renderTable(); updSortBtn(); return;
    }

    if(t.id === 'pgPrev'){ STATE.page = Math.max(1,STATE.page-1); renderTable(); return; }
    if(t.id === 'pgNext'){ STATE.page++; renderTable(); return; }

    if(t.id === 'dpBtn'){
      var was = $('dpDrop').classList.contains('open');
      document.querySelectorAll('.dp-drop,.dp-drop2').forEach(function(d){d.classList.remove('open');});
      if(!was) $('dpDrop').classList.add('open');
      return;
    }
    if(t.id === 'sortBtn'){
      var was = $('sortDrop').classList.contains('open');
      document.querySelectorAll('.dp-drop,.dp-drop2').forEach(function(d){d.classList.remove('open');});
      if(!was) $('sortDrop').classList.add('open');
      return;
    }
    var opt = t.closest('.droption[data-sort]');
    if(opt){
      STATE.sortCol = opt.dataset.sort; STATE.sortAsc = false; STATE.page = 1;
      $('sortDrop').classList.remove('open'); renderTable(); updSortBtn(); return;
    }
    if(t.id === 'expBtn'){
      var rows = getSorted(getFilt());
      var hdr = ['\u65e5\u671f','\u5e7f\u544a\u7cfb\u5217','\u8bcd\u7c7b','\u652f\u51fa','\u5c55\u793a','\u70b9\u51fb','\u5b89\u88c5','\u6fc0\u6d3b','\u6ce8\u518c','\u5145\u503c','\u5b89\u88c5\u6210\u672c','\u6ce8\u518c\u6210\u672c','\u70b9\u51fb\u7387','\u5b89\u88c5\u7387','\u6fc0\u6d3b\u7387','\u6ce8\u518c\u7387','ROI'];
      var csv = [hdr.join(',')];
      rows.forEach(function(r){
        var roi = n(r.\u652f\u51fa)>0 ? n(r.\u603b\u5145\u503c\u91d1\u989d)/n(r.\u652f\u51fa) : 0;
        var ic = n(r.\u5b89\u88c5\u6b21\u6570)>0 ? n(r.\u652f\u51fa)/n(r.\u5b89\u88c5\u6b21\u6570) : 0;
        var rc = n(r.\u6ce8\u518c\u4eba\u6570)>0 ? n(r.\u652f\u51fa)/n(r.\u6ce8\u518c\u4eba\u6570) : 0;
        csv.push([r.date,'"'+r.\u5e7f\u544a\u7cfb\u5217\u540d\u79f0+'"',r.\u8bcd\u7c7b,r.\u652f\u51fa,r.\u5c55\u793a\u6b21\u6570,r.\u70b9\u51fb\u6b21\u6570,r.\u5b89\u88c5\u6b21\u6570,r.\u6fc0\u6d3b\u6570,r.\u6ce8\u518c\u4eba\u6570,r.\u603b\u5145\u503c\u91d1\u989d,ic>0?ic.toFixed(2):'',rc>0?rc.toFixed(2):'',r.\u70b9\u51fb\u7387,r.\u5b89\u88c5\u7387,r.\u6fc0\u6d3b\u7387,r.\u6ce8\u518c\u7387,roi.toFixed(4)].join(','));
      });
      var blob = new Blob(['\ufeff'+csv.join('\n')],{type:'text/csv;charset=utf-8'});
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'asa_campaigns.csv';
      a.click();
      return;
    }

    if(!t.closest('.dp-wrap') && !t.closest('.dp-wrap2')){
      document.querySelectorAll('.dp-drop,.dp-drop2').forEach(function(d){d.classList.remove('open');});
    }
  });

  fetch('asa_backend_data.json').then(function(r){return r.json();})
    .then(function(json){ D=json; init(); })
    .catch(function(e){ console.error(e); s('loadingMsg','\u6570\u636e\u52a0\u8f7d\u5931\u8d25'); });

})();
"""

# ══════════════════════════════════════════════════════════════
# STEP 4 — Write all files
# ══════════════════════════════════════════════════════════════
print("\nStep 2: 生成 CSS / JS / HTML ...")
OUT_DIR = '/Users/benny/Desktop/听脑ai/广告数据/asa后端数据/'
CSS_OUT  = OUT_DIR + 'style.css'
JS_OUT   = OUT_DIR + 'app.js'
HTML_OUT = OUT_DIR + 'index.html'

with open(CSS_OUT,'w',encoding='utf-8') as f:
    f.write(CSS.strip())
print(f"  CSS: {CSS_OUT}")

with open(JS_OUT,'w',encoding='utf-8') as f:
    f.write(JS)
print(f"  JS:  {JS_OUT}")

# Build HTML — use string concatenation to avoid </script> in Python strings
# Split the closing script tag: '</scr' + 'ipt>' prevents HTML parser from seeing it
HTML = (
    '<!DOCTYPE html>\n'
    '<html lang="zh">\n'
    '<head>\n'
    '<meta charset="UTF-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
    '<title>ASA \u5e7f\u544a\u540e\u7aef\u5206\u6790\u770b\u677f</title>\n'
    '<link rel="stylesheet" href="style.css">\n'
    '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>\n'
    '</head>\n'
    '<body>\n'
    '<h1>ASA \u5e7f\u544a\u540e\u7aef\u5206\u6790\u770b\u677f</h1>\n'
    '<p class="sub">\u5339\u914d\u7387: <span id="mRate">\u2014</span> &nbsp;|&nbsp; \u6570\u636e\u622a\u4e8e: <span id="dUntil">\u2014</span> (\u540e\u7aef\u6570\u636e\u53ef\u80fd\u67091~2\u5929\u5ef6\u8fdf)</p>\n'
    '\n'
    '  <div class="kpi-section">\n'+
    '    <div class="kpi-section-hd">\n'+
    '      <span class="kpi-section-title">\ud83d\udcca <span id="kpiMonthLabel">\u672c\u6708</span> KPI \u76ee\u6807</span>\n'+
    '      <select id="monthSel" class="month-sel"></select>\n'+
    '      <button class="btn" id="editKpiBtn">\u7f16\u8f91\u76ee\u6807</button>\n'+
    '    </div>\n'+
    '    <div class="kpi-section-body" id="kpiBody"></div>\n'+
    '  </div>\n'
    '\n'
    '<div class="kpi-grid">\n'
    '  <div class="kpi">\n'
    '    <div class="label">\u603b\u652f\u51fa</div>\n'
    '    <div class="value" id="k1">\u2014</div>\n'
    '    <div class="sub" id="k1s"></div>\n'
    '  </div>\n'
    '  <div class="kpi green">\n'
    '    <div class="label">\u603b\u5b89\u88c5\u91cf</div>\n'
    '    <div class="value" id="k5">\u2014</div>\n'
    '    <div class="sub">\u5b89\u88c5\u7387 <span id="k5r">\u2014</span></div>\n'
    '  </div>\n'
    '  <div class="kpi blue">\n'
    '    <div class="label">\u6ce8\u518c\u4eba\u6570</div>\n'
    '    <div class="value" id="k2">\u2014</div>\n'
    '    <div class="sub">\u6ce8\u518c\u7387 <span id="k2r">\u2014</span></div>\n'
    '  </div>\n'
    '  <div class="kpi yellow">\n'
    '    <div class="label">\u603b\u5145\u503c</div>\n'
    '    <div class="value" id="k3">\u2014</div>\n'
    '    <div class="sub">\u5145\u503c ROI <span id="k3r">\u2014</span></div>\n'
    '  </div>\n'
    '  <div class="kpi red">\n'
    '    <div class="label">\u6ce8\u518c\u6210\u672c</div>\n'
    '    <div class="value" id="k4">\u2014</div>\n'
    '    <div class="sub" id="k4s"></div>\n'
    '  </div>\n'
    '</div>\n'
    '\n'
    '<div class="charts">\n'
    '  <div class="chart-box"><h3>\ud83d\udcc8 \u652f\u51fa\u4e0e\u5145\u503c\u8d8b\u52bf</h3><canvas id="c0"></canvas></div>\n'
    '  <div class="chart-box"><h3>\ud83d\udcc9 \u70b9\u51fb\u7387\u4e0e ROI \u8d8b\u52bf</h3><canvas id="c1"></canvas></div>\n'
    '</div>\n'
    '\n'
    '<div class="brand-row">\n'
    '  <div class="brand-card brand">\n'
    '    <h3>\ud83c\udf3f \u54c1\u724c\u8bcd</h3>\n'
    '    <div class="brow"><span class="bl">\u652f\u51fa</span><span class="bv" id="bsp">\u2014</span></div>\n'
    '    <div class="brow"><span class="bl">\u6ce8\u518c\u4eba\u6570</span><span class="bv g" id="breg">\u2014</span></div>\n'
    '    <div class="brow"><span class="bl">\u6ce8\u518c\u6210\u672c</span><span class="bv y" id="brc">\u2014</span></div>\n'
    '    <div class="brow"><span class="bl">\u6ce8\u518c\u7387</span><span class="bv" id="brr">\u2014</span></div>\n'
    '    <div class="brow"><span class="bl">\u5145\u503c ROI</span><span class="bv g" id="broi">\u2014</span></div>\n'
    '  </div>\n'
    '  <div class="brand-card nonbrand">\n'
    '    <h3>\ud83d\udd0d \u975e\u54c1\u724c\u8bcd</h3>\n'
    '    <div class="brow"><span class="bl">\u652f\u51fa</span><span class="bv" id="nbsp">\u2014</span></div>\n'
    '    <div class="brow"><span class="bl">\u6ce8\u518c\u4eba\u6570</span><span class="bv g" id="nbreg">\u2014</span></div>\n'
    '    <div class="brow"><span class="bl">\u6ce8\u518c\u6210\u672c</span><span class="bv y" id="nbrc">\u2014</span></div>\n'
    '    <div class="brow"><span class="bl">\u6ce8\u518c\u7387</span><span class="bv" id="nbrr">\u2014</span></div>\n'
    '    <div class="brow"><span class="bl">\u5145\u503c ROI</span><span class="bv g" id="nbroi">\u2014</span></div>\n'
    '  </div>\n'
    '</div>\n'
    '\n'
    '<div class="toolbar">\n'
    '  <button class="btn active" data-f="all">\u5168\u90e8</button>\n'
    '  <button class="btn" data-f="7d">\u8fd17\u5929</button>\n'
    '  <button class="btn" data-f="month">\u672c\u6708</button>\n'
    '  <button class="btn" data-f="brand">\u54c1\u724c\u8bcd</button>\n'
    '  <button class="btn" data-f="nonbrand">\u975e\u54c1\u724c\u8bcd</button>\n'
    '  <div class="dp-wrap">\n'
    '    <button class="dp-btn" id="dpBtn">\u9009\u62e9\u65e5\u671f \u25be</button>\n'
    '    <div class="dp-drop" id="dpDrop">\n'
    '      <div class="dp-chips">\n'
    '        <span class="dp-chip" data-qf="all">\u5168\u90e8</span>\n'
    '        <span class="dp-chip" data-qf="7d">\u8fd17\u5929</span>\n'
    '        <span class="dp-chip" data-qf="month">\u672c\u6708</span>\n'
    '        <span class="dp-chip" data-qf="clear">\u6e05\u9664</span>\n'
    '      </div>\n'
    '      <div class="dates-grid" id="dGrid"></div>\n'
    '      <div class="dp-foot">\n'
    '        <button class="clr" id="dpClr">\u6e05\u9664</button>\n'
    '        <span class="dp-note chosen" id="dNote">\u5df2\u9009 0 \u5929</span>\n'
    '        <button id="dpOk">\u786e\u5b9a</button>\n'
    '      </div>\n'
    '    </div>\n'
    '  </div>\n'
    '  <span class="dp-note" id="dateTag"></span>\n'
    '  <div class="dp-wrap2">\n'
    '    <button class="dp-btn2" id="sortBtn">\u6309\u652f\u51fa\u6392\u5e8f \u25be</button>\n'
    '    <div class="dp-drop2" id="sortDrop">\n'
    '      <div class="droption sel" data-sort="\u652f\u51fa">\u6309\u652f\u51fa\u6392\u5e8f</div>\n'
    '      <div class="droption" data-sort="roi">\u6309 ROI \u6392\u5e8f</div>\n'
    '      <div class="droption" data-sort="\u6ce8\u518c\u4eba\u6570">\u6309\u6ce8\u518c\u6392\u5e8f</div>\n'
    '      <div class="droption" data-sort="\u6fc0\u6d3b\u6570">\u6309\u6fc0\u6d3b\u6392\u5e8f</div>\n'
    '      <div class="droption" data-sort="\u70b9\u51fb\u7387">\u6309\u70b9\u51fb\u7387\u6392\u5e8f</div>\n'
    '    </div>\n'
    '  </div>\n'
    '  <button class="btn" id="expBtn" style="margin-left:auto">\ud83d\udce5 \u5bfc\u51fa CSV</button>\n'
    '</div>\n'
    '\n'
    '<div class="table-wrap">\n'
    '  <div class="table-head">\n'
    '    <b>\u5e7f\u544a\u7cfb\u5217\u660e\u7ec6\uff08\u5171 <b id="camCount">\u2014</b> \u6761\uff09</b>\n'
    '    <span style="margin-left:12px;font-size:11px;color:#71767b">\u2705 \u5408\u8ba1\u884c\u7ed3\u5e03\u8868\u5e3d\u90e8</span>\n'
    '    <span style="margin-left:auto" id="pgInfo"></span>\n'
    '  </div>\n'
    '  <div id="loadingMsg" class="loading">\u6570\u636e\u52a0\u8f7d\u4e2d...</div>\n'
    '  <div style="overflow-x:auto;max-height:65vh;overflow-y:auto" id="tableScroll">\n'
    '    <table>\n'
    '      <thead>\n'
    '        <tr>\n'
    '          <th data-col="date">\u65e5\u671f <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u5e7f\u544a\u7cfb\u5217\u540d\u79f0">\u5e7f\u544a\u7cfb\u5217 <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u8bcd\u7c7b">\u8bcd\u7c7b <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u652f\u51fa">\u652f\u51fa <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u5c55\u793a\u6b21\u6570">\u5c55\u793a <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u70b9\u51fb\u6b21\u6570">\u70b9\u51fb <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u5b89\u88c5\u6b21\u6570">\u5b89\u88c5 <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u6fc0\u6d3b\u6570">\u6fc0\u6d3b <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u6ce8\u518c\u4eba\u6570">\u6ce8\u518c <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u603b\u5145\u503c\u91d1\u989d">\u5145\u503c <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u5b89\u88c5\u6210\u672c">\u5b89\u88c5\u6210\u672c <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u6ce8\u518c\u6210\u672c">\u6ce8\u518c\u6210\u672c <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u70b9\u51fb\u7387">\u70b9\u51fb\u7387 <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u5b89\u88c5\u7387">\u5b89\u88c5\u7387 <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u6fc0\u6d3b\u7387">\u6fc0\u6d3b\u7387 <span class="si">\u2195</span></th>\n'
    '          <th data-col="\u6ce8\u518c\u7387">\u6ce8\u518c\u7387 <span class="si">\u2195</span></th>\n'
    '          <th data-col="roi">ROI <span class="si">\u2195</span></th>\n'
    '        </tr>\n'
    '      </thead>\n'
    '      <tbody id="camBody"></tbody>\n'
    '    </table>\n'
    '  </div>\n'
    '  <div class="pg-wrap">\n'
    '    <div>\n'
    '      <button class="pg-btn" id="pgPrev">\u25c0 \u4e0a\u4e00\u9875</button>\n'
    '      <button class="pg-btn" id="pgNext">\u4e0b\u4e00\u9875 \u25b6</button>\n'
    '    </div>\n'
    '    <span id="pgLabel"></span>\n'
    '  </div>\n'
    '</div>\n'
    '\n'
    '  <div class="kpi-modal" id="kpiModal">\n'
    '    <div class="kpi-modal-box">\n'
    '      <h3>\ud83d\udcab KPI \u76ee\u6807\u8bbe\u7f6e</h3>\n'
    '      <div class="form-row"><label>\u652f\u51fa\u76ee\u6807\uff08\uffe5\uff09</label><input type="number" id="kpiSpend" placeholder="\u8f93\u5165\u652f\u51fa\u76ee\u6807"></div>\n'
    '      <div class="form-row"><label>\u6ce8\u518c\u4eba\u6570\u76ee\u6807</label><input type="number" id="kpiReg" placeholder="\u8f93\u5165\u6ce8\u518c\u4eba\u6570\u76ee\u6807"></div>\n'
    '      <div class="form-row"><label>\u603b\u5b89\u88c5\u91cf\u76ee\u6807</label><input type="number" id="kpiInstalls" placeholder="\u8f93\u5165\u5b89\u88c5\u91cf\u76ee\u6807"></div>\n'
    '      <div class="form-row"><label>\u975e\u54c1\u724c\u6ce8\u518c\u76ee\u6807</label><input type="number" id="kpiNbReg" placeholder="\u8f93\u5165\u975e\u54c1\u724c\u6ce8\u518c\u4eba\u6570"></div>\n'
    '      <div class="form-row"><label>\u975e\u54c1\u724c\u6ce8\u518c\u6210\u672c</label><input type="number" id="kpiNbRegCost" placeholder="\u8f93\u5165\u76ee\u6807\u503c\uff08\uffe5\uff09"></div>\n'
    '      <div class="form-foot">\n'
    '        <button class="btn-cancel" id="kpiCancelBtn">\u53d6\u6d88</button>\n'
    '        <button class="btn-ok" id="kpiSaveBtn">\u4fdd\u5b58</button>\n'
    '      </div>\n'
    '    </div>\n'
    '  </div>\n'
    '\n'
    "  <script src=\"app.js\"><" + "/script>\n"
    "  </body>\n"
    "  </html>\n"
)

with open(HTML_OUT,'w',encoding='utf-8') as f:
    # Replace any lone surrogates with the actual character they represent
    def fix_surrogates(s):
        result = []
        i = 0
        while i < len(s):
            cp = ord(s[i])
            if 0xD800 <= cp <= 0xDBFF:  # high surrogate
                if i+1 < len(s) and 0xDC00 <= ord(s[i+1]) <= 0xDFFF:  # low surrogate
                    # Combine surrogates into a single character
                    combined = (cp - 0xD800) * 0x400 + (ord(s[i+1]) - 0xDC00) + 0x10000
                    result.append(chr(combined))
                    i += 2
                    continue
            result.append(s[i])
            i += 1
        return ''.join(result)
    f.write(fix_surrogates(HTML))

print(f"  HTML: {HTML_OUT} ({os.path.getsize(HTML_OUT)//1024} KB)")
print("\nDone!")
