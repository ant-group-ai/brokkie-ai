# brokkie_full.py
import streamlit as st
import pandas as pd
import io
import os
from fpdf import FPDF
from datetime import datetime
import base64
import random
import textwrap

st.set_page_config(page_title="Brokkie - Full 12-step Valuation Prototype", layout="wide")

# ---------- Helpers ----------

def safe_text(s: str) -> str:
    """Clean problematic Unicode for FPDF (latin1 only)."""
    if not s:
        return ""
    return (
        s.replace("—", "-")
         .replace("–", "-")
         .replace("“", '"')
         .replace("”", '"')
         .replace("’", "'")
         .replace("…", "...")
         .encode("latin1", errors="replace")
         .decode("latin1")
    )

def safe_multicell(pdf, text: str, w=None, h=6, max_chars=120, align="L"):
    """Safe wrapper for FPDF.multi_cell with width handling + wrapping."""
    txt = safe_text(text)
    if w is None:
        w = pdf.w - pdf.l_margin - pdf.r_margin
    for line in txt.split("\n"):
        for chunk in textwrap.wrap(line, max_chars, break_long_words=True):
            pdf.multi_cell(w, h, chunk, align=align)

def save_excel(df, filename="parsed_financial_data.xlsx"):
    with io.BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Financials")
        data = buffer.getvalue()
    return data

