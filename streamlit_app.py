import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Meta Ad Spy", layout="wide")

st.title("🎯 Competitor Ad Intelligence")

# Sidebar settings & inputs
with st.sidebar:
    st.header("Search Filters")
    api_key = st.text_input("ScrapeCreators API Key", type="password")
    query = st.text_input("Keyword", value="ndis consumables")
    country = st.selectbox("Country", ["AU", "US", "GB", "NZ", "CA"], index=0)
    sort_by = st.selectbox("Sort Order", ["total_impressions", "most_recent"], index=0)
    search_btn = st.button("Search Ads", type="primary")

if search_btn:
    if not api_key:
        st.error("Please enter your ScrapeCreators API Key.")
    else:
        url = "https://api.scrapecreators.com/v1/facebook/adLibrary/search/ads"
        headers = {"x-api-key": api_key}
        params = {
            "query": query,
            "country": country,
            "status": "ACTIVE",
            "sort_by": sort_by
        }

        with st.spinner("Fetching ads from Meta Ad Library..."):
            res = requests.get(url, headers=headers, params=params)

        if res.status_code != 200:
            st.error(f"API Error ({res.status_code}): {res.text}")
        else:
            data = res.json()
            ads = data.get("searchResults") or data.get("items") or data.get("ads") or []
            st.caption(f"Credits remaining: {data.get('credits_remaining', 'N/A')}")

            rows = []
            for ad in ads:
                page_name = ad.get("page_name") or ad.get("advertiser_name") or "Unknown"

                # Calculate days active
                start_val = ad.get("start_date")
                days_active = 0
                if start_val:
                    try:
                        if isinstance(start_val, (int, float)):
                            start_dt = datetime.fromtimestamp(start_val)
                        else:
                            clean_d = str(start_val).split("T")[0]
                            start_dt = datetime.strptime(clean_d, "%Y-%m-%d")
                        days_active = (datetime.now() - start_dt).days
                    except Exception:
                        days_active = 0

                snapshot = ad.get("snapshot") or {}
                body_obj = snapshot.get("body")
                if isinstance(body_obj, dict):
                    body = body_obj.get("text") or body_obj.get("markup", {}).get("__html", "")
                elif isinstance(body_obj, str):
                    body = body_obj
                else:
                    body = snapshot.get("caption") or snapshot.get("title") or ""

                hook = body.strip().split("\n")[0][:120] if body else "No text body"
                cta = snapshot.get("cta_text") or snapshot.get("cta_type") or "Learn More"
                archive_id = ad.get("ad_archive_id") or ad.get("id")
                ad_url = f"https://www.facebook.com/ads/library/?id={archive_id}" if archive_id else ""

                rows.append({
                    "Advertiser": page_name,
                    "Days Active": days_active,
                    "Opening Hook": hook,
                    "CTA": cta,
                    "Ad Link": ad_url,
                    "Full Copy": body
                })

            df = pd.DataFrame(rows)
            if not df.empty:
                df = df.sort_values(by="Days Active", ascending=False)
                
                c1, c2 = st.columns(2)
                c1.metric("Total Ads Found", len(df))
                c2.metric("Longest Active Run", f"{df['Days Active'].max()} days")

                st.dataframe(
                    df[["Advertiser", "Days Active", "Opening Hook", "CTA", "Ad Link"]],
                    column_config={"Ad Link": st.column_config.LinkColumn("View on Meta")},
                    use_container_width=True
                )

                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv, f"{query}_ads.csv", "text/csv")
            else:
                st.warning("No ads found. Try broader keywords.")
