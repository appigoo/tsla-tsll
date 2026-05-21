import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="TSLA / TSLL 關係計算器",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .metric-card {
        background: #f7f6f2;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 4px;
    }
    .metric-label {
        font-size: 12px;
        color: #888;
        margin: 0 0 4px 0;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 600;
        color: #1a1a1a;
        margin: 0;
    }
    .metric-sub-up {
        font-size: 12px;
        color: #2d7a3a;
        margin: 4px 0 0 0;
    }
    .metric-sub-dn {
        font-size: 12px;
        color: #c0392b;
        margin: 4px 0 0 0;
    }
    .metric-sub-neu {
        font-size: 12px;
        color: #888;
        margin: 4px 0 0 0;
    }
    .section-title {
        font-size: 14px;
        font-weight: 600;
        color: #888;
        letter-spacing: 0.04em;
        margin: 1.5rem 0 0.75rem 0;
        text-transform: uppercase;
    }
    .warning-box {
        background: #fffbe8;
        border: 1px solid #f0c040;
        border-radius: 8px;
        padding: 10px 16px;
        font-size: 12px;
        color: #7a5a00;
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def get_prices():
    try:
        tsla = yf.Ticker("TSLA").history(period="5d")
        tsll = yf.Ticker("TSLL").history(period="5d")
        if not tsla.empty and not tsll.empty:
            tsla_now = tsla['Close'].iloc[-1]
            tsll_now = tsll['Close'].iloc[-1]
            tsla_prev = tsla['Close'].iloc[-2] if len(tsla) >= 2 else tsla_now
            tsll_prev = tsll['Close'].iloc[-2] if len(tsll) >= 2 else tsll_now
            return tsla_now, tsll_now, tsla_prev, tsll_prev
    except Exception:
        pass
    return 300.0, 10.0, 295.0, 9.8


@st.cache_data(ttl=300)
def get_history():
    try:
        tsla = yf.Ticker("TSLA").history(period="20d")['Close']
        return tsla
    except Exception:
        return pd.Series(dtype=float)


def fmt_chg(now, prev):
    chg = (now - prev) / prev * 100
    sign = "▲" if chg >= 0 else "▼"
    cls = "up" if chg >= 0 else "dn"
    return chg, sign, cls


tsla_now, tsll_now, tsla_prev, tsll_prev = get_prices()
tsla_chg, tsla_sign, tsla_cls = fmt_chg(tsla_now, tsla_prev)
tsll_chg, tsll_sign, tsll_cls = fmt_chg(tsll_now, tsll_prev)
ratio = tsll_now / tsla_now

# ── 頂部刷新 ──
col_h1, col_h2 = st.columns([6, 1])
with col_h1:
    st.markdown("## 📊 TSLA / TSLL 關係計算器")
with col_h2:
    if st.button("🔄 刷新", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── 四卡片 ──
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
      <p class="metric-label">TSLA 現價</p>
      <p class="metric-value">${tsla_now:.2f}</p>
      <p class="metric-sub-{tsla_cls}">{tsla_sign} {abs(tsla_chg):.2f}%　昨日對比</p>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
      <p class="metric-label">TSLL 現價</p>
      <p class="metric-value">${tsll_now:.2f}</p>
      <p class="metric-sub-{tsll_cls}">{tsll_sign} {abs(tsll_chg):.2f}%　昨日對比</p>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card">
      <p class="metric-label">TSLL 杠杆倍數</p>
      <p class="metric-value">2×</p>
      <p class="metric-sub-neu">每日重置型杠杆 ETF</p>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="metric-card">
      <p class="metric-label">TSLL / TSLA 比率</p>
      <p class="metric-value">{ratio:.4f}</p>
      <p class="metric-sub-neu">當前價格比率</p>
    </div>""", unsafe_allow_html=True)

st.divider()

# ── 圖表：TSLA 近20日 ──
st.markdown('<p class="section-title">TSLA 收盤價走勢（近 20 日）</p>', unsafe_allow_html=True)
hist = get_history()
if not hist.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index.strftime("%m/%d"),
        y=hist.values,
        mode='lines+markers',
        line=dict(color='#2980b9', width=2),
        marker=dict(size=5, color='#2980b9'),
        fill='tozeroy',
        fillcolor='rgba(41,128,185,0.07)',
        name='TSLA 收盤'
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickfont=dict(size=11, color='#999')),
        yaxis=dict(showgrid=True, gridcolor='#f0ede6', tickfont=dict(size=11, color='#999')),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ── 情景模擬 ──
st.markdown('<p class="section-title">情景模擬</p>', unsafe_allow_html=True)

col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    pct_change = st.slider(
        "TSLA 變化幅度（%）",
        min_value=-30.0, max_value=30.0, value=0.0, step=0.5,
        format="%.1f%%"
    )
with col_s2:
    target_price = st.number_input(
        "或直接輸入 TSLA 目標價（$）",
        min_value=10.0, max_value=2000.0,
        value=round(tsla_now * (1 + pct_change / 100), 2),
        step=1.0
    )
    # 若手動輸入覆蓋滑桿
    pct_from_input = (target_price - tsla_now) / tsla_now * 100
    if abs(pct_from_input - pct_change) > 0.6:
        pct_change = pct_from_input

tsll_chg_sim = pct_change * 2
tsll_new = tsll_now * (1 + tsll_chg_sim / 100)

rc1, rc2, rc3 = st.columns(3)
with rc1:
    st.metric("TSLA 變化率", f"{pct_change:+.2f}%")
with rc2:
    st.metric("TSLL 預期變化率", f"{tsll_chg_sim:+.2f}%")
with rc3:
    st.metric("TSLL 預期價格", f"${tsll_new:.2f}", delta=f"{tsll_chg_sim:+.2f}%")

if pct_change > 0:
    st.success(f"📈 上漲情景：TSLA +{pct_change:.1f}% → TSLL 預期 +{tsll_chg_sim:.1f}%，放大收益但風險更高。")
elif pct_change < 0:
    st.error(f"📉 下跌情景：TSLA {pct_change:.1f}% → TSLL 預期 {tsll_chg_sim:.1f}%，損失同步放大。")
else:
    st.info("請移動滑桿或輸入目標價格進行模擬。")

st.divider()

# ── 情景對照表 ──
st.markdown('<p class="section-title">情景對照表（-20% 至 +20%）</p>', unsafe_allow_html=True)

steps = list(range(-20, 25, 5))
rows = []
for s in steps:
    tsla_p = tsla_now * (1 + s / 100)
    tsll_c = s * 2
    tsll_p = tsll_now * (1 + tsll_c / 100)
    signal = "🟢 看漲" if s > 5 else ("🔴 看跌" if s < -5 else "⚪ 中性")
    rows.append({
        "TSLA 變化": f"{s:+d}%",
        "TSLA 價格 ($)": f"{tsla_p:.2f}",
        "TSLL 變化": f"{tsll_c:+d}%",
        "TSLL 預期價格 ($)": f"{tsll_p:.2f}",
        "信號": signal
    })

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# ── 波動衰減估算 ──
st.markdown('<p class="section-title">波動衰減估算（震盪市場）</p>', unsafe_allow_html=True)

col_d1, col_d2 = st.columns(2)
with col_d1:
    hold_days = st.slider("持有天數", 1, 90, 30, step=1, format="%d 天")
with col_d2:
    daily_vol = st.slider("假設日均波幅（%）", 1.0, 10.0, 3.0, step=0.5, format="%.1f%%")

v = daily_vol / 100
tsla_decay = (pow(1 - v * v / 2, hold_days) - 1) * 100
tsll_decay = (pow(1 - 4 * v * v / 2, hold_days) - 1) * 100

d1, d2 = st.columns(2)
with d1:
    st.metric(
        f"TSLA 累計損耗（{hold_days}天，假設持平）",
        f"{tsla_decay:.2f}%",
        delta=None
    )
with d2:
    st.metric(
        f"TSLL 波動衰減損耗（{hold_days}天）",
        f"{tsll_decay:.2f}%",
        delta=None
    )

st.markdown("""
<div class="warning-box">
⚠️ <strong>風險提示</strong>：杠杆 ETF 每日重置，長期持有時波動衰減（Volatility Decay）會侵蝕淨值，
即使 TSLA 最終持平，TSLL 仍可能虧損。本計算器僅供參考，不構成任何投資建議。數據來源：Yahoo Finance。
</div>
""", unsafe_allow_html=True)

# ── 側邊欄說明 ──
with st.sidebar:
    st.title("📖 使用說明")
    st.markdown("""
**計算公式**
```
TSLL 新價格 ≈ 當前 TSLL × (1 + 2 × TSLA變化率)
```

**波動衰減公式**
```
損耗 = (1 - σ²/2)^n - 1
TSLL損耗 = (1 - 4σ²/2)^n - 1
```
其中 σ = 日均波幅，n = 持有天數

**重要風險**
- TSLL 每日重置，不適合長期持有
- 震盪市場中損耗最為顯著
- 數據每 60 秒自動刷新
""")
    st.divider()
    st.caption("數據來源：Yahoo Finance（yfinance）")
