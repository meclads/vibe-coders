/**
 * Budget Traveller solver.
 * State is (flights used, city, coupons used), so the stop constraint is explicit.
 * Time: O((K+1) * C * M); space: O((K+1) * C * N) for DP and predecessors.
 */
export function solveBudgetRoute(n, flights, k, coupons) {
  if (!Number.isInteger(n) || n < 1 || !Number.isInteger(k) || k < 0 ||
      !Number.isInteger(coupons) || coupons < 0) throw new Error('Invalid graph parameters.');
  const edges = flights.map((f, edgeIndex) => ({
    source: Number(f.source), destination: Number(f.destination),
    price: Number(f.price), edgeIndex
  }));
  for (const e of edges) {
    if (!Number.isInteger(e.source) || !Number.isInteger(e.destination) ||
        e.source < 1 || e.source > n || e.destination < 1 || e.destination > n ||
        !Number.isSafeInteger(e.price) || e.price < 0) throw new Error('Invalid flight.');
  }
  if (n === 1) return { reachable: true, cost: 0, path: [1], pathFlights: [], stops: 0, couponsUsed: 0 };
  const maxFlights = k + 1, maxCoupons = Math.min(coupons, maxFlights);
  const INF = Number.POSITIVE_INFINITY;
  const adjacency = Array.from({length:n+1}, () => []);
  for (const edge of edges) adjacency[edge.source].push(edge);
  const dp = Array.from({length:maxFlights+1},()=>Array.from({length:n+1},()=>Array(maxCoupons+1).fill(INF)));
  const prev = Array.from({length:maxFlights+1},()=>Array.from({length:n+1},()=>Array(maxCoupons+1).fill(null)));
  dp[0][1][0] = 0;
  for (let usedFlights=0; usedFlights<maxFlights; usedFlights++) {
    for (let city=1; city<=n; city++) {
      for (let usedCoupons=0; usedCoupons<=maxCoupons; usedCoupons++) {
        const current=dp[usedFlights][city][usedCoupons];
        if (!Number.isFinite(current)) continue;
        for (const e of adjacency[city]) {
          const nextFlights=usedFlights+1;
          const full=current+e.price;
          if (full<dp[nextFlights][e.destination][usedCoupons]) {
            dp[nextFlights][e.destination][usedCoupons]=full;
            prev[nextFlights][e.destination][usedCoupons]={city,usedFlights,usedCoupons,edgeIndex:e.edgeIndex,couponUsed:false};
          }
          if (usedCoupons<maxCoupons) {
            const discounted=current+Math.floor(e.price/2);
            if (discounted<dp[nextFlights][e.destination][usedCoupons+1]) {
              dp[nextFlights][e.destination][usedCoupons+1]=discounted;
              prev[nextFlights][e.destination][usedCoupons+1]={city,usedFlights,usedCoupons,edgeIndex:e.edgeIndex,couponUsed:true};
            }
          }
        }
      }
    }
  }
  let best={cost:INF, flights:0, coupons:0};
  for(let f=1;f<=maxFlights;f++) for(let c=0;c<=maxCoupons;c++) {
    if(dp[f][n][c]<best.cost) best={cost:dp[f][n][c],flights:f,coupons:c};
  }
  if(!Number.isFinite(best.cost)) return {reachable:false,cost:-1,path:[],pathFlights:[],stops:0,couponsUsed:0};
  const pathFlights=[];
  let city=n, f=best.flights, c=best.coupons;
  while(f>0) {
    const p=prev[f][city][c];
    if(!p) throw new Error('Could not reconstruct optimal path.');
    const original=edges[p.edgeIndex];
    pathFlights.push({...original,couponUsed:p.couponUsed,paidPrice:p.couponUsed?Math.floor(original.price/2):original.price});
    city=p.city; f=p.usedFlights; c=p.usedCoupons;
  }
  pathFlights.reverse();
  const path=[1,...pathFlights.map(e=>e.destination)];
  return {reachable:true,cost:best.cost,path,pathFlights,stops:Math.max(0,pathFlights.length-1),couponsUsed:pathFlights.filter(e=>e.couponUsed).length};
}

