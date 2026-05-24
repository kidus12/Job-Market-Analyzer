import streamlit as st
import anthropic
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup
import json
import re
from collections import Counter
from tavily import TavilyClient

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Job Market Analyzer",
    page_icon="📊",
    layout="wide"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Space Mono', monospace !important;
    }

    .stApp {
        background-color: #0a0a0f;
        color: #e8e8f0;
    }

    .metric-card {
        background: linear-gradient(135deg, #12121a, #1a1a2e);
        border: 1px solid #2a2a4a;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }

    .metric-value {
        font-family: 'Space Mono', monospace;
        font-size: 2.4rem;
        font-weight: 700;
        color: #7c6aff;
        line-height: 1;
    }

    .metric-label {
        font-size: 0.8rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: 6px;
    }

    .skill-tag {
        display: inline-block;
        background: #1a1a2e;
        border: 1px solid #7c6aff44;
        border-radius: 6px;
        padding: 4px 10px;
        margin: 3px;
        font-size: 0.78rem;
        color: #a89fff;
        font-family: 'Space Mono', monospace;
    }

    .section-header {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #7c6aff;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid #2a2a4a;
    }

    .stButton > button {
        background: linear-gradient(135deg, #7c6aff, #5a4fcf);
        color: white;
        border: none;
        border-radius: 8px;
        font-family: 'Space Mono', monospace;
        font-size: 0.85rem;
        letter-spacing: 1px;
        padding: 12px 28px;
        width: 100%;
        transition: opacity 0.2s;
    }

    .stButton > button:hover {
        opacity: 0.85;
    }

    .stSelectbox label, .stMultiSelect label {
        color: #888 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
    }

    .job-card {
        background: #12121a;
        border: 1px solid #2a2a4a;
        border-left: 3px solid #7c6aff;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 10px;
    }

    .job-title {
        font-family: 'Space Mono', monospace;
        font-size: 0.9rem;
        color: #e8e8f0;
        font-weight: 700;
    }

    .job-company {
        color: #7c6aff;
        font-size: 0.82rem;
        margin-top: 4px;
    }

    .job-meta {
        color: #666;
        font-size: 0.75rem;
        margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("# 📊 Job Market Analyzer")
st.markdown("*Real-time intelligence on DS/AI internship trends*")
st.markdown("---")

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 API Keys")
    tavily_key = st.text_input("Tavily API Key", type="password", value="add tavily key here")
    anthropic_key = st.text_input("Anthropic API Key", type="password", value="add claude code here")

    st.markdown("---")
    st.markdown("### 🎯 Search Filters")

    role_type = st.multiselect(
        "Role Type",
        ["Data Science", "AI/ML", "Software Engineering", "Data Analytics", "Data Engineering"],
        default=["Data Science", "AI/ML"]
    )

    location = st.selectbox(
        "Location",
        ["DMV (DC/MD/VA)", "Remote", "Nationwide", "New York", "San Francisco", "Seattle"]
    )

    experience_level = st.selectbox(
        "Level",
        ["Internship", "Entry Level", "Both"]
    )

    num_results = st.slider("Results to fetch", 10, 50, 20)

    st.markdown("---")
    run_button = st.button("🔍 Analyze Market")


# ── Helper: scrape intern-list.com ─────────────────────────────────────────
def scrape_intern_list(query: str, location_filter: str) -> list[dict]:
    listings = []
    loc_map = {
        "DMV (DC/MD/VA)": "washington-dc",
        "Remote": "remote",
        "Nationwide": "",
        "New York": "new-york",
        "San Francisco": "san-francisco",
        "Seattle": "seattle"
    }
    loc_slug = loc_map.get(location_filter, "")
    url = f"https://intern-list.com/?search={requests.utils.quote(query)}"
    if loc_slug:
        url += f"&location={loc_slug}"

    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.find_all("div", class_=re.compile(r"job|listing|card|posting", re.I))[:20]
        for card in cards:
            title_el = card.find(["h2", "h3", "a"], class_=re.compile(r"title|role|position", re.I))
            company_el = card.find(["span", "div", "p"], class_=re.compile(r"company|employer|org", re.I))
            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else ""
            desc = card.get_text(separator=" ", strip=True)[:500]
            if title and len(title) > 3:
                listings.append({
                    "title": title,
                    "company": company,
                    "location": location_filter,
                    "description": desc,
                    "source": "intern-list.com"
                })
    except Exception as e:
        st.warning(f"intern-list scrape partial: {e}")
    return listings


# ── Helper: fetch via Tavily ───────────────────────────────────────────────
def fetch_via_tavily(tavily_client, role_types: list, location: str, num: int) -> list[dict]:
    listings = []
    loc_str = location.replace("DMV (DC/MD/VA)", "Washington DC Maryland Virginia")
    for role in role_types[:3]:
        level = "internship 2025 2026"
        query = f"{role} {level} {loc_str} site:linkedin.com OR site:indeed.com OR site:lever.co OR site:greenhouse.io"
        try:
            results = tavily_client.search(
                query=query,
                search_depth="basic",
                max_results=max(5, num // len(role_types))
            )
            for r in results.get("results", []):
                listings.append({
                    "title": r.get("title", ""),
                    "location": location,
                    "description": r.get("content", "")[:600],
                    "url": r.get("url", ""),
                    "source": "Tavily/Web"
                })
        except Exception as e:
            st.warning(f"Tavily query failed for {role}: {e}")
    return listings


# ── Helper: Claude extracts structured data ────────────────────────────────
def extract_job_data_with_claude(client, listings: list[dict]) -> list[dict]:
    if not listings:
        return []

    structured = []
    batch_size = 10
    progress = st.progress(0, text="Extracting skills with Claude...")

    for i in range(0, len(listings), batch_size):
        batch = listings[i:i+batch_size]
        batch_text = "\n\n---\n\n".join([
            f"LISTING {j+1}:\nTitle: {l.get('title','')}\nURL: {l.get('url','')}\nDescription: {l.get('description','')[:400]}"
            for j, l in enumerate(batch)
        ])

        prompt = f"""Analyze these job listings and extract structured data. Return ONLY valid JSON, no other text.

{batch_text}

Return a JSON array where each element has:
- "title": job title (string)
- "company": company name extracted from the description or URL — look for phrases like "at CompanyName", "join CompanyName", or the hiring organization mentioned in the text. Never return "Unknown", make your best guess from available context.
- "role_category": one of ["Data Science", "AI/ML", "Software Engineering", "Data Analytics", "Data Engineering", "Other"]
- "skills": array of specific technical skills mentioned (e.g. ["Python", "SQL", "TensorFlow", "AWS"])
- "location_type": one of ["Remote", "Hybrid", "On-site", "Unknown"]
- "experience_level": one of ["Internship", "Entry Level", "Mid Level", "Unknown"]

Extract only skills explicitly mentioned. Return exactly {len(batch)} objects in the array."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text.strip()
            text = re.sub(r"```json\s*|\s*```", "", text).strip()
            parsed = json.loads(text)
            for j, item in enumerate(parsed):
                if j < len(batch):
                    item["source"] = batch[j].get("source", "")
                    item["url"] = batch[j].get("url", "")
                structured.append(item)
        except Exception as e:
            st.warning(f"Claude parse error on batch {i//batch_size + 1}: {e}")
            for l in batch:
                structured.append({
                    "title": l.get("title", ""),
                    "company": l.get("company", ""),
                    "role_category": "Other",
                    "skills": [],
                    "location_type": "Unknown",
                    "experience_level": "Unknown",
                    "source": l.get("source", ""),
                    "url": l.get("url", "")
                })

        progress.progress(min((i + batch_size) / len(listings), 1.0),
                         text=f"Processed {min(i+batch_size, len(listings))}/{len(listings)} listings...")

    progress.empty()
    return structured


# ── Helper: build charts ───────────────────────────────────────────────────
CHART_THEME = {
    "paper_bgcolor": "#0a0a0f",
    "plot_bgcolor": "#0a0a0f",
    "font": {"color": "#e8e8f0", "family": "DM Sans"},
    "colorway": ["#7c6aff", "#5a9fff", "#ff6a9f", "#6affb8", "#ffb86a", "#ff6a6a"]
}

def skill_frequency_chart(structured: list[dict]):
    all_skills = []
    for item in structured:
        all_skills.extend([s.strip() for s in item.get("skills", [])])
    if not all_skills:
        st.info("No skills extracted.")
        return
    counts = Counter(all_skills).most_common(25)
    df = pd.DataFrame(counts, columns=["Skill", "Count"])
    fig = go.Figure(go.Bar(
        x=df["Count"], y=df["Skill"], orientation="h",
        marker=dict(color=df["Count"], colorscale=[[0, "#2a2a4a"], [1, "#7c6aff"]], showscale=False),
        text=df["Count"], textposition="outside", textfont=dict(color="#e8e8f0", size=11)
    ))
    fig.update_layout(
        title=dict(text="Top Skills in Demand", font=dict(family="Space Mono", size=14, color="#7c6aff")),
        yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
        xaxis=dict(showgrid=False, zeroline=False),
        height=600, margin=dict(l=10, r=60, t=50, b=10), **CHART_THEME
    )
    st.plotly_chart(fig, use_container_width=True)


def company_chart(structured: list[dict]):
    companies = [item.get("company", "") for item in structured if item.get("company") and item.get("company") not in ("Unknown", "")]
    if not companies:
        st.info("No company data available.")
        return
    counts = Counter(companies).most_common(15)
    df = pd.DataFrame(counts, columns=["Company", "Listings"])
    fig = px.bar(df, x="Company", y="Listings", color="Listings",
                 color_continuous_scale=["#2a2a4a", "#7c6aff"])
    fig.update_layout(
        title=dict(text="Most Active Hiring Companies", font=dict(family="Space Mono", size=14, color="#7c6aff")),
        coloraxis_showscale=False, xaxis_tickangle=-35, height=400,
        margin=dict(l=10, r=10, t=50, b=80), **CHART_THEME
    )
    st.plotly_chart(fig, use_container_width=True)


def role_breakdown_chart(structured: list[dict]):
    roles = [item.get("role_category", "Other") for item in structured]
    counts = Counter(roles)
    df = pd.DataFrame(list(counts.items()), columns=["Role", "Count"])
    fig = px.pie(df, names="Role", values="Count", hole=0.55,
                 color_discrete_sequence=["#7c6aff", "#5a9fff", "#ff6a9f", "#6affb8", "#ffb86a", "#ff6a6a"])
    fig.update_layout(
        title=dict(text="Role Type Breakdown", font=dict(family="Space Mono", size=14, color="#7c6aff")),
        legend=dict(font=dict(color="#e8e8f0")), height=380,
        margin=dict(l=10, r=10, t=50, b=10), **CHART_THEME
    )
    fig.update_traces(textfont_color="#e8e8f0")
    st.plotly_chart(fig, use_container_width=True)


def location_type_chart(structured: list[dict]):
    locs = [item.get("location_type", "Unknown") for item in structured]
    counts = Counter(locs)
    df = pd.DataFrame(list(counts.items()), columns=["Type", "Count"])
    fig = px.bar(df, x="Type", y="Count", color="Type",
                 color_discrete_sequence=["#7c6aff", "#5a9fff", "#ff6a9f", "#6affb8"])
    fig.update_layout(
        title=dict(text="Remote vs On-site Breakdown", font=dict(family="Space Mono", size=14, color="#7c6aff")),
        showlegend=False, height=350, margin=dict(l=10, r=10, t=50, b=10), **CHART_THEME
    )
    st.plotly_chart(fig, use_container_width=True)


# ── Main logic ─────────────────────────────────────────────────────────────
if run_button:
    if not tavily_key or not anthropic_key:
        st.error("Please enter both API keys in the sidebar.")
    elif not role_type:
        st.error("Select at least one role type.")
    else:
        tavily_client = TavilyClient(api_key=tavily_key)
        anthropic_client = anthropic.Anthropic(api_key=anthropic_key)

        with st.spinner("Fetching live listings..."):
            tavily_listings = fetch_via_tavily(tavily_client, role_type, location, num_results)
            query_str = " ".join(role_type[:2])
            intern_list_listings = scrape_intern_list(query_str, location)
            all_listings = tavily_listings + intern_list_listings

        if not all_listings:
            st.error("No listings found. Try adjusting filters.")
        else:
            st.success(f"Found **{len(all_listings)}** listings ({len(tavily_listings)} from web, {len(intern_list_listings)} from intern-list.com)")
            structured = extract_job_data_with_claude(anthropic_client, all_listings)
            if not structured:
                st.error("Extraction failed. Check your Anthropic API key.")
            else:
                st.session_state["structured"] = structured
                st.session_state["ran"] = True


# ── Display results ────────────────────────────────────────────────────────
if st.session_state.get("ran") and "structured" in st.session_state:
    structured = st.session_state["structured"]
    total = len(structured)

    all_skills = []
    for item in structured:
        all_skills.extend(item.get("skills", []))
    unique_skills = len(set(all_skills))
    companies = set(i.get("company", "") for i in structured if i.get("company") and i.get("company") not in ("Unknown", ""))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{total}</div><div class="metric-label">Listings Analyzed</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{unique_skills}</div><div class="metric-label">Unique Skills Found</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(companies)}</div><div class="metric-label">Companies Hiring</div></div>', unsafe_allow_html=True)
    with col4:
        top_skill = Counter(all_skills).most_common(1)[0][0] if all_skills else "N/A"
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="font-size:1.3rem">{top_skill}</div><div class="metric-label">Most Wanted Skill</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📈 Skills", "🏢 Companies & Roles", "📋 Listings"])

    with tab1:
        skill_frequency_chart(structured)
        st.markdown('<div class="section-header">Top Skills At a Glance</div>', unsafe_allow_html=True)
        top_skills = Counter(all_skills).most_common(15)
        tags_html = "".join([f'<span class="skill-tag">{s} <b>({c})</b></span>' for s, c in top_skills])
        st.markdown(tags_html, unsafe_allow_html=True)

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            role_breakdown_chart(structured)
        with c2:
            location_type_chart(structured)
        company_chart(structured)

    with tab3:
        st.markdown('<div class="section-header">Raw Listings</div>', unsafe_allow_html=True)
        for item in structured[:30]:
            title = item.get("title", "Untitled")
            company = item.get("company", "")
            role_cat = item.get("role_category", "")
            skills = item.get("skills", [])[:5]
            loc_type = item.get("location_type", "")
            source = item.get("source", "")
            url = item.get("url", "")
            skills_str = " · ".join(skills) if skills else "No skills extracted"
            link = f'<a href="{url}" target="_blank" style="color:#7c6aff; font-size:0.75rem;">View listing →</a>' if url else ""
            st.markdown(f"""
            <div class="job-card">
                <div class="job-title">{title}</div>
                <div class="job-company">{company}</div>
                <div class="job-meta">{role_cat} · {loc_type} · {source}</div>
                <div class="job-meta" style="margin-top:6px; color:#a89fff;">{skills_str}</div>
                <div style="margin-top:6px">{link}</div>
            </div>
            """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center; padding: 80px 20px; color: #444;">
        <div style="font-size: 3rem; margin-bottom: 16px;">📊</div>
        <div style="font-family: 'Space Mono', monospace; font-size: 1rem; color: #666;">
            Set your filters and click Analyze Market
        </div>
        <div style="font-size: 0.8rem; color: #444; margin-top: 8px;">
            Pulls live data from Tavily + intern-list.com, parsed by Claude
        </div>
    </div>
    """, unsafe_allow_html=True)