def download_link(byte_data, filename, label="Download"):
    b64 = base64.b64encode(byte_data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{label}</a>'

def generate_parsed_financials(uploaded_files):
    """Mock parsed financials generator."""
    revenue = random.randint(200_000, 3_000_000)
    cogs = int(revenue * random.uniform(0.2, 0.6))
    expenses = int(revenue * random.uniform(0.1, 0.3))
    net_income = revenue - cogs - expenses
    sde = net_income + int(expenses * 0.25)
    df = pd.DataFrame([
        {"Metric": "TTM Revenue", "Value": revenue},
        {"Metric": "COGS", "Value": cogs},
        {"Metric": "Operating Expenses", "Value": expenses},
        {"Metric": "Net Income", "Value": net_income},
        {"Metric": "SDE (est)", "Value": sde},
    ])
    return df

def generate_questions(parsed_preview):
    """Mock Q&A generator."""
    return [
        "Provide explanation for revenue seasonality (if any).",
        "List one-time expenses in the last 12 months.",
        "Explain related-party transactions (if any).",
        "Confirm recurring monthly revenue streams and churn rates.",
        "List major customer concentrations (>10% of revenue).",
        "Provide typical gross margin by service/product line."
    ]

def compute_valuation_models(financials_dict):
    revenue = financials_dict.get("TTM Revenue", 0)
    net_income = financials_dict.get("Net Income", 0)
    sde = financials_dict.get("SDE (est)", 0)
    assets = financials_dict.get("Assets", 0)
    BE = revenue * 0.8
    APEEV = max((sde * 4) + assets, BE * 0.6)
    IVB = net_income * 6
    CMA = revenue * random.uniform(0.6, 1.2)
    return {"BE": BE, "APEEV": APEEV, "IVB": IVB, "CMA": CMA}

def format_usd(x):
    try:
        return f"${int(x):,}"
    except Exception:
        return f"${x}"

def generate_final_pdf(context, filename="Final_Valuation_Report.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    page_width = pdf.w - pdf.l_margin - pdf.r_margin

    # Title
    pdf.set_font("Arial", "B", 16)
    safe_multicell(pdf, "Final Valuation Report", w=page_width, h=8)
    pdf.set_font("Arial", size=10)
    pdf.ln(4)
    safe_multicell(pdf, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", w=page_width)
    pdf.ln(6)

    # Business Summary
    pdf.set_font("Arial", "B", 12)
    safe_multicell(pdf, "Business Summary", w=page_width)
    pdf.set_font("Arial", size=10)
    safe_multicell(pdf, f"Business Name: {context.get('business_name','N/A')}", w=page_width)
    safe_multicell(pdf, f"Primary Contact: {context.get('seller_contact','N/A')}", w=page_width)
    pdf.ln(4)

    # Primary Data
    pdf.set_font("Arial", "B", 12)
    safe_multicell(pdf, "Primary Data", w=page_width)
    pdf.set_font("Arial", size=10)
    for k, v in context.get("primary_data", {}).items():
        safe_multicell(pdf, f"{k}: {format_usd(v)}", w=page_width)
    pdf.ln(4)

    # Valuation Summary
    pdf.set_font("Arial", "B", 12)
    safe_multicell(pdf, "Valuation Models Summary", w=page_width)
    pdf.set_font("Arial", size=10)
    for k, v in context.get("valuations", {}).items():
        safe_multicell(pdf, f"{k}: {format_usd(v)}", w=page_width)
    pdf.ln(6)

    # Notes
    pdf.set_font("Arial", "B", 12)
    safe_multicell(pdf, "Recommended Value & Notes", w=page_width)
    pdf.set_font("Arial", size=10)
    notes = context.get("notes", "No notes")
    safe_multicell(pdf, notes, w=page_width)

    out = pdf.output(dest="S")
    if isinstance(out, str):
        out = out.encode("latin1")
    return out

def generate_cim_pdf(context, filename="CIM_Teaser.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    page_width = pdf.w - pdf.l_margin - pdf.r_margin

    # Cover
    pdf.add_page()
    pdf.set_font("Arial", "B", 22)
    safe_multicell(pdf, f"{context.get('business_name','Company')} — Teaser", w=page_width, h=12, align="C")
    pdf.ln(6)
    pdf.set_font("Arial", size=12)
    safe_multicell(pdf, context.get("one_liner","Confidential business opportunity — summary below."), w=page_width)
    pdf.ln(6)
    safe_multicell(pdf, f"Location: {context.get('location','N/A')}", w=page_width)
    safe_multicell(pdf, f"Industry: {context.get('industry','N/A')}", w=page_width)
    revenue = context.get("primary_data", {}).get("TTM Revenue", 0)
    safe_multicell(pdf, f"Est. Revenue (TTM): {format_usd(revenue)}", w=page_width)

    # Financial snapshot
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    safe_multicell(pdf, "Financial Snapshot", w=page_width, h=8)
    pdf.set_font("Arial", size=11)
    for k, v in context.get("primary_data", {}).items():
        safe_multicell(pdf, f"{k}: {format_usd(v)}", w=page_width)

    # Highlights
    pdf.ln(4)
    pdf.set_font("Arial", "B", 12)
    safe_multicell(pdf, "Investment Highlights", w=page_width)
    pdf.set_font("Arial", size=11)
    for h in context.get("highlights", ["Recurring revenue", "Strong margins", "Scalable operations"]):
        safe_multicell(pdf, f"- {h}", w=page_width)

    # Market & comps summary
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    safe_multicell(pdf, "Market Overview & Comps", w=page_width, h=8)
    pdf.set_font("Arial", size=11)
    mr = context.get("market_research", {})
    safe_multicell(pdf, f"Industry multiples: {mr.get('Industry_multiples',{})}", w=page_width)
    comps = mr.get("RealEstate_comps", [])
    if comps:
        pdf.ln(2)
        pdf.set_font("Arial", "B", 12)
        safe_multicell(pdf, "Comps (mock):", w=page_width)
        pdf.set_font("Arial", size=11)
        for c in comps:
            safe_multicell(pdf, f"{c.get('address','N/A')} - {format_usd(c.get('value',0))}", w=page_width)

    # Buyer fit
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    safe_multicell(pdf, "Buyer Fit / Next Steps", w=page_width, h=8)
    pdf.set_font("Arial", size=11)
    safe_multicell(pdf, "This teaser is intended for qualified buyers only. Contact broker to receive full CIM and data room access.", w=page_width)
    pdf.ln(4)
    safe_multicell(pdf, f"Broker Contact: {context.get('broker_contact','broker@example.com')}", w=page_width)

    out = pdf.output(dest="S")
    if isinstance(out, str):
        out = out.encode("latin1")
    return out

# ---------- App State Init ----------
for key in ["step","uploaded_files","parsed_df","questions","answers","assets","market_research","valuations"]:
    if key not in st.session_state:
        st.session_state[key] = {} if key in ["answers","assets","valuations"] else None
if "step" not in st.session_state: st.session_state.step = 1
if "business_meta" not in st.session_state:
    st.session_state.business_meta = {"name":"Demo Business", "location":"Seattle, WA", "industry":"Service"}

# ---------- Layout ----------
st.title("Brokkie — 12-Step Valuation Workflow Prototype")
st.markdown("**Simulated / demo** — visual and operational prototype.")

# Top progress bar
progress_pct = int((st.session_state.step - 1) / 11 * 100)
st.progress(progress_pct)
st.markdown(f"**Step {st.session_state.step} of 12**")

col1, col2 = st.columns([3,1])
with col2:
    if st.button("Previous Step") and st.session_state.step > 1:
        st.session_state.step -= 1
    if st.button("Next Step") and st.session_state.step < 12:
        st.session_state.step += 1
    st.markdown("---")
    st.markdown("Quick Nav")
    for i in range(1,13):
        if st.button(f"Go to {i}"):
            st.session_state.step = i

with col1:
    step = st.session_state.step

    # ---------------- STEP 1 ----------------
    if step == 1:
        st.header("Step 1 — Upload Source Documents")
        uploaded = st.file_uploader("Upload supporting documents (multiple)", accept_multiple_files=True)
        if uploaded:
            st.session_state.uploaded_files = uploaded
            parsed = generate_parsed_financials(uploaded)
            st.session_state.parsed_df = parsed
            excel_bytes = save_excel(parsed)
            st.session_state.parsed_xlsx = excel_bytes
            st.markdown(download_link(excel_bytes, "parsed_financial_data.xlsx", "Download parsed_financial_data.xlsx"), unsafe_allow_html=True)
            st.dataframe(parsed)

    # ---------------- STEP 2 ----------------
    elif step == 2:
        st.header("Step 2 — Confirm / Correct Primary Data")
        if st.session_state.parsed_df is None:
            st.warning("Upload Step 1 first.")
        else:
            df = st.session_state.parsed_df.copy()
            edited = st.data_editor(df, num_rows="dynamic")
            if st.button("Save Confirmed Data"):
                st.session_state.parsed_df = edited
                d = {r.Metric: int(r.Value) for r in edited.itertuples()}
                st.session_state.primary_data = d
                st.success("Primary data confirmed.")

    # ---------------- STEP 3 ----------------
    elif step == 3:
        st.header("Step 3 — Generate Q&A for Seller")
        if st.session_state.parsed_df is None:
            st.warning("Upload Step 1 first.")
        else:
            qs = generate_questions(st.session_state.parsed_df)
            st.session_state.questions = qs
            for i,q in enumerate(qs):
                st.text_area(f"Q{i+1}: {q}", key=f"q{i}")
            if st.button("Export Questions PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                for i,q in enumerate(qs):
                    safe_multicell(pdf, f"Q{i+1}. {q}")
                pdf_bytes = pdf.output(dest="S").encode("latin1")
                st.markdown(download_link(pdf_bytes, "general_questions.pdf", "Download Questions PDF"), unsafe_allow_html=True)

    # ---------------- STEP 4 ----------------
    elif step == 4:
        st.header("Step 4 — Upload Answers / Fill Q&A")
        for i,q in enumerate(st.session_state.questions or []):
            ans = st.text_area(f"Answer to Q{i+1}", key=f"ans_{i}", placeholder="Type seller's answer here")
            st.session_state.answers[f"Q{i+1}"] = ans
        if st.button("Save Answers"):
            st.success("Seller answers saved.")

    # ---------------- STEP 5 ----------------
    elif step == 5:
        st.header("Step 5 — Excel Tables Adjustment")
        st.info("Download, edit offline, re-upload if needed.")
        if st.session_state.parsed_xlsx:
            st.markdown(download_link(st.session_state.parsed_xlsx, "parsed_financial_data.xlsx", "Download Parsed Excel"), unsafe_allow_html=True)
        uploaded_fix = st.file_uploader("Upload corrected Excel", type=["xlsx"])
        if uploaded_fix:
            try:
                df_fix = pd.read_excel(uploaded_fix)
                st.session_state.parsed_df = df_fix
                st.success("Corrected Excel uploaded.")
            except Exception:
                st.error("Invalid XLSX.")

    # ---------------- STEP 6 ----------------
    elif step == 6:
        st.header("Step 6 — Upload FFE / Inventory / Real Estate")
        ffe_files = st.file_uploader("FFE / Inventory / RE files", accept_multiple_files=True, key="ffe")
        if ffe_files:
            st.session_state.assets['ffe'] = [f.name for f in ffe_files]
            st.success(f"{len(ffe_files)} files uploaded.")

    # ---------------- STEP 7 ----------------
    elif step == 7:
        st.header("Step 7 — Confirm / Correct Asset Inputs")
        default_assets = {"Furniture & Fixtures": 20000, "Inventory Value": 15000, "Real Estate": 350000}
        if st.button("Load Mock Asset Extraction"):
            st.session_state.assets['extracted'] = default_assets
        if 'extracted' in st.session_state.assets:
            df_assets = pd.DataFrame(list(st.session_state.assets['extracted'].items()), columns=["Asset","Value"])
            edited_assets = st.data_editor(df_assets, num_rows="dynamic")
            if st.button("Save Asset Confirmations"):
                st.session_state.assets['confirmed'] = {r.Asset: int(r.Value) for r in edited_assets.itertuples()}
                st.success("Assets confirmed.")

    # ---------------- STEP 8 ----------------
    elif step == 8:
        st.header("Step 8 — Market Research")
        if st.button("Start Mock Market Research"):
            research = {
                "FFE_avg": 18000,
                "RealEstate_comps":[{"address":"123 Main", "value":360000},{"address":"456 Oak","value":340000}],
                "Industry_multiples":{"median_rev_multiple":0.9,"median_sde_multiple":3.5}
            }
            st.session_state.market_research = research
            st.success("Market research completed.")
        if st.session_state.market_research:
            st.write(st.session_state.market_research)

    # ---------------- STEP 9 ----------------
    elif step == 9:
        st.header("Step 9 — Inventory Upload")
        inv_file = st.file_uploader("Upload inventory CSV/XLSX", type=["csv","xlsx"])
        if inv_file:
            try:
                inv = pd.read_csv(inv_file) if inv_file.type=="text/csv" else pd.read_excel(inv_file)
                st.session_state.inventory = inv
                st.success("Inventory uploaded.")
                st.dataframe(inv.head())
            except Exception:
                st.error("Could not parse file.")

    # ---------------- STEP 10 ----------------
    elif step == 10:
        st.header("Step 10 — Real Estate Upload")
        re_file = st.file_uploader("Upload property docs", accept_multiple_files=True)
        if re_file:
            st.session_state.real_estate_files = [f.name for f in re_file]
            st.success("Real estate docs uploaded.")

    # ---------------- STEP 11 ----------------
    elif step == 11:
        st.header("Step 11 — Asset Data Preview")
        st.subheader("Primary Financials")
        st.write(st.session_state.get("primary_data", {}))
        st.subheader("Assets Confirmed")
        st.write(st.session_state.assets.get("confirmed", {}))
        st.subheader("Market Research")
        st.write(st.session_state.market_research or {})
        if st.button("Generate CIM / Teaser PDF"):
            ctx = {
                "business_name": st.session_state.business_meta.get("name","Demo Business"),
                "location": st.session_state.business_meta.get("location","N/A"),
                "industry": st.session_state.business_meta.get("industry","N/A"),
                "primary_data": st.session_state.get("primary_data",{}),
                "highlights":["Recurring revenue","Strong gross margins","Scalable ops"],
                "market_research": st.session_state.get("market_research",{}),
                "one_liner":"Confidential investment opportunity.",
                "broker_contact":"broker@example.com"
            }
            pdf_bytes = generate_cim_pdf(ctx)
            st.markdown(download_link(pdf_bytes,"CIM_Teaser.pdf","Download CIM / Teaser PDF"), unsafe_allow_html=True)

    # ---------------- STEP 12 ----------------
    elif step == 12:
        st.header("Step 12 — Valuation & Recommendations")
        if st.button("Compute Valuation Models"):
            vals = compute_valuation_models(st.session_state.get("primary_data",{}))
            st.session_state.valuations = vals
            st.success("Valuations computed.")
        st.write(st.session_state.valuations or {})
        if st.button("Generate Final Valuation Report PDF"):
            ctx = {
                "business_name": st.session_state.business_meta.get("name","Demo Business"),
                "seller_contact":"seller@example.com",
                "primary_data": st.session_state.get("primary_data",{}),
                "valuations": st.session_state.get("valuations",{}),
                "notes":"Preliminary recommendation — review with broker."
            }
            pdf_bytes = generate_final_pdf(ctx)
            st.markdown(download_link(pdf_bytes,"Final_Valuation_Report.pdf","Download Final Valuation Report"), unsafe_allow_html=True)

# ---------- Sidebar Dashboards ----------
st.sidebar.header("Analytics Dashboards")

dash_option = st.sidebar.selectbox("Select Dashboard", ["None","BrokerIQ Dashboard","DealReady"])
if dash_option == "BrokerIQ Dashboard":
    st.sidebar.markdown("**BrokerIQ Mock Dashboard**")
    # Mock deals table
    deals = pd.DataFrame([
        {"Deal":f"Deal {i+1}","Status":random.choice(["Active","Pending","Closed"]),
         "Value":random.randint(100_000,2_000_000)} for i in range(10)
    ])
    st.subheader("Deals Overview")
    st.dataframe(deals)
    # Charts
    st.subheader("Deals Value Distribution")
    st.bar_chart(deals.set_index("Deal")["Value"])
    st.subheader("Deals by Status")
    st.bar_chart(deals['Status'].value_counts())

elif dash_option == "DealReady":
    st.sidebar.markdown("**DealReady Mock Tool**")
    st.subheader("DealReady Financial Preview")
    revenue_input = st.number_input("Enter TTM Revenue", 0, 5_000_000, value=500_000, step=10_000)
    expenses_input = st.number_input("Operating Expenses", 0, 2_000_000, value=150_000, step=5_000)
    sde_calc = revenue_input - expenses_input + int(expenses_input*0.25)
    st.metric("Estimated SDE", f"${sde_calc:,}")
    st.subheader("DealReady Charts")
    st.bar_chart(pd.DataFrame({"Revenue":[revenue_input],"Expenses":[expenses_input]}))
