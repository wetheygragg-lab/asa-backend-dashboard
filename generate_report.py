#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ASA后端数据 -> asa_report_data.json

INNER JOIN on (date_norm, 广告系列名称, 渠道)
brand = '品牌' in 广告系列名称
ratios: CTR=点击/展示, IPR=安装/点击, ACR=激活/安装, RGR=注册/激活, ROI=充值/支出
"""
import json, os, pandas as pd

FILE = '/Users/benny/Desktop/听脑ai/广告数据/asa后端数据/asa广告后端分析.xlsx'
JSON_OUT = '/Users/benny/Desktop/听脑ai/广告数据/asa后端数据/asa_report_data.json'

# ── 1. Load Excel ──────────────────────────────────────────────────────────────
ad = pd.read_excel(FILE, sheet_name='广告端数据')
be = pd.read_excel(FILE, sheet_name='后端数据')

# ── 2. Normalise date keys ────────────────────────────────────────────────────
#  广告端: 日期 like '2026/05/01'  -> 'MM-DD'
#  后端: row_id like '2026-05-01 周五' -> 'MM-DD'
ad['date_norm'] = ad['日期'].apply(
    lambda x: x[5:7] + '-' + x[8:10] if isinstance(x, str) and len(x) >= 10 else '')
be['date_norm'] = be['row_id'].apply(
    lambda x: x[5:7] + '-' + x[8:10] if isinstance(x, str) and len(x) >= 10 else '')

# ── 3. Prepare backend lookup (INNER JOIN keys: date_norm, 广告系列名称, 渠道) ─
be_grp = be.groupby(['date_norm', '广告系列名称', '渠道']).agg(
    激活数=('激活数', 'sum'),
    注册人数=('注册人数', 'sum'),
    总充值金额=('总充值金额', 'sum'),
    新用户充值金额=('新用户充值金额', 'sum'),
    新用户充值人数=('新用户充值人数', 'sum'),
).reset_index()

# ── 4. INNER JOIN ─────────────────────────────────────────────────────────────
# After merge, overlapping columns get _x (ad) / _y (backend) suffixes.
# Keep ad spend/impressions/clicks/installs; use backend for activation/revenue.
m = ad.merge(be_grp, on=['date_norm', '广告系列名称', '渠道'], how='inner')

# Drop ad's own columns that overlap with backend data (use backend's instead)
cols_to_drop = [c for c in m.columns if c.endswith('_x') and c.replace('_x', '_y') in m.columns]
m = m.drop(columns=cols_to_drop)
m = m.rename(columns={c: c.replace('_y', '') for c in m.columns if c.endswith('_y')})

# Numeric coercions
for c in ['支出', '展示次数', '点击次数', '安装次数（总计）', '激活数', '注册人数',
          '总充值金额', '新用户充值金额', '新用户充值人数']:
    m[c] = pd.to_numeric(m[c], errors='coerce').fillna(0)

# Rename for clarity
m = m.rename(columns={'安装次数（总计）': '安装次数'})

# ── 5. Brand classification ────────────────────────────────────────────────────
m['词类'] = m['广告系列名称'].apply(
    lambda x: '品牌词' if '品牌' in str(x) else '非品牌词')

# ── 6. Ratio helpers ──────────────────────────────────────────────────────────
def rate(a, b):
    try:
        return float(a) / float(b) if float(b) != 0 else 0.0
    except (TypeError, ValueError):
        return 0.0

def jnum(v):
    """JSON-safe number: NaN / inf -> 0"""
    try:
        f = float(v)
        return 0.0 if (f != f or abs(f) == float('inf')) else f
    except (TypeError, ValueError):
        return 0.0

# ── 7. Row-level ratios ───────────────────────────────────────────────────────
m['点击率'] = [rate(r['点击次数'], r['展示次数']) for _, r in m.iterrows()]
m['安装率'] = [rate(r['安装次数'], r['点击次数']) for _, r in m.iterrows()]
m['激活率'] = [rate(r['激活数'], r['安装次数']) for _, r in m.iterrows()]
m['注册率'] = [rate(r['激活数'], r['注册人数']) for _, r in m.iterrows()]

# ── 8. Aggregation helper ─────────────────────────────────────────────────────
def agg_totals(df):
    s = df
    sp = jnum(s['支出'].sum())
    reg = jnum(s['注册人数'].sum())
    rev = jnum(s['总充值金额'].sum())
    new_rev = jnum(s['新用户充值金额'].sum())
    imp = jnum(s['展示次数'].sum())
    clk = jnum(s['点击次数'].sum())
    inst = jnum(s['安装次数'].sum())
    act = jnum(s['激活数'].sum())
    new_usr = jnum(s['新用户充值人数'].sum())

    return dict(
        支出=sp,
        展示次数=imp,
        点击次数=clk,
        安装次数=inst,
        激活数=act,
        注册人数=reg,
        总充值金额=rev,
        新用户充值金额=new_rev,
        点击率=jnum(rate(clk, imp)),
        安装率=jnum(rate(inst, clk)),
        激活率=jnum(rate(act, inst)),
        注册率=jnum(rate(act, reg)),
        ROI=jnum(rate(rev, sp)),
    )

# ── 9. Build total / brand / nonbrand ───────────────────────────────────────
tot     = agg_totals(m)
brand   = agg_totals(m[m['词类'] == '品牌词'])
nonbrand = agg_totals(m[m['词类'] == '非品牌词'])

# ── 10. Daily helpers ────────────────────────────────────────────────────────
def build_daily(daily_df):
    """Return list of daily dicts with abbreviated keys."""
    result = []
    for d, g in daily_df.groupby('date_norm'):
        sp  = jnum(g['支出'].sum())
        imp = jnum(g['展示次数'].sum())
        clk = jnum(g['点击次数'].sum())
        ins = jnum(g['安装次数'].sum())
        act = jnum(g['激活数'].sum())
        reg = jnum(g['注册人数'].sum())
        rev = jnum(g['总充值金额'].sum())
        nr  = jnum(g['新用户充值金额'].sum())

        ctr = jnum(rate(clk, imp))
        ipr = jnum(rate(ins, clk))
        acr = jnum(rate(act, ins))
        rgr = jnum(rate(act, reg))
        roi = jnum(rate(rev, sp))

        result.append(dict(
            d=d, spend=sp, imp=int(imp), clk=int(clk), inst=int(ins),
            act=int(act), reg=reg, rev=rev, newR=nr,
            roi=roi, ctr=ctr,
            # extra ratios (used in some downstream consumers)
            安装率=ipr, 激活率=acr, 注册率=rgr,
        ))
    result.sort(key=lambda x: x['d'])
    return result

# All daily (all channels, all campaigns)
daily = build_daily(m)

# Split by 词类
daily_brand = build_daily(m[m['词类'] == '品牌词'])
daily_nb    = build_daily(m[m['词类'] == '非品牌词'])

# Split by 渠道
daily_asa = build_daily(m[m['渠道'] == 'ASA'])
daily_hw  = build_daily(m[m['渠道'] == '华为'])

daily_asa_brand = build_daily(m[(m['渠道'] == 'ASA') & (m['词类'] == '品牌词')])
daily_asa_nb    = build_daily(m[(m['渠道'] == 'ASA') & (m['词类'] == '非品牌词')])
daily_hw_brand  = build_daily(m[(m['渠道'] == '华为') & (m['词类'] == '品牌词')])
daily_hw_nb     = build_daily(m[(m['渠道'] == '华为') & (m['词类'] == '非品牌词')])

# ── 11. Assemble output ───────────────────────────────────────────────────────
out = dict(
    total=tot,
    brand=brand,
    nonbrand=nonbrand,
    daily=daily,
    dailyBrand=daily_brand,
    dailyNb=daily_nb,
    dailyASA=daily_asa,
    dailyASA_brand=daily_asa_brand,
    dailyASA_nb=daily_asa_nb,
    dailyHW=daily_hw,
    dailyHW_brand=daily_hw_brand,
    dailyHW_nb=daily_hw_nb,
)

# ── 12. Write JSON ────────────────────────────────────────────────────────────
with open(JSON_OUT, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

sz = os.path.getsize(JSON_OUT) // 1024
print(f"Written: {JSON_OUT}  ({sz} KB)")
print(f"  matched rows : {len(m)}")
print(f"  brand rows   : {(m['词类']=='品牌词').sum()}")
print(f"  nonbrand rows: {(m['词类']=='非品牌词').sum()}")
print(f"  daily entries: {len(daily)}")
print()
print(f"  total 支出  : {tot['支出']:,.2f}")
print(f"  brand 支出   : {brand['支出']:,.2f}")
print(f"  nonbrand 支出: {nonbrand['支出']:,.2f}")
print(f"  total ROI    : {tot['ROI']:.4f}")
print(f"  brand ROI    : {brand['ROI']:.4f}")
print(f"  nonbrand ROI : {nonbrand['ROI']:.4f}")