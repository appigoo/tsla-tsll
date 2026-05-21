import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import feedparser
import datetime

st.set_page_config(
    page_title="TSLA / TSLL 智能計算器",
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
    .metric-label { font-size: 12px; color: #888; margin: 0 0 4px 0; }
    .metric-value { font-size: 26px; font-weight: 600; color: #1a1a1a; margin: 0; }
    .metric-sub-up   { font-size: 12px; color: #2d7a3a; margin: 4px 0 0 0; }
    .metric-sub-dn   { font-size: 12px; color: #c0392b; margin: 4px 0 0 0; }
    .metric-sub-neu  { font-size: 12px; color: #888;    margin: 4px 0 0 0; }
    .section-title {
        font-size: 13px; font-weight: 600; color: #888;
        letter-spacing: 0.05em; margin: 1.5rem 0 0.75rem 0;
        text-transform: uppercase;
    }
    .signal-box {
        border-radius: 12px; padding: 20px 24px; margin-bottom: 16px;
    }
    .signal-bull { background: #eaf6ec; border: 1.5px solid #2d7a3a; }
    .signal-bear { background: #fdecea; border: 1.5px solid #c0392b; }
    .signal-neu  { background: #f5f4f0; border: 1.5px solid #ccc; }
    .signal-title { font-size: 22px; font-weight: 700; margin: 0 0 4px 0; }
    .signal-sub   { font-size: 13px; color: #555; margin: 0; }
    .score-bar-wrap { background: #e8e6e0; border-radius: 99px; height: 10px; margin: 12px 0 4px; }
    .score-bar      { height: 10px; border-radius: 99px; transition: width 0.4s; }
    .factor-row {
        display: flex; align-items: center; justify-content: space-between;
        padding: 8px 0; border-bottom: 0.5px solid #ece9e2; font-size: 13px;
    }
    .factor-row:last-child { border-bottom: none; }
    .badge {
        display: inline-block; font-size: 11px; font-weight: 600;
        padding: 2px 10px; border-radius: 99px;
    }
    .badge-bull { background: #d4edda; color: #1a5e2a; }
    .badge-bear { background: #fad7d5; color: #8b1a1a; }
    .badge-neu  { background: #e8e6e0; color: #555; }
    .news-item  {
        padding: 8px 0; border-bottom: 0.5px solid #ece9e2;
        font-size: 13px; color: #333;
    }
    .news-item:last-child { border-bottom: none; }
    .news-time  { font-size: 11px; color: #aaa; margin-top: 2px; }
    .warning-box {
        background: #fffbe8; border: 1px solid #f0c040;
        border-radius: 8px; padding: 10px 16px;
        font-size: 12px; color: #7a5a00; margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════
# DATA FETCHING
# ════════════════════════════════════════

@st.cache_data(ttl=60)
def get_prices():
    try:
        tsla = yf.Ticker("TSLA").history(period="5d")
        tsll = yf.Ticker("TSLL").history(period="5d")
        if not tsla.empty and not tsll.empty:
            tsla_now  = tsla['Close'].iloc[-1]
            tsll_now  = tsll['Close'].iloc[-1]
            tsla_prev = tsla['Close'].iloc[-2] if len(tsla) >= 2 else tsla_now
            tsll_prev = tsll['Close'].iloc[-2] if len(tsll) >= 2 else tsll_now
            return tsla_now, tsll_now, tsla_prev, tsll_prev
    except Exception:
        pass
    return 300.0, 10.0, 295.0, 9.8


@st.cache_data(ttl=120)
def get_indicators():
    """RSI(14), MACD, Bollinger, Volume ratio for TSLA"""
    try:
        df = yf.Ticker("TSLA").history(period="60d")
        close = df['Close']
        vol   = df['Volume']

        # RSI
        delta = close.diff()
        gain  = delta.clip(lower=0)
        loss  = (-delta).clip(lower=0)
        avg_g = gain.ewm(com=13, adjust=False).mean()
        avg_l = loss.ewm(com=13, adjust=False).mean()
        rs    = avg_g / avg_l
        rsi   = (100 - 100 / (1 + rs)).iloc[-1]

        # MACD
        ema12  = close.ewm(span=12, adjust=False).mean()
        ema26  = close.ewm(span=26, adjust=False).mean()
        macd   = (ema12 - ema26).iloc[-1]
        signal = (ema12 - ema26).ewm(span=9, adjust=False).mean().iloc[-1]
        hist   = macd - signal

        # Bollinger %B
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        pct_b = ((close - (sma20 - 2*std20)) / (4*std20)).iloc[-1]

        # Volume ratio (today vs 20d avg)
        vol_ratio = vol.iloc[-1] / vol.rolling(20).mean().iloc[-1]

        return {
            'rsi': round(rsi, 1),
            'macd_hist': round(hist, 3),
            'pct_b': round(pct_b, 2),
            'vol_ratio': round(vol_ratio, 2)
        }
    except Exception:
        return {'rsi': 50.0, 'macd_hist': 0.0, 'pct_b': 0.5, 'vol_ratio': 1.0}


@st.cache_data(ttl=120)
def get_macro():
    """QQQ pre-market proxy + VIX"""
    try:
        vix = yf.Ticker("^VIX").history(period="2d")['Close']
        qqq = yf.Ticker("QQQ").history(period="5d")['Close']
        vix_now  = vix.iloc[-1]
        qqq_chg  = (qqq.iloc[-1] - qqq.iloc[-2]) / qqq.iloc[-2] * 100
        return {'vix': round(vix_now, 2), 'qqq_chg': round(qqq_chg, 2)}
    except Exception:
        return {'vix': 20.0, 'qqq_chg': 0.0}


@st.cache_data(ttl=180)
def get_put_call():
    """TSLA options Put/Call ratio"""
    try:
        tk   = yf.Ticker("TSLA")
        exp  = tk.options[0]
        chain = tk.option_chain(exp)
        put_vol  = chain.puts['volume'].sum()
        call_vol = chain.calls['volume'].sum()
        if call_vol > 0:
            return round(put_vol / call_vol, 2)
    except Exception:
        pass
    return 1.0


@st.cache_data(ttl=300)
def get_news():
    """Fetch TSLA/Musk RSS headlines"""
    feeds = [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=TSLA&region=US&lang=en-US",
        "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best",
    ]
    items = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                title = entry.get('title', '')
                pub   = entry.get('published', '')
                link  = entry.get('link', '')
                kw    = any(k in title.lower() for k in ['tesla', 'tsla', 'musk', 'elon'])
                if kw or 'yahoo' in url:
                    items.append({'title': title, 'pub': pub, 'link': link})
                if len(items) >= 6:
                    break
        except Exception:
            pass
        if len(items) >= 6:
            break

    # Sentiment: bullish keywords
    bull_kw = ['beat', 'surge', 'rally', 'jump', 'gain', 'record', 'strong', 'upgrade',
               'buy', 'bull', 'positive', 'growth', 'profit', 'delivery']
    bear_kw = ['miss', 'drop', 'fall', 'loss', 'recall', 'lawsuit', 'downgrade',
               'sell', 'bear', 'concern', 'decline', 'cut', 'weak', 'crash']
    bull_count = sum(1 for i in items if any(k in i['title'].lower() for k in bull_kw))
    bear_count = sum(1 for i in items if any(k in i['title'].lower() for k in bear_kw))
    news_score = (bull_count - bear_count)  # -6 to +6
    return items[:6], news_score


@st.cache_data(ttl=300)
def get_history():
    try:
        return yf.Ticker("TSLA").history(period="20d")['Close']
    except Exception:
        return pd.Series(dtype=float)


def fmt_chg(now, prev):
    chg  = (now - prev) / prev * 100
    sign = "▲" if chg >= 0 else "▼"
    cls  = "up" if chg >= 0 else "dn"
    return chg, sign, cls


# ════════════════════════════════════════
# DIRECTION ENGINE
# ════════════════════════════════════════

def compute_signal(ind, macro, pc_ratio, news_score, tsla_chg):
    """
    Five factors → weighted score 0-100
    Factor weights:
      盤前TSLA走勢  25
      QQQ方向       15
      VIX恐慌       20
      Put/Call      20
      技術(RSI+MACD) 20
    """
    scores = {}

    # 1. TSLA overnight/yesterday change
    if   tsla_chg >  2: s1 = 100
    elif tsla_chg >  0.5: s1 = 70
    elif tsla_chg > -0.5: s1 = 50
    elif tsla_chg > -2: s1 = 30
    else: s1 = 0
    scores['TSLA 昨日走勢'] = (s1, 25)

    # 2. QQQ direction
    qc = macro['qqq_chg']
    if   qc >  1: s2 = 100
    elif qc >  0: s2 = 65
    elif qc > -1: s2 = 35
    else: s2 = 0
    scores['QQQ 納指方向'] = (s2, 15)

    # 3. VIX
    vix = macro['vix']
    if   vix < 15: s3 = 100
    elif vix < 20: s3 = 75
    elif vix < 25: s3 = 50
    elif vix < 30: s3 = 25
    else: s3 = 0
    scores['VIX 恐慌指數'] = (s3, 20)

    # 4. Put/Call ratio (lower = more bullish)
    if   pc_ratio < 0.7: s4 = 100
    elif pc_ratio < 0.9: s4 = 70
    elif pc_ratio < 1.1: s4 = 50
    elif pc_ratio < 1.4: s4 = 25
    else: s4 = 0
    scores['期權 Put/Call'] = (s4, 20)

    # 5. Technical: RSI + MACD histogram
    rsi  = ind['rsi']
    hist = ind['macd_hist']
    # RSI
    if   30 < rsi < 50: rs = 60
    elif 50 <= rsi < 65: rs = 85
    elif rsi >= 65: rs = 40   # overbought caution
    elif rsi <= 30: rs = 30   # oversold — wait
    else: rs = 50
    # MACD
    ms = 75 if hist > 0 else 25
    s5 = int(rs * 0.6 + ms * 0.4)
    scores['技術指標 RSI/MACD'] = (s5, 20)

    # Weighted total
    total = sum(v * w for v, w in scores.values()) / sum(w for _, w in scores.values())

    # News overlay (±5 pts)
    news_adj = max(-10, min(10, news_score * 2.5))
    total = max(0, min(100, total + news_adj))

    return round(total), scores


# ════════════════════════════════════════
# LOAD DATA
# ════════════════════════════════════════

tsla_now, tsll_now, tsla_prev, tsll_prev = get_prices()
tsla_chg, tsla_sign, tsla_cls = fmt_chg(tsla_now, tsla_prev)
tsll_chg, tsll_sign, tsll_cls = fmt_chg(tsll_now, tsll_prev)
ratio  = tsll_now / tsla_now
ind    = get_indicators()
macro  = get_macro()
pc     = get_put_call()
news_items, news_score = get_news()
hist   = get_history()
score, factor_scores = compute_signal(ind, macro, pc, news_score, tsla_chg)


# ════════════════════════════════════════
# HEADER
# ════════════════════════════════════════

col_h1, col_h2 = st.columns([6, 1])
with col_h1:
    st.markdown("## 📊 TSLA / TSLL 智能計算器")
    st.caption(f"最後更新：{datetime.datetime.now().strftime('%H:%M:%S')}　數據來源：Yahoo Finance")
with col_h2:
    if st.button("🔄 刷新數據", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ════════════════════════════════════════
# TOP METRICS
# ════════════════════════════════════════

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-card">
      <p class="metric-label">TSLA 現價</p>
      <p class="metric-value">${tsla_now:.2f}</p>
      <p class="metric-sub-{tsla_cls}">{tsla_sign} {abs(tsla_chg):.2f}%　昨日對比</p>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card">
      <p class="metric-label">TSLL 現價</p>
      <p class="metric-value">${tsll_now:.2f}</p>
      <p class="metric-sub-{tsll_cls}">{tsll_sign} {abs(tsll_chg):.2f}%　昨日對比</p>
    </div>""", unsafe_allow_html=True)
with c3:
    vix_cls = "dn" if macro['vix'] > 25 else ("neu" if macro['vix'] > 18 else "up")
    st.markdown(f"""<div class="metric-card">
      <p class="metric-label">VIX 恐慌指數</p>
      <p class="metric-value">{macro['vix']}</p>
      <p class="metric-sub-{vix_cls}">{'⚠️ 高恐慌' if macro['vix']>25 else ('中性' if macro['vix']>18 else '✅ 低恐慌')}</p>
    </div>""", unsafe_allow_html=True)
with c4:
    pc_cls = "up" if pc < 0.9 else ("neu" if pc < 1.2 else "dn")
    st.markdown(f"""<div class="metric-card">
      <p class="metric-label">Put/Call 比率</p>
      <p class="metric-value">{pc}</p>
      <p class="metric-sub-{pc_cls}">{'看多情緒' if pc<0.9 else ('中性' if pc<1.2 else '看空情緒')}</p>
    </div>""", unsafe_allow_html=True)

st.divider()

# ════════════════════════════════════════
# DIRECTION ENGINE OUTPUT
# ════════════════════════════════════════

st.markdown('<p class="section-title">🧠 今日方向預判引擎</p>', unsafe_allow_html=True)

if score >= 62:
    box_cls   = "signal-bull"
    direction = "📈 偏多　建議持有 / 買入 TSLL"
    summary   = f"五大信號綜合偏多，信心指數 {score}/100。VIX 處於 {macro['vix']} 安全區間，期權市場傾向看漲。"
    bar_color = "#2d7a3a"
elif score <= 38:
    box_cls   = "signal-bear"
    direction = "📉 偏空　建議觀望 / 減持 TSLL"
    summary   = f"五大信號綜合偏空，信心指數 {score}/100。謹慎操作，杠杆放大虧損風險。"
    bar_color = "#c0392b"
else:
    box_cls   = "signal-neu"
    direction = "⚖️ 中性　方向不明，建議觀望"
    summary   = f"信號混合，信心指數 {score}/100。建議等待更明確的方向再入場。"
    bar_color = "#888"

st.markdown(f"""
<div class="signal-box {box_cls}">
  <p class="signal-title">{direction}</p>
  <p class="signal-sub">{summary}</p>
  <div class="score-bar-wrap">
    <div class="score-bar" style="width:{score}%; background:{bar_color};"></div>
  </div>
  <p style="font-size:11px; color:#888; margin:0;">信心指數：{score} / 100</p>
</div>
""", unsafe_allow_html=True)

# Factor breakdown
st.markdown("**五大信號明細**")
factor_col1, factor_col2 = st.columns(2)
items_list = list(factor_scores.items())

def factor_badge(score_val):
    if score_val >= 65:
        return f'<span class="badge badge-bull">看多</span>'
    elif score_val <= 35:
        return f'<span class="badge badge-bear">看空</span>'
    else:
        return f'<span class="badge badge-neu">中性</span>'

def factor_detail(name, ind, macro, pc):
    details = {
        'TSLA 昨日走勢': f"{tsla_sign} {abs(tsla_chg):.2f}%",
        'QQQ 納指方向':  f"{'▲' if macro['qqq_chg']>=0 else '▼'} {abs(macro['qqq_chg']):.2f}%",
        'VIX 恐慌指數':  f"{macro['vix']}",
        '期權 Put/Call': f"P/C = {pc}",
        '技術指標 RSI/MACD': f"RSI {ind['rsi']} | MACD hist {ind['macd_hist']:+.3f}",
    }
    return details.get(name, "")

for i, (name, (sv, wt)) in enumerate(items_list):
    col = factor_col1 if i % 2 == 0 else factor_col2
    detail = factor_detail(name, ind, macro, pc)
    with col:
        st.markdown(f"""
        <div class="factor-row">
          <span><b>{name}</b><br><span style="color:#aaa;font-size:11px">{detail}</span></span>
          <span style="text-align:right">
            {factor_badge(sv)}
            <span style="font-size:11px; color:#aaa; margin-left:6px">權重 {wt}%</span>
          </span>
        </div>""", unsafe_allow_html=True)

st.divider()

# ════════════════════════════════════════
# NEWS
# ════════════════════════════════════════

st.markdown('<p class="section-title">📰 TSLA 最新資訊</p>', unsafe_allow_html=True)
if news_items:
    for item in news_items:
        title = item['title']
        pub   = item.get('pub', '')[:16]
        link  = item.get('link', '#')
        st.markdown(f"""
        <div class="news-item">
          <a href="{link}" target="_blank" style="color:#1a1a1a; text-decoration:none;">{title}</a>
          <p class="news-time">{pub}</p>
        </div>""", unsafe_allow_html=True)
else:
    st.info("暫無最新新聞。")

st.divider()

# ════════════════════════════════════════
# PRICE CHART
# ════════════════════════════════════════

st.markdown('<p class="section-title">TSLA 收盤價走勢（近 20 日）</p>', unsafe_allow_html=True)
if not hist.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index.strftime("%m/%d"), y=hist.values,
        mode='lines+markers',
        line=dict(color='#2980b9', width=2),
        marker=dict(size=5, color='#2980b9'),
        fill='tozeroy', fillcolor='rgba(41,128,185,0.07)',
        name='TSLA 收盤'
    ))
    fig.update_layout(
        height=220, margin=dict(l=0,r=0,t=8,b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickfont=dict(size=11,color='#999')),
        yaxis=dict(showgrid=True, gridcolor='#f0ede6', tickfont=dict(size=11,color='#999')),
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ════════════════════════════════════════
# SCENARIO SIMULATOR
# ════════════════════════════════════════

st.markdown('<p class="section-title">情景模擬</p>', unsafe_allow_html=True)

col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    pct_change = st.slider("TSLA 變化幅度（%）", -30.0, 30.0, 0.0, 0.5, format="%.1f%%")
with col_s2:
    target_price = st.number_input(
        "或直接輸入 TSLA 目標價（$）",
        min_value=10.0, max_value=2000.0,
        value=round(tsla_now * (1 + pct_change / 100), 2), step=1.0
    )
    pct_from_input = (target_price - tsla_now) / tsla_now * 100
    if abs(pct_from_input - pct_change) > 0.6:
        pct_change = pct_from_input

tsll_chg_sim = pct_change * 2
tsll_new      = tsll_now * (1 + tsll_chg_sim / 100)

rc1, rc2, rc3 = st.columns(3)
with rc1:  st.metric("TSLA 變化率",       f"{pct_change:+.2f}%")
with rc2:  st.metric("TSLL 預期變化率",    f"{tsll_chg_sim:+.2f}%")
with rc3:  st.metric("TSLL 預期價格",      f"${tsll_new:.2f}", delta=f"{tsll_chg_sim:+.2f}%")

if pct_change > 0:
    st.success(f"📈 上漲情景：TSLA +{pct_change:.1f}% → TSLL 預期 +{tsll_chg_sim:.1f}%，放大收益但風險更高。")
elif pct_change < 0:
    st.error(f"📉 下跌情景：TSLA {pct_change:.1f}% → TSLL 預期 {tsll_chg_sim:.1f}%，損失同步放大。")
else:
    st.info("請移動滑桿或輸入目標價格進行模擬。")

st.divider()

# ════════════════════════════════════════
# SCENARIO TABLE
# ════════════════════════════════════════

st.markdown('<p class="section-title">情景對照表（-20% 至 +20%）</p>', unsafe_allow_html=True)
rows = []
for s in range(-20, 25, 5):
    tsla_p = tsla_now * (1 + s/100)
    tsll_c = s * 2
    tsll_p = tsll_now * (1 + tsll_c/100)
    signal = "🟢 看漲" if s > 5 else ("🔴 看跌" if s < -5 else "⚪ 中性")
    rows.append({
        "TSLA 變化":       f"{s:+d}%",
        "TSLA 價格 ($)":   f"{tsla_p:.2f}",
        "TSLL 變化":       f"{tsll_c:+d}%",
        "TSLL 預期價格 ($)": f"{tsll_p:.2f}",
        "信號":            signal
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()

# ════════════════════════════════════════
# DECAY CALCULATOR
# ════════════════════════════════════════

st.markdown('<p class="section-title">波動衰減估算（震盪市場）</p>', unsafe_allow_html=True)
col_d1, col_d2 = st.columns(2)
with col_d1: hold_days = st.slider("持有天數", 1, 90, 30, step=1, format="%d 天")
with col_d2: daily_vol = st.slider("假設日均波幅（%）", 1.0, 10.0, 3.0, step=0.5, format="%.1f%%")

v = daily_vol / 100
tsla_decay = (pow(1 - v*v/2,   hold_days) - 1) * 100
tsll_decay = (pow(1 - 4*v*v/2, hold_days) - 1) * 100

d1, d2 = st.columns(2)
with d1: st.metric(f"TSLA 累計損耗（{hold_days}天）", f"{tsla_decay:.2f}%")
with d2: st.metric(f"TSLL 波動衰減損耗（{hold_days}天）", f"{tsll_decay:.2f}%")

st.markdown("""
<div class="warning-box">
⚠️ <strong>風險提示</strong>：本工具所有信號僅供參考，不構成投資建議。
杠杆 ETF 每日重置，震盪市場中損耗顯著，請嚴格控制倉位及止損。
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════

with st.sidebar:
    st.title("📖 引擎說明")
    st.markdown(f"""
**信心指數：{score} / 100**

| 因子 | 權重 |
|------|------|
| TSLA 昨日走勢 | 25% |
| QQQ 納指方向  | 15% |
| VIX 恐慌指數  | 20% |
| 期權 Put/Call | 20% |
| RSI + MACD    | 20% |

---
**當前技術數據**
- RSI(14)：`{ind['rsi']}`
- MACD Hist：`{ind['macd_hist']:+.3f}`
- 成交量比：`{ind['vol_ratio']}x`
- QQQ：`{'▲' if macro['qqq_chg']>=0 else '▼'} {abs(macro['qqq_chg']):.2f}%`

---
**使用建議**
- 信心 ≥ 62：考慮做多 TSLL
- 信心 ≤ 38：觀望或做空
- 38–62：方向不明，等待

數據每 60 秒自動刷新。
""")
    st.caption("⚠️ 不構成投資建議")
