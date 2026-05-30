# Trading Master — Agent Handoff Guide 📈

This file serves as the context-building brief and configuration guide for coding agents modifying the **Trading Master** dashboard.

---

## 1. Product Shape
- **Core Experience**: A quantitative financial trading dashboard designed to backtest options trading strategies, visualize pricing models, and monitor risk profiles for multi-asset options contracts and portfolios.
- **Frontend Tech**: Streamlit-based data-science dashboard utilizing Pandas, Plotly/Altair for charts, and real-time numeric calculators.

---

## 2. Directory Structure
- **Physical Path**: `/Users/guoq/opc/trading-master/`
- **Main Files**:
  - `app.py`: Core Streamlit script containing dashboard logic, math formulas, and interactive controls.
  - `opc.config.json`: Dynamic host config file mapping port 8501 to the OPC server.

---

## 3. Runtime & Mapping Details
- **Type**: `proxy`
- **Port Bind**: Port `8501` (served locally via Streamlit daemon running under PM2)
- **PM2 Process Name**: `trading-master`
- **OPC Gateway Route**: `http://home.lab/trading-master/`
- **Config Override**: Managed by `opc.config.json`:
  ```json
  {
    "name": "Trading Master",
    "emoji": "📈",
    "description": "Multi-Asset Trading Strategy & Market Intelligence Dashboard",
    "type": "proxy",
    "target": "http://localhost:8501",
    "route": "/trading-master"
  }
  ```

---

## 4. Coding Agent Modification Rules
> [!IMPORTANT]
> 1. **Data Science Libraries**: Coding agents must verify that packages like `streamlit`, `pandas`, and `plotly` are available inside the `/opt/anaconda3` python env before altering algorithms.
> 2. **Daemon Management**: To load script edits, restart the Streamlit background process on PM2:
>    ```bash
>    pm2 restart trading-master
>    ```
