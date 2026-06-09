# Quantitative Crypto Framework

## Overview
This repository contains a modular, production-ready quantitative trading framework designed for digital asset analysis, backtesting, and automated execution. Developed with a strict mathematical and computational focus, the architecture spans from high-frequency, loop-free simulation engines to macro trend-following indicators and portfolio rebalancing modules.

---

## Repository Architecture & Modules

### Module 1: High-Performance Vectorized Backtesting Engine (Core Component)
The core simulation sub-system is a fully vectorized algorithmic backtesting engine built to evaluate short-term liquidity dislocations (pullbacks) within established macroeconomic uptrends. It completely eliminates iterative time-stepping (e.g., standard `for` loops or Pandas `iterrows()`), achieving $O(1)$ computational efficiency relative to row-by-row iteration.

#### Mathematical Strategy Definition
* **Signal Generation:** A primary signal is triggered at time $t$ if the structural and momentum conditions are simultaneously satisfied:
$$C_t > \frac{1}{200} \sum_{i=0}^{199} C_{t-i}$$
$$\%K_t = \frac{C_t - L_{10}}{H_{10} - L_{10}} \times 100 < 5$$
* **Execution & Limit Order Simulation:** Resting limit orders are simulated at a fixed 3% discount to the closing price ($P_{buy} = C_t \times 0.97$). Execution occurs if the low price satisfies $L_{t+i} \le P_{buy}$ within a forward-looking matrix window ($i \in [1, 10]$).
* **Computational Optimization:** Implements temporal matrix shifting to project future price vectors into the current row context. Optimal entry and exit points are isolated instantly via vectorized boolean masks and cumulative summation checks (`cumsum(axis=1) == 1`).

---

### Module 2: Algorithmic Portfolio Rebalancing (Binance API Integration)
An automated asset allocation and risk-mitigation module designed to interface directly with spot/margin accounts via the Binance API.

* **Dynamic Weight Adjustment:** The script tracks portfolio drift away from predefined target asset weights by calculating real-time geometric distances across asset vectors.
* **Execution Optimization:** Incorporates threshold-based execution bands (e.g., trigger rebalancing only when a specific asset deviates by $\pm X\%$ from its target). This optimization minimizes trading drag, controls transaction fee overhead, and protects capital against micro-volatility noise.

---

### Module 3: Secular Trend Filtering (Bull Market Support Band Framework)
A macro-directional regime filter utilized to dynamically adjust market exposure based on long-term support and resistance boundaries.

* **Mathematical Foundation:** Implements a dynamic indicator band that synthesizes the 20-week Exponential Moving Average (EMA) and the 21-week Simple Moving Average (SMA).
* **System Integration:** Acts as a systematic programmatic switch (`True/False` regime filter). Underlying algorithmic strategies reference this module to scale position sizes up or down depending on whether the macro market environment is classified as a structural expansion or contraction regime.

---

## Technical Stack & Dependencies
* **Data Manipulation & Processing:** `pandas`, `numpy` (heavy utilization of vectorization and matrix calculations).
* **Data Ingestion:** `yfinance` (historical analysis) and `Binance API` wrappers.
* **Technical Analysis:** `ta` library for structural momentum equations.
* **Visualization:** `matplotlib` for equity curve tracking, asset allocation distributions, and trade execution mapping.
