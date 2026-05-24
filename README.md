![Dashboard](<img width="1901" height="944" alt="JobMarketAnalyzer png" src="https://github.com/user-attachments/assets/19df68ea-7b17-4d77-ad37-6480aea11eef" />
<img width="1901" height="944" alt="JobMarketAnalyzer png" src="https://github.com/user-attachments/assets/19df68ea-7b17-4d77-ad37-6480aea11eef" />


# Job Market Analyzer

Real-time intelligence on DS/AI internship trends, powered by the Claude API.

## What it does

Fetches live job listings from the web via Tavily and intern-list.com, then uses Claude to extract and normalize structured data from raw listing text. Results are displayed in an interactive Streamlit dashboard.

## Features

- Live job listing fetching from LinkedIn, Indeed, Lever, Greenhouse, and intern-list.com
- Claude-powered skill extraction from unstructured job descriptions
- Filters by role type, location, and experience level
- Visualizations for top skills, role breakdown, remote vs on-site, and hiring companies

## Tech Stack

Python · Streamlit · Anthropic API · Tavily · BeautifulSoup · Plotly · Pandas

## Setup

```bash
pip install streamlit anthropic tavily-python beautifulsoup4 plotly pandas requests
streamlit run projectApp.py
```

Add your Anthropic and Tavily API keys in the sidebar when the app launches.
