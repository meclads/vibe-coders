import test from 'node:test';
import assert from 'node:assert/strict';
import {solveBudgetRoute,parseFlightsCsv,generateGraph,exportFlightsCsv} from './solver.js';

test('direct flight uses coupon when cheaper',()=>{
  const r=solveBudgetRoute(2,[{source:1,destination:2,price:9}],0,1);
  assert.equal(r.cost,4); assert.equal(r.pathFlights[0].couponUsed,true);
});
test('K stops permits K+1 flights',()=>{
  const f=[{source:1,destination:2,price:2},{source:2,destination:3,price:2},{source:3,destination:4,price:2}];
  assert.equal(solveBudgetRoute(4,f,2,0).cost,6);
  assert.equal(solveBudgetRoute(4,f,1,0).cost,-1);
});
test('unreachable destination returns -1',()=>assert.equal(solveBudgetRoute(3,[{source:1,destination:2,price:1}],2,0).cost,-1));
test('price one can become zero',()=>assert.equal(solveBudgetRoute(2,[{source:1,destination:2,price:1}],0,1).cost,0));
test('coupons may be unused',()=>{const r=solveBudgetRoute(2,[{source:1,destination:2,price:10}],0,3);assert.equal(r.cost,5);assert.equal(r.couponsUsed,1);});
test('N=1 is zero-cost route',()=>{const r=solveBudgetRoute(1,[],0,0);assert.equal(r.cost,0);assert.deepEqual(r.path,[1]);});
test('CSV parser accepts reordered headers',()=>assert.deepEqual(parseFlightsCsv('price,destination,source\n20,2,1\n'),[{source:1,destination:2,price:20}]));
test('CSV parser rejects missing columns',()=>assert.throws(()=>parseFlightsCsv('from,to,cost\n1,2,3'),/must contain/));
test('seeded graph generation is deterministic',()=>assert.deepEqual(generateGraph(5,8,123),generateGraph(5,8,123)));
test('CSV export marks chosen and coupon flights',()=>{
 const flights=[{source:1,destination:2,price:9},{source:2,destination:3,price:7}];
 const r=solveBudgetRoute(3,flights,1,1);
 const csv=exportFlightsCsv(flights,r);
 assert.match(csv,/on_optimal_path,coupon_used/); assert.match(csv,/x,x,4,4/);
});
test('multiple coupons can change the optimal route',()=>{
 const flights=[
  {source:1,destination:4,price:20},
  {source:1,destination:2,price:7},
  {source:2,destination:3,price:7},
  {source:3,destination:4,price:7}
 ];
 const r=solveBudgetRoute(4,flights,2,3);
 assert.equal(r.cost,9);
 assert.deepEqual(r.path,[1,2,3,4]);
});
