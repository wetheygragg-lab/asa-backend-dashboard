
(function(){
  var $ = document.getElementById.bind(document);
  var D = null, T, BR, NBR, DY, CAMS;
  STATE = {filter:'all', dates:new Set(), sortCol:'\u652f\u51fa', sortAsc:false, page:1, PAGE_SIZE:50};
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

  // KPI/品牌卡片专用：永远返回当月全量数据，完全忽略任何品牌/非品牌/日期筛选
  function getKpiFilt(){
    return CAMS;
  }

  function renderKPIs(){
    var fc = getKpiFilt();
    var tSp=0, tImp=0, tClk=0, tIns=0, tReg=0, tRev=0;
    fc.forEach(function(c){
      tSp  += n(c.\u652f\u51fa);
      tImp += n(c.\u5c55\u793a\u6b21\u6570);
      tClk += n(c.\u70b9\u51fb\u6b21\u6570);
      tIns += n(c.\u5b89\u88c5\u6b21\u6570);
      tReg += n(c.\u6ce8\u518c\u4eba\u6570);
      tRev += n(c.\u603b\u5145\u503c\u91d1\u989d);
    });
    s('k1', cny(tSp));
    s('k1s', '\u5c55\u793a '+fmt(tImp,0)+' | \u70b9\u51fb '+fmt(tClk,0)+' | \u5b89\u88c5 '+fmt(tIns,0));
    s('k5', fmt(tIns,0));
    s('k5r', pct(tIns/tImp));
    s('k2', fmt(tReg,0));
    s('k2r', pct(tReg/tIns));
    s('k3', cny(tRev));
    s('k3r', pct(tSp>0?tRev/tSp:0));
    var rc = tReg>0 ? tSp/tReg : 0;
    s('k4', isFinite(rc) ? cny(rc) : '\u2014');
    // brand/nonbrand from filtered
    var bSp=0,bReg=0,nbSp=0,nbReg=0;
    fc.forEach(function(c){
      if(c.\u8bcd\u7c7b==='\u54c1\u724c\u8bcd'){ bSp+=n(c.\u652f\u51fa); bReg+=n(c.\u6ce8\u518c\u4eba\u6570); }
      else { nbSp+=n(c.\u652f\u51fa); nbReg+=n(c.\u6ce8\u518c\u4eba\u6570); }
    });
    var bc = bReg>0 ? bSp/bReg : 0, nbc = nbReg>0 ? nbSp/nbReg : 0;
    s('k4s', '\u54c1\u724c \u00a5'+(isFinite(bc)?bc.toFixed(2):'\u2014')+' | \u975e\u54c1\u724c \u00a5'+(isFinite(nbc)?nbc.toFixed(2):'\u2014'));
    var matched = fc.filter(function(c){ return n(c.\u6fc0\u6d3b\u6570)>0 || n(c.\u6ce8\u518c\u4eba\u6570)>0; }).length;
    s('mRate', matched+'/'+fc.length+' ('+(matched/fc.length*100).toFixed(1)+'%)');
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
    var fc = getKpiFilt();
    var bSp=0, bReg=0, bRev=0, bAct=0, nbSp=0, nbReg=0, nbRev=0, nbAct=0;
    fc.forEach(function(c){
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
    return now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0');
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

    // Compute brand/nonbrand from KPI-filtered campaigns (NOT date-filtered)
    var filtCams = getKpiFilt();
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

    if(t.id === 'dpOk'){ $('dpDrop').classList.remove('open'); STATE.page=1; render(); renderKPI(); return; }
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
