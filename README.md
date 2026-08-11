# Derivatives Pricing Dashboard

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-app-red?logo=streamlit&logoColor=white)
![License](https://img.shields.io/github/license/savsuth/BlackScholes-Pricing-Dashboard)

An interactive **Black–Scholes option pricing dashboard** built with **Streamlit**, enabling users to explore how option prices behave under different market conditions.
An interactive **Black–Scholes option pricing dashboard** built with **Streamlit**, enabling users to explore how option prices behave under different market conditions.  


---

## 🚀 Features

- **Option Pricing Calculator**
  - Compute European **Call** and **Put** option prices instantly.
  - Visualize values in a clean, responsive layout.

- **Interactive Heatmaps**
  - Explore how option prices vary with **Spot Price** and **Volatility** ranges.
  - Side-by-side heatmaps for quick comparison of Call vs. Put dynamics.

- **Customizable Inputs**
  - Spot Price (S)  
  - Strike Price (K)  
  - Time to Maturity (T, in years)  
  - Volatility (σ)  
  - Risk-Free Rate (r)  
  - User-defined ranges for Spot Price and Volatility for heatmaps.

---
## Dependencies

- **pandas**: For handling and displaying tabular input/output data  
- **numpy**: For mathematical and numerical operations  
- **scipy**: For statistical functions  
- **matplotlib**: For plotting static heatmaps  
- **seaborn**: For visually enhanced heatmap styles

## Installation
```bash
git clone https://github.com/savsuth/BlackScholes-Pricing-Dashboard.git
cd BlackScholes-Pricing-Dashboard
pip install -r requirements.txt
streamlit run streamlit_app.py
```

##  Results
### Dashboard Overview
<p align="center">
  <img src="Img-1.png" alt="Dashboard Overview" width="45%"/>
  <img src="Img-2.png" alt="Heatmap Example" width="45%"/>
</p>






