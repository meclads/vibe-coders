# Budget Traveller with Coupons

A React + Vite app that finds the minimum-cost route from city 1 to city N with at most K intermediate stops and C coupons. Coupons halve one flight's price using floor division.

## Requirements
- Node.js 18+ (Node.js 20 LTS recommended)
- npm

## Run on Windows
Open this folder in VS Code, then in Terminal run:

```powershell
npm install
npm run dev
```

Open the local URL Vite prints (usually http://localhost:5173).

## Tests and production build

```powershell
npm test
npm run build
```

## CSV format

The CSV needs a header with `source,destination,price`. The graph is directed. City 1 is the start; city N is the destination, where N is inferred as the highest city ID in the CSV. In the UI you can adjust N if your graph contains an isolated higher-numbered destination.

## Algorithm

Layered dynamic programming state `(flightsUsed, city, couponsUsed)`. Each edge relaxes both the full-fare transition and, when a coupon remains, the discounted transition. The algorithm considers up to `K + 1` flights and reconstructs predecessor states to recover the selected route and coupon placements.

- Time: `O((K + 1) * C * M)` for the straightforward edge scanning implementation.
- Space: `O((K + 1) * C * N)` for DP states and predecessor pointers.

## Notes
- This app is client-side; no backend is required.
- The graph is drawn in an SVG with an automatic circular layout to keep setup simple.
- The journey replay advances one flight per second.
