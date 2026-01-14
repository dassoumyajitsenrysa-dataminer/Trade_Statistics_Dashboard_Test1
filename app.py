import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------
# PAGE CONFIG (DARK)
# -----------------------
st.set_page_config(
    page_title="India Export Market Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------
# DATA LOADING & CLEANING
# -----------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/trade_map_2024.txt", sep="\t")

    df = df.rename(columns={
        "Importers": "country",
        "Select your indicators-Value exported in 2024 (USD thousand)": "export_value",
        "Select your indicators-Growth in exported value between 2020-2024 (%, p.a.)": "growth",
        "Select your indicators-Ranking of partner countries in world imports": "world_rank"
    })

    # Remove aggregate
    df = df[df["country"] != "World"]

    # Convert to numeric
    for col in ["export_value", "growth", "world_rank"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Market strategy classification
    median_value = df["export_value"].median()

    df["strategy"] = "Watch"
    df.loc[(df.export_value >= median_value) & (df.growth >= 0), "strategy"] = "Invest"
    df.loc[(df.export_value < median_value) & (df.growth >= 0), "strategy"] = "Nurture"
    df.loc[(df.export_value >= median_value) & (df.growth < 0), "strategy"] = "Defend"

    return df


df = load_data()

# -----------------------
# HSN INPUT GATE
# -----------------------
st.title("🇮🇳 India Export Market Intelligence Dashboard")

c1, c2 = st.columns([3, 1])

hsn_code = c1.text_input(
    "Enter HSN Code",
    value="DEFAULT-HSN",
    help="Enter 6 or 8 digit HSN code"
)

analyze = c2.button("Analyze", use_container_width=True)

if not analyze:
    st.info("👆 Enter an HSN code and click **Analyze** to generate insights.")
    st.stop()

# -----------------------
# EXECUTIVE SUMMARY
# -----------------------
st.subheader(f"📊 Executive Summary — HSN: {hsn_code}")

k1, k2, k3, k4 = st.columns(4)

total_exports = df["export_value"].sum()
top_country_share = df["export_value"].max() / total_exports * 100
avg_growth = df["growth"].mean()

k1.metric("Total Export Value (USD Mn)", f"{total_exports/1000:,.1f}")
k2.metric("Active Markets", df.country.nunique())
k3.metric("Market Concentration", f"{top_country_share:.1f}%")
k4.metric("Avg Growth (CAGR)", f"{avg_growth:.1f}%")

# -----------------------
# GLOBAL FOOTPRINT
# -----------------------
st.subheader("🌍 Global Export Footprint")

m1, m2 = st.columns([2, 1])

with m1:
    map_fig = px.choropleth(
        df,
        locations="country",
        locationmode="country names",
        color="export_value",
        hover_name="country",
        color_continuous_scale="Blues",
        labels={"export_value": "Export Value (USD '000)"}
    )
    st.plotly_chart(map_fig, use_container_width=True)

with m2:
    top10 = df.sort_values("export_value", ascending=False).head(10)
    bar_fig = px.bar(
        top10,
        x="export_value",
        y="country",
        orientation="h",
        title="Top 10 Importing Markets",
        labels={"export_value": "USD '000", "country": ""}
    )
    st.plotly_chart(bar_fig, use_container_width=True)

# -----------------------
# MARKET OPPORTUNITY MATRIX
# -----------------------
st.subheader("📈 Market Opportunity Matrix")

# --- FIX FOR NaN SIZE ISSUE ---
scatter_df = df[df["export_value"].notna() & (df["export_value"] > 0)].copy()

scatter_df["bubble_size"] = scatter_df["export_value"] ** 0.5

fig_scatter = px.scatter(
    scatter_df,
    x="growth",
    y="export_value",
    size="bubble_size",
    color="strategy",
    hover_name="country",
    size_max=60,
    labels={
        "growth": "Export Growth (%)",
        "export_value": "Export Value (USD '000)"
    }
)

# Quadrant lines
median_growth = scatter_df["growth"].median()
median_value = scatter_df["export_value"].median()

fig_scatter.add_vline(x=median_growth, line_dash="dot", opacity=0.3)
fig_scatter.add_hline(y=median_value, line_dash="dot", opacity=0.3)

st.plotly_chart(fig_scatter, use_container_width=True)

# -----------------------
# STRATEGIC RECOMMENDATIONS
# -----------------------
st.subheader("🧠 Strategic Recommendations")

focus = df[df.strategy == "Invest"].sort_values("export_value", ascending=False).head(3)
risk_country = df.sort_values("export_value", ascending=False).iloc[0]

st.markdown(f"""
### ✅ Priority Markets
Focus immediately on **{', '.join(focus.country.tolist())}** — high value with positive momentum.

### ⚠️ Concentration Risk
**{risk_country.country}** alone contributes **{top_country_share:.1f}%** of total exports.

### 🚀 Expansion Signal
Markets in **Nurture** quadrant show growth but are under-penetrated.
""")

st.dataframe(
    df.sort_values("export_value", ascending=False)[
        ["country", "export_value", "growth", "strategy"]
    ],
    use_container_width=True
)