export function parseFlightsCsv(text) {
  const lines=String(text).replace(/^\uFEFF/,'').split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
  if(lines.length<1) throw new Error('CSV file is empty.');
  const headers=splitCsvLine(lines[0]).map(s=>s.trim().toLowerCase());
  const required=['source','destination','price'];
  const indexes=Object.fromEntries(required.map(k=>[k,headers.indexOf(k)]));
  if(required.some(k=>indexes[k]<0)) throw new Error('CSV must contain source,destination,price columns.');
  const flights=[];
  for(let i=1;i<lines.length;i++) {
    const cols=splitCsvLine(lines[i]);
    const vals=required.map(k=>cols[indexes[k]]?.trim());
    if(vals.some(v=>v===undefined||v==='')) throw new Error(`Invalid or incomplete data on CSV row ${i+1}.`);
    const [source,destination,price]=vals.map(Number);
    if(!Number.isInteger(source)||source<1||!Number.isInteger(destination)||destination<1||!Number.isSafeInteger(price)||price<0) throw new Error(`Invalid city ID or price on CSV row ${i+1}.`);
    flights.push({source,destination,price});
  }
  if(!flights.length) throw new Error('CSV contains headers but no flight rows.');
  return flights;
}
function splitCsvLine(line) {
  const out=[]; let value='', quoted=false;
  for(let i=0;i<line.length;i++) {
    const ch=line[i];
    if(ch==='"'&&line[i+1]==='"'&&quoted){value+='"';i++;}
    else if(ch==='"') quoted=!quoted;
    else if(ch===','&&!quoted){out.push(value);value='';}
    else value+=ch;
  }
  if(quoted) throw new Error('CSV has an unmatched quote.');
  out.push(value); return out;
}

export function generateGraph(n, m, seed=1, ensureReachable=true) {
  if(!Number.isInteger(n)||n<1||n>40||!Number.isInteger(m)||m<0||m>500) throw new Error('N must be 1–40 and M must be 0–500.');
  let state=(Number(seed)>>>0)||1;
  const random=()=>{state=(1664525*state+1013904223)>>>0;return state/4294967296;};
  const flights=[];
  const seen=new Set();
  const add=(source,destination,price)=>{const key=`${source},${destination},${price}`;if(!seen.has(key)){seen.add(key);flights.push({source,destination,price});}};
  if(ensureReachable && n>1) for(let city=1;city<n;city++) add(city,city+1,Math.floor(random()*180)+20);
  let attempts=0;
  while(flights.length<m && attempts<m*30+100) {
    attempts++;
    const source=Math.floor(random()*n)+1,destination=Math.floor(random()*n)+1,price=Math.floor(random()*300)+1;
    add(source,destination,price);
  }
  return flights.slice(0,m);
}

export function exportFlightsCsv(flights, result) {
  const pathEdges=new Map();
  if(result?.reachable) for(const f of result.pathFlights) pathEdges.set(f.edgeIndex,f);
  const header=['source','destination','price','on_optimal_path','coupon_used','discounted_price','paid_price'];
  const rows=flights.map((f,i)=>{
    const chosen=pathEdges.get(i);
    const coupon=Boolean(chosen?.couponUsed);
    return [f.source,f.destination,f.price,chosen?'x':'',coupon?'x':'',coupon?Math.floor(Number(f.price)/2):f.price,chosen?chosen.paidPrice:''];
  });
  return [header,...rows].map(row=>row.map(v=>csvEscape(v)).join(',')).join('\r\n')+'\r\n';
}
function csvEscape(value) {
  const s=String(value ?? '');
  return /[",\r\n]/.test(s)?`"${s.replace(/"/g,'""')}"`:s;
}
