import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Plane, Upload, Shuffle, Route, TicketPercent, Play, Pause, RotateCcw, Download, Sparkles, ArrowRight, CircleHelp, Wallet, Clock3, MapPin, CheckCircle2, AlertCircle } from 'lucide-react';
import { solveBudgetRoute, parseFlightsCsv, generateGraph, exportFlightsCsv } from './solver.js';
import './style.css';

const demo = { n: 6, k: 2, c: 2, flights: [
  { source: 1, destination: 2, price: 120 }, { source: 1, destination: 3, price: 100 },
  { source: 2, destination: 4, price: 70 }, { source: 3, destination: 4, price: 80 },
  { source: 3, destination: 5, price: 45 }, { source: 4, destination: 6, price: 90 },
  { source: 5, destination: 6, price: 110 }, { source: 2, destination: 5, price: 90 },
  { source: 1, destination: 4, price: 230 }, { source: 5, destination: 4, price: 25 }
] };

function App() {
  const [mode, setMode] = useState('manual');
  const [n, setN] = useState(demo.n);
  const [m, setM] = useState(demo.flights.length);
  const [k, setK] = useState(demo.k);
  const [c, setC] = useState(demo.c);
  const [rows, setRows] = useState(demo.flights.map(f => ({...f})));
  const [csvError, setCsvError] = useState('');
  const [error, setError] = useState('');
  const [seed, setSeed] = useState(42);
  const [reachable, setReachable] = useState(true);
  const [result, setResult] = useState(() => solveBudgetRoute(demo.n, demo.flights, demo.k, demo.c));
  const [solved, setSolved] = useState(true);
  const [animStep, setAnimStep] = useState(-1);
  const [paused, setPaused] = useState(false);
  const [running, setRunning] = useState(false);
  const timerRef = useRef(null);
  const fileRef = useRef(null);

  useEffect(() => {
    if (!running || paused) return;
    timerRef.current = setInterval(() => setAnimStep(s => {
      const next = s + 1;
      if (next >= (result?.pathFlights?.length || 0)) { clearInterval(timerRef.current); setRunning(false); return result?.pathFlights?.length || 0; }
      return next;
    }), 1000);
    return () => clearInterval(timerRef.current);
  }, [running, paused, result]);

  useEffect(() => () => clearInterval(timerRef.current), []);

  const pathFlights = result?.pathFlights || [];
  const activeFlight = running || animStep >= 0 ? pathFlights[Math.min(animStep, pathFlights.length - 1)] : null;
  const runningCost = pathFlights.slice(0, Math.max(0, animStep + 1)).reduce((sum, f) => sum + f.paidPrice, 0);
  const usedCoupons = pathFlights.slice(0, Math.max(0, animStep + 1)).filter(f => f.couponUsed).length;
  const visitedStops = Math.max(0, Math.min(animStep + 1, Math.max(0, pathFlights.length - 1)));

  function resetAnimation() {
    clearInterval(timerRef.current); setRunning(false); setPaused(false); setAnimStep(-1);
  }
  function solve() {
    setError('');
    const parsedN = Number(n), parsedK = Number(k), parsedC = Number(c);
    if (!Number.isInteger(parsedN) || parsedN < 1) return setError('Number of cities N must be a positive integer.');
    if (!Number.isInteger(parsedK) || parsedK < 0) return setError('K must be a non-negative integer.');
    if (!Number.isInteger(parsedC) || parsedC < 0) return setError('C must be a non-negative integer.');
    if (rows.some(f => !Number.isInteger(Number(f.source)) || !Number.isInteger(Number(f.destination)) || Number(f.source)<1 || Number(f.destination)<1 || Number(f.source)>parsedN || Number(f.destination)>parsedN || !Number.isSafeInteger(Number(f.price)) || Number(f.price)<0)) return setError('Every flight needs valid city IDs and a non-negative whole-number price.');
    const normalized = rows.map(f => ({source:Number(f.source), destination:Number(f.destination), price:Number(f.price)}));
    const solvedResult = solveBudgetRoute(parsedN, normalized, parsedK, parsedC);
    setN(parsedN); setRows(normalized); setM(normalized.length); setResult(solvedResult); setSolved(true); resetAnimation();
  }
  function addFlight() { setRows(r => [...r, {source:1, destination:Math.max(1, Number(n)), price:100}]); setM(Number(m)+1); }
  function updateFlight(i, key, value) { setRows(r => r.map((f,j) => i===j ? {...f,[key]:value} : f)); }
  function removeFlight(i) { setRows(r => r.filter((_,j)=>i!==j)); setM(Math.max(0, Number(m)-1)); }
  function makeRandom() {
    setError('');
    const nn = Number(n), mm = Number(m), kk = Number(k), cc = Number(c);
    if (!Number.isInteger(nn)||nn<1||nn>40) return setError('Random graph N must be between 1 and 40.');
    if (!Number.isInteger(mm)||mm<0||mm>500) return setError('M must be between 0 and 500.');
    if (!Number.isInteger(kk)||kk<0||!Number.isInteger(cc)||cc<0) return setError('K and C must be non-negative integers.');
    if (reachable && nn > 1 && mm < nn - 1) return setError(`To guarantee a route, M must be at least N - 1 (${nn - 1}) when reachability is enabled.`);
    const generated = generateGraph(nn, mm, Number(seed)||0, reachable);
    setRows(generated); setM(generated.length); setSolved(false); setResult(null); resetAnimation();
  }
  async function loadCsv(file) {
    setCsvError(''); setError('');
    try {
      const text = await file.text();
      const flights = parseFlightsCsv(text);
      const maxCity = flights.reduce((mx,f)=>Math.max(mx,f.source,f.destination), 1);
      setRows(flights); setN(maxCity); setM(flights.length); setSolved(false); setResult(null); resetAnimation();
    } catch (e) { setCsvError(e.message || 'Could not read CSV file.'); }
  }
  function downloadCsv() {
    const text = exportFlightsCsv(rows, result);
    const url = URL.createObjectURL(new Blob([text], {type:'text/csv;charset=utf-8;'}));
    const a = document.createElement('a'); a.href=url; a.download='budget-traveller-results.csv'; a.click(); URL.revokeObjectURL(url);
  }
  function startJourney() {
    if (!result?.reachable || !pathFlights.length) return;
    clearInterval(timerRef.current); setAnimStep(0); setPaused(false); setRunning(pathFlights.length > 1);
    if (pathFlights.length === 1) setRunning(false);
  }

  const graph = useMemo(() => {
    const width=760, height=360, cx=width/2, cy=height/2, radius=Math.min(width*.39,height*.39);
    const positions = Array.from({length:Number(n)||0},(_,i)=> {
      const angle = -Math.PI/2 + 2*Math.PI*i/Math.max(1,Number(n));
      return {id:i+1,x:cx+radius*Math.cos(angle),y:cy+radius*Math.sin(angle)};
    });
    return {width,height,positions};
  }, [n]);
  const pathEdgeSet = new Set(pathFlights.map(f => f.edgeIndex));
  const couponEdgeSet = new Set(pathFlights.filter(f=>f.couponUsed).map(f=>f.edgeIndex));
  const pathNodeSet = new Set(result?.path || []);
  const currentNode = animStep >= 0 && pathFlights.length ? pathFlights[Math.min(animStep, pathFlights.length-1)].destination : null;

  return <div className="app-shell">
    <header className="topbar">
      <div className="brand"><div className="brand-mark"><Plane size={22}/></div><div><div className="brand-title">Routewise</div><div className="brand-sub">BUDGET TRAVELLER</div></div></div>
      <div className="topbar-right"><span className="live-dot"/> Algorithm lab <span className="topbar-divider"/> <span className="avatar">BT</span></div>
    </header>
    <main className="main">
      <section className="hero">
        <div className="eyebrow"><Sparkles size={14}/> SMART ROUTE OPTIMIZER</div>
        <h1>Go farther.<br/><span>Spend less.</span></h1>
        <p>Find the cheapest flight path with stop limits and discount coupons. Then watch your journey unfold.</p>
        <div className="hero-pills"><span><Route size={14}/> Stop-aware routing</span><span><TicketPercent size={14}/> Smart coupon use</span><span><Clock3 size={14}/> Live journey replay</span></div>
      </section>

      <div className="section-heading"><div><span className="step-tag">01</span><h2>Plan your journey</h2></div><span className="muted">Configure your flight network</span></div>
      <section className="planner card">
        <div className="mode-tabs">
          <button className={mode==='manual'?'mode-tab active':'mode-tab'} onClick={()=>setMode('manual')}><Route size={16}/> Manual input</button>
          <button className={mode==='csv'?'mode-tab active':'mode-tab'} onClick={()=>setMode('csv')}><Upload size={16}/> CSV upload</button>
          <button className={mode==='random'?'mode-tab active':'mode-tab'} onClick={()=>setMode('random')}><Shuffle size={16}/> Random graph</button>
        </div>
        <div className="config-grid">
          <label className="field"><span>Number of cities (N)</span><input type="number" min="1" max="100" value={n} onChange={e=>setN(e.target.value)}/></label>
          <label className="field"><span>Maximum stops (K)</span><input type="number" min="0" value={k} onChange={e=>setK(e.target.value)}/><small>K stops = up to K + 1 flights</small></label>
          <label className="field"><span>Discount coupons (C)</span><input type="number" min="0" value={c} onChange={e=>setC(e.target.value)}/><small>Each coupon halves one flight</small></label>
        </div>

        {mode==='manual' && <div className="flight-editor">
          <div className="subheading"><div><h3>Flight connections</h3><p>Add the one-way flights available between cities.</p></div><button className="button button-light button-small" onClick={addFlight}>+ Add flight</button></div>
          <div className="flight-table-wrap"><table><thead><tr><th>FROM CITY</th><th>TO CITY</th><th>TICKET PRICE</th><th/></tr></thead><tbody>
            {rows.map((f,i)=><tr key={i}><td><input aria-label={`Flight ${i+1} source`} type="number" min="1" value={f.source} onChange={e=>updateFlight(i,'source',e.target.value)}/></td><td><input aria-label={`Flight ${i+1} destination`} type="number" min="1" value={f.destination} onChange={e=>updateFlight(i,'destination',e.target.value)}/></td><td><div className="price-input"><span>₹</span><input aria-label={`Flight ${i+1} price`} type="number" min="0" value={f.price} onChange={e=>updateFlight(i,'price',e.target.value)}/></div></td><td><button className="icon-button danger" aria-label="Remove flight" onClick={()=>removeFlight(i)}>×</button></td></tr>)}
          </tbody></table></div>
        </div>}

        {mode==='csv' && <div className="upload-panel"><div className="upload-icon"><Upload size={22}/></div><div><h3>Import a flight network</h3><p>Choose a CSV with the columns <code>source,destination,price</code>.</p><button className="button button-light button-small" onClick={()=>fileRef.current?.click()}>Choose CSV file</button><input ref={fileRef} type="file" accept=".csv,text/csv" hidden onChange={e=>e.target.files?.[0]&&loadCsv(e.target.files[0])}/>{csvError&&<p className="error-text">{csvError}</p>}</div><button className="text-button" onClick={()=>{const blob=new Blob(['source,destination,price\\n1,2,120\\n1,3,100\\n3,4,80\\n4,6,90\\n'],{type:'text/csv'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='sample-flights.csv';a.click();}}>Download sample CSV</button></div>}

        {mode==='random' && <div className="random-panel"><div className="config-grid random-fields"><label className="field"><span>Number of flights (M)</span><input type="number" min="0" max="500" value={m} onChange={e=>setM(e.target.value)}/></label><label className="field"><span>Random seed</span><input type="number" value={seed} onChange={e=>setSeed(e.target.value)}/><small>Same seed creates the same graph</small></label><label className="field"><span>Destination reachability</span><select value={reachable?'yes':'no'} onChange={e=>setReachable(e.target.value==='yes')}><option value="yes">Ensure a route exists</option><option value="no">Allow unreachable destination</option></select></label></div><button className="button button-light" onClick={makeRandom}><Shuffle size={16}/> Generate graph</button></div>}

        {error&&<div className="error-banner"><AlertCircle size={17}/>{error}</div>}
        <div className="planner-footer"><span className="hint"><CircleHelp size={15}/> Start is city 1 · Destination is city N</span><button className="button button-primary" onClick={solve}>Find cheapest route <ArrowRight size={16}/></button></div>
      </section>

      <div className="section-heading result-heading"><div><span className="step-tag">02</span><h2>Route analysis</h2></div><span className="muted">Your optimized flight plan</span></div>
      {!solved || !result ? <div className="empty-state card"><div className="empty-icon"><Route size={24}/></div><h3>Ready to calculate</h3><p>Generate a graph or load your flights, then find the cheapest route.</p></div> :
      <div className="results-grid">
        <section className="card graph-card">
          <div className="card-header"><div><h3>Flight network</h3><p>Directed graph · weighted connections</p></div><span className="status-chip"><span className="live-dot"/> {result.reachable?'Route found':'No valid route'}</span></div>
          <div className="graph-canvas">
            {Number(n)>0 && <svg viewBox={`0 0 ${graph.width} ${graph.height}`} role="img" aria-label="Directed flight graph">
              <defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#94a3b8"/></marker><marker id="arrowPath" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#3b82f6"/></marker><marker id="arrowGold" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#d99a22"/></marker></defs>
              {rows.map((f,i)=>{const a=graph.positions[Number(f.source)-1],b=graph.positions[Number(f.destination)-1];if(!a||!b)return null;const dx=b.x-a.x,dy=b.y-a.y,len=Math.max(1,Math.hypot(dx,dy)),ux=dx/len,uy=dy/len;const start={x:a.x+ux*23,y:a.y+uy*23},end={x:b.x-ux*25,y:b.y-uy*25};const isPath=pathEdgeSet.has(i),isCoupon=couponEdgeSet.has(i);const bend=(i%3-1)*13;const mx=(start.x+end.x)/2-uy*bend,my=(start.y+end.y)/2+ux*bend;return <g key={i}><path d={`M ${start.x} ${start.y} Q ${mx} ${my} ${end.x} ${end.y}`} fill="none" stroke={isCoupon?'#d99a22':isPath?'#3b82f6':'#cbd5e1'} strokeWidth={isPath?3.2:1.6} markerEnd={isCoupon?'url(#arrowGold)':isPath?'url(#arrowPath)':'url(#arrow)'}/><text x={mx} y={my-6} textAnchor="middle" className={`edge-label ${isCoupon?'gold-label':''}`}>{f.price}</text></g>})}
              {graph.positions.map(p=>{const isStart=p.id===1,isEnd=p.id===Number(n),isPath=pathNodeSet.has(p.id);let fill=isStart?'#d5f8e8':isEnd?'#ffe0e2':isPath?'#ffedcf':'#f1f5f9';let stroke=isStart?'#15966b':isEnd?'#e44f5f':isPath?'#e99a23':'#cbd5e1';return <g key={p.id}><circle cx={p.x} cy={p.y} r="21" fill={fill} stroke={stroke} strokeWidth="2"/><text x={p.x} y={p.y+4} textAnchor="middle" className="node-label">{p.id}</text>{isStart&&<text x={p.x} y={p.y+35} textAnchor="middle" className="node-caption">START</text>}{isEnd&&<text x={p.x} y={p.y+35} textAnchor="middle" className="node-caption">DEST</text>}</g>})}
              {currentNode&&graph.positions[currentNode-1]&&<g><circle cx={graph.positions[currentNode-1].x} cy={graph.positions[currentNode-1].y} r="28" fill="none" stroke="#8b5cf6" strokeWidth="3" strokeDasharray="4 4"/><circle cx={graph.positions[currentNode-1].x} cy={graph.positions[currentNode-1].y} r="5" fill="#8b5cf6"/></g>}
            </svg>}
          </div>
          <div className="legend"><span><i className="legend-dot start"/>Start</span><span><i className="legend-dot dest"/>Destination</span><span><i className="legend-dot stop"/>Path city</span><span><i className="legend-line path"/>Chosen route</span><span><i className="legend-line coupon"/>Coupon flight</span></div>
          <div className="graph-summary"><span><strong>{n}</strong> cities</span><span><strong>{rows.length}</strong> flights</span><span><strong>{k}</strong> max stops</span><span><strong>{c}</strong> coupons</span></div>
        </section>
        <section className="card result-card">
          <div className="card-header"><div><h3>Best available route</h3><p>Lowest cost within your constraints</p></div><div className="result-icon"><Wallet size={20}/></div></div>
          {result.reachable ? <>
            <div className="cost-label">MINIMUM TOTAL COST</div><div className="cost-value"><span>₹</span>{result.cost.toLocaleString('en-IN')}</div>
            <div className="route-chips">{result.path.map((city,i)=><React.Fragment key={`${city}-${i}`}><span className={`route-city ${i===0?'route-start':i===result.path.length-1?'route-end':'route-middle'}`}>{city}</span>{i<result.path.length-1&&<ArrowRight size={14} className="route-arrow"/>}</React.Fragment>)}</div>
            <div className="metric-grid"><div className="metric"><span>Flights</span><strong>{result.pathFlights.length}</strong></div><div className="metric"><span>Stops</span><strong>{result.stops}</strong></div><div className="metric"><span>Coupons used</span><strong>{result.couponsUsed}<small> / {c}</small></strong></div></div>
            <div className="breakdown"><h4>Flight-by-flight breakdown</h4>{result.pathFlights.map((f,i)=><div className="breakdown-row" key={i}><div className={`flight-index ${f.couponUsed?'coupon-index':''}`}>{String(i+1).padStart(2,'0')}</div><div className="flight-route"><strong>{f.source} <ArrowRight size={12}/> {f.destination}</strong><span>{f.couponUsed?'Coupon applied':'Full fare'}</span></div><div className="flight-cost"><span className={f.couponUsed?'old-price':''}>{f.couponUsed?`₹${f.price}`:''}</span><strong>₹{f.paidPrice}</strong></div></div>)}</div>
          </> : <div className="unreachable"><div className="empty-icon"><Route size={24}/></div><h3>No valid route found</h3><p>City {n} cannot be reached from city 1 using at most {Number(k)+1} flights. Try increasing K or adding flights.</p></div>}
          <button className="button button-primary full-button" disabled={!result.reachable||!pathFlights.length} onClick={startJourney}><Play size={16} fill="currentColor"/> Start journey animation</button>
          <button className="button button-light full-button export-button" onClick={downloadCsv}><Download size={16}/> Export results to CSV</button>
        </section>
      </div>}

      {solved && result?.reachable && <section className="card journey-card">
        <div className="card-header"><div><div className="eyebrow small-eyebrow"><MapPin size={13}/> LIVE REPLAY</div><h3>Your journey, step by step</h3><p>Watch the selected route and coupon savings in sequence.</p></div><span className="progress-text">{Math.max(0,animStep+1)} / {pathFlights.length} flights</span></div>
        <div className="progress-track"><div className="progress-fill" style={{width:`${pathFlights.length?Math.max(0,Math.min(100,(animStep+1)/pathFlights.length*100)):0}%`}}/></div>
        <div className="journey-live-grid"><div className="live-stat"><span>RUNNING COST</span><strong>₹{runningCost.toLocaleString('en-IN')}</strong></div><div className="live-stat"><span>STOPS VISITED</span><strong>{visitedStops}</strong></div><div className="live-stat"><span>COUPONS USED</span><strong>{usedCoupons} <small>/ {c}</small></strong></div><div className="live-stat"><span>STATUS</span><strong className="journey-status">{animStep<0?'Ready':running?(paused?'Paused':'In transit'):animStep>=pathFlights.length?'Complete':'Arrived'}</strong></div></div>
        {activeFlight && <div className={`active-flight ${activeFlight.couponUsed?'active-coupon':''}`}><div className="active-plane"><Plane size={20}/></div><div className="active-detail"><span>FLIGHT {Math.min(animStep+1,pathFlights.length)} OF {pathFlights.length}</span><strong>City {activeFlight.source} <ArrowRight size={15}/> City {activeFlight.destination}</strong><small>{activeFlight.couponUsed?'Coupon applied · 50% off':'Standard ticket price'}</small></div><div className="active-fare"><span>{activeFlight.couponUsed?`₹${activeFlight.price} →`: 'TICKET FARE'}</span><strong>₹{activeFlight.paidPrice}</strong></div></div>}
        {animStep>=pathFlights.length&&pathFlights.length>0&&<div className="success-banner"><CheckCircle2 size={18}/> Journey complete! Final cost: ₹{result.cost.toLocaleString('en-IN')}</div>}
        <div className="journey-controls"><button className="button button-primary" onClick={()=>{if(animStep<0||animStep>=pathFlights.length)startJourney();else setPaused(false);}}><Play size={15} fill="currentColor"/>{animStep<0||animStep>=pathFlights.length?'Start':'Resume'}</button><button className="button button-light" disabled={!running} onClick={()=>setPaused(true)}><Pause size={15}/> Pause</button><button className="button button-light" onClick={()=>{resetAnimation();}}><RotateCcw size={15}/> Reset</button><button className="button button-light" onClick={startJourney}><RotateCcw size={15}/> Restart</button></div>
      </section>}

      <section className="complexity-strip"><div className="complexity-icon"><Sparkles size={18}/></div><div><strong>Built for optimal decisions</strong><p>Layered shortest-path dynamic programming · Coupons tracked as part of each state.</p></div><div className="complexity-badges"><span>Time: O((K+1) · C · M)</span><span>Space: O((K+1) · C · N)</span></div></section>
      <footer><div className="footer-brand"><Plane size={15}/> Routewise</div><span>Budget Traveller with Coupons · Algorithm visualization project</span></footer>
    </main>
  </div>;
}

createRoot(document.getElementById('root')).render(<App/>);
