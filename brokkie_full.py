# brokkie_full.py
import streamlit as st
import pandas as pd
import io
import os
from fpdf import FPDF
from datetime import datetime
import base64
import random

st.set_page_config(page_title="Brokkie - Full 12-step Valuation Prototype", layout="wide")

# ---------- Helpers ----------
def safe_text(s):
    if not s:
        return ""
    return (s.replace("—", "-")
             .replace("–", "-")
             .replace("“", '"')
             .replace("”", '"')
             .replace("’", "'")
             .replace("…", "...")
             .encode("latin1", errors="replace").decode("latin1"))
# Safe wrapper for multi_cell to avoid FPDF errors
def safe_multicell(pdf, text, w=0, h=6):
    txt = safe_text(text)
  import textwrap

# Helper to safely split long text into chunks for FPDF
def safe_multicell(pdf, text, w=0, h=6, max_chars=100):
    for line in text.split("\n"):
        for chunk in textwrap.wrap(safe_text(line), max_chars):
            pdf.multi_cell(w, h, chunk)

# Example usage:
txt = "Very long text that might break FPDF rendering if not split properly..."
safe_multicell(pdf, txt)


def save_excel(df, filename="parsed_financial_data.xlsx"):
    with io.BytesIO() as buffer:
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Financials")
        data = buffer.getvalue()
    return data

def download_link(byte_data, filename, label="Download"):
    b64 = base64.b64encode(byte_data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{label}</a>'
    return href

def generate_parsed_financials(uploaded_files):
    # Create a mocked parsed_financial_data.xlsx based on uploaded files
    revenue = random.randint(200000, 3000000)
    cogs = int(revenue * random.uniform(0.2, 0.6))
    expenses = int(revenue * random.uniform(0.1, 0.3))
    net_income = revenue - cogs - expenses
    sde = net_income + int(expenses * 0.25)  # simplified add-backs
    df = pd.DataFrame([{
        "Metric": "TTM Revenue",
        "Value": revenue
    }, {
        "Metric": "COGS",
        "Value": cogs
    }, {
        "Metric": "Operating Expenses",
        "Value": expenses
    }, {
        "Metric": "Net Income",
        "Value": net_income
    }, {
        "Metric": "SDE (est)",
        "Value": sde
    }])
    return df

def generate_questions(parsed_preview):
    # Mocked smart Q&A generator
    q = [
        "Provide explanation for revenue seasonality (if any).",
        "List one-time expenses in the last 12 months.",
        "Explain related-party transactions (if any).",
        "Confirm recurring monthly revenue streams and churn rates.",
        "List major customer concentrations (>10% of revenue).",
        "Provide typical gross margin by service/product line."
    ]
    return q

def compute_valuation_models(financials_dict):
    revenue = financials_dict.get("TTM Revenue", 0)
    net_income = financials_dict.get("Net Income", 0)
    sde = financials_dict.get("SDE (est)", 0)
    BE = revenue * 0.8
    APEEV = max((sde * 4) + financials_dict.get("Assets", 0), BE * 0.6)
    IVB = net_income * 6
    CMA = revenue * random.uniform(0.6, 1.2)
    return {"BE": BE, "APEEV": APEEV, "IVB": IVB, "CMA": CMA}

def format_usd(x):
    try:
        return f"${int(x):,}"
    except:
        return f"${x}"

def generate_final_pdf(context, filename="Final_Valuation_Report.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 8, safe_text("Final Valuation Report"), ln=True)
    pdf.set_font("Arial", size=10)
    pdf.ln(4)
    pdf.cell(0, 6, safe_text(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"), ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, safe_text("Business Summary"), ln=True)
    pdf.set_font("Arial", size=10)
    safe_multicell(pdf, f"Business Name: {context.get('business_name','N/A')}")
    safe_multicell(pdf, f"Primary Contact: {context.get('seller_contact','N/A')}")
    pdf.ln(4)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, safe_text("Primary Data"), ln=True)
    pdf.set_font("Arial", size=10)
    for k,v in context.get("primary_data", {}).items():
        pdf.cell(0,6, safe_text(f"{k}: {format_usd(v)}"), ln=True)
    pdf.ln(4)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0,6, safe_text("Valuation Models Summary"), ln=True)
    pdf.set_font("Arial", size=10)
    for k,v in context.get("valuations", {}).items():
        pdf.cell(0,6, safe_text(f"{k}: {format_usd(v)}"), ln=True)
    pdf.ln(6)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0,6, safe_text("Recommended Value & Notes"), ln=True)
    pdf.set_font("Arial", size=10)
    safe_multicell(pdf, context.get("notes","No notes"))
    return pdf.output(dest="S").encode("latin1")

def generate_cim_pdf(context, filename="CIM_Teaser.pdf"):
    # Multi-page CIM-style teaser (mock)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)

    # Cover / Teaser page
    pdf.add_page()
    pdf.set_font("Arial", "B", 22)
    pdf.cell(0, 12, safe_text(f"{context.get('business_name','Company')} — Teaser"), ln=True, align="C")
    pdf.ln(6)
    pdf.set_font("Arial", size=12)
    safe_multicell(pdf, context.get("one_liner","Confidential business opportunity — summary below."))
    pdf.ln(6)
    pdf.cell(0, 6, safe_text(f"Location: {context.get('location','N/A')}"), ln=True)
    pdf.cell(0, 6, safe_text(f"Industry: {context.get('industry','N/A')}"), ln=True)
    pdf.cell(0, 6, safe_text(f"Est. Revenue (TTM): {format_usd(context.get('primary_data',{}).get('TTM Revenue',0))}"), ln=True)

    # Financial snapshot
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, safe_text("Financial Snapshot"), ln=True)
    pdf.set_font("Arial", size=11)
    for k,v in context.get("primary_data", {}).items():
        pdf.cell(0,6, safe_text(f"{k}: {format_usd(v)}"), ln=True)

    # Highlights
    pdf.ln(4)
    pdf.set_font("Arial","B",12)
    pdf.cell(0,6,safe_text("Investment Highlights"), ln=True)
    pdf.set_font("Arial", size=11)
    for h in context.get("highlights", ["Recurring revenue", "Strong margins", "Scalable operations"]):
       safe_multicell(pdf, f"- {h}")

    # Market & comps summary
    pdf.add_page()
    pdf.set_font("Arial","B",14)
    pdf.cell(0,8,safe_text("Market Overview & Comps"), ln=True)
    pdf.set_font("Arial", size=11)
    mr = context.get("market_research", {})
    safe_multicell(pdf, f"Industry multiples: {mr.get('Industry_multiples',{})}")
    comps = mr.get("RealEstate_comps", [])
    pdf.ln(2)
    if comps:
        pdf.set_font("Arial","B",12)
        pdf.cell(0,6,safe_text("Comps (mock):"), ln=True)
        pdf.set_font("Arial", size=11)
        for c in comps:
            pdf.cell(0,6, safe_text(f"{c.get('address','N/A')} - {format_usd(c.get('value',0))}"), ln=True)

    # Buyer fit and contact
    pdf.add_page()
    pdf.set_font("Arial","B",14)
    pdf.cell(0,8,safe_text("Buyer Fit / Next Steps"), ln=True)
    pdf.set_font("Arial", size=11)
    safe_multicell(pdf, "This teaser is intended for qualified buyers only. Contact broker to receive full CIM and data room access.")
    pdf.ln(4)
    pdf.cell(0,6, safe_text(f"Broker Contact: {context.get('broker_contact','broker@example.com')}"), ln=True)

    return pdf.output(dest="S").encode("latin1")

# ---------- App state init ----------
if "step" not in st.session_state:
    st.session_state.step = 1
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "parsed_df" not in st.session_state:
    st.session_state.parsed_df = None
if "questions" not in st.session_state:
    st.session_state.questions = []
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "assets" not in st.session_state:
    st.session_state.assets = {}
if "market_research" not in st.session_state:
    st.session_state.market_research = None
if "valuations" not in st.session_state:
    st.session_state.valuations = {}
if "business_meta" not in st.session_state:
    st.session_state.business_meta = {"name":"Demo Business", "location":"Seattle, WA", "industry":"Service"}

# ---------- Layout ----------
st.title("Brokkie — 12-Step Valuation Workflow Prototype")
st.markdown("**Simulated / demo** — visual and operational prototype to showcase the future tool's power.")

# Global top progress bar (12 steps)
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

    # ---------------- STEP 1: Upload Source Documents ----------------
    if step == 1:
        st.header("Step 1 — Upload Source Documents")
        st.info("Required: Tax Returns, Profit & Loss (TTM/YTD), Monthly DORs. Upload any files to simulate parsing.")
        uploaded = st.file_uploader("Upload supporting documents (multiple)", accept_multiple_files=True)
        if uploaded:
            st.session_state.uploaded_files = uploaded
            st.success(f"{len(uploaded)} files uploaded.")
            parsed = generate_parsed_financials(uploaded)
            st.session_state.parsed_df = parsed
            excel_bytes = save_excel(parsed)
            st.session_state.parsed_xlsx = excel_bytes
            st.markdown(download_link(excel_bytes, "parsed_financial_data.xlsx", "Download parsed_financial_data.xlsx"), unsafe_allow_html=True)
            st.dataframe(parsed)

    # ---------------- STEP 2: Confirm / Correct Primary Data ----------------
    elif step == 2:
        st.header("Step 2 — Confirm / Correct Primary Data")
        if st.session_state.parsed_df is None:
            st.warning("No parsed data yet. Please complete Step 1 first (upload documents).")
        else:
            st.write("Preview parsed financials:")
            df = st.session_state.parsed_df.copy()
            edited = st.data_editor(df, num_rows="dynamic")
            if st.button("Save Confirmed Data"):
                st.session_state.parsed_df = edited
                st.success("Primary data confirmed and saved.")
                d = {r.Metric: int(r.Value) for r in edited.itertuples()}
                st.session_state.primary_data = d

    # ---------------- STEP 3: Generate Q&A for Seller ----------------
    elif step == 3:
        st.header("Step 3 — Generate Q&A for Seller")
        if st.session_state.parsed_df is None:
            st.warning("Please upload parsed financials in Step 1.")
        else:
            st.write("Auto-generating Q&A based on parsed data...")
            qs = generate_questions(st.session_state.parsed_df)
            st.session_state.questions = qs
            for i,q in enumerate(qs):
                st.markdown(f"**Q{i+1}.** {q}")
            if st.button("Export Questions (PDF)"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(0,6, "Seller Q&A", ln=True)
                pdf.ln(4)
                for i,q in enumerate(qs):
                   safe_multicell(pdf, f"Q{i+1}. {q}")
                pdf_bytes = pdf.output(dest="S").encode("latin1")
                st.markdown(download_link(pdf_bytes, "general_questions.pdf", "Download general_questions.pdf"), unsafe_allow_html=True)

    # ---------------- STEP 4: Upload Answers from Seller ----------------
    elif step == 4:
        st.header("Step 4 — Upload Seller Answers / Fill Q&A")
        st.write("Paste answers or upload a text file containing answers.")
        for i,q in enumerate(st.session_state.questions):
            ans = st.text_area(f"Answer to Q{i+1}", key=f"ans_{i}", placeholder="Type seller's answer or paste content here")
            st.session_state.answers[f"Q{i+1}"] = ans
        if st.button("Save Answers"):
            st.success("Saved seller answers.")

    # ---------------- STEP 5: Excel Tables Adjustment (Manual) ----------------
    elif step == 5:
        st.header("Step 5 — Excel Tables Adjustment (Manual)")
        st.info("Download parsed Excel, edit offline, and re-upload if needed.")
        if "parsed_xlsx" in st.session_state:
            st.markdown(download_link(st.session_state.parsed_xlsx, "parsed_financial_data.xlsx", "Download parsed_financial_data.xlsx"), unsafe_allow_html=True)
        uploaded_fix = st.file_uploader("Upload corrected Excel (optional)", type=["xlsx"])
        if uploaded_fix:
            try:
                df_fix = pd.read_excel(uploaded_fix)
                st.session_state.parsed_df = df_fix
                st.success("Corrected Excel uploaded and accepted.")
            except Exception as e:
                st.error("Could not read uploaded file. Make sure it's a valid XLSX.")

    # ---------------- STEP 6: Upload FFE / Inventory / Real Estate ----------------
    elif step == 6:
        st.header("Step 6 — Upload FFE / Inventory / Real Estate Docs")
        st.info("Upload photos or documents for Furniture, Fixtures & Equipment, Inventory listing, Real Estate docs.")
        ffe_files = st.file_uploader("FFE / Inventory / Real Estate files (multiple)", accept_multiple_files=True, key="ffe")
        if ffe_files:
            st.session_state.assets['ffe'] = [f.name for f in ffe_files]
            st.success(f"Uploaded {len(ffe_files)} asset files.")
            st.write(st.session_state.assets['ffe'])

    # ---------------- STEP 7: Confirm / Correct Asset Inputs ----------------
    elif step == 7:
        st.header("Step 7 — Confirm / Correct Asset Inputs")
        st.write("Review extracted asset info (mocked).")
        default_assets = {"Furniture & Fixtures": 20000, "Inventory Value": 15000, "Real Estate (land+building)": 350000}
        if st.button("Load Mock Asset Extraction"):
            st.session_state.assets['extracted'] = default_assets
        if 'extracted' in st.session_state.assets:
            df_assets = pd.DataFrame(list(st.session_state.assets['extracted'].items()), columns=["Asset","Value"])
            edited_assets = st.data_editor(df_assets, num_rows="dynamic")
            if st.button("Save Asset Confirmations"):
                st.session_state.assets['confirmed'] = {r.Asset: int(r.Value) for r in edited_assets.itertuples()}
                st.success("Asset inputs confirmed.")

    # ---------------- STEP 8: Market Research ----------------
    elif step == 8:
        st.header("Step 8 — Market Research")
        st.info("Run automated (mock) research for FFE, Real Estate comps, and Industry CMAs.")
        if st.button("Start Mock Market Research"):
            research = {
                "FFE_avg": 18000,
                "RealEstate_comps": [{"address":"123 Main", "value": 360000}, {"address":"456 Oak", "value": 340000}],
                "Industry_multiples": {"median_rev_multiple": 0.9, "median_sde_multiple": 3.5}
            }
            st.session_state.market_research = research
            st.success("Market research completed (mock).")
        if st.session_state.market_research:
            st.write(st.session_state.market_research)

    # ---------------- STEP 9: Inventory ----------------
    elif step == 9:
        st.header("Step 9 — Inventory Upload")
        inv_file = st.file_uploader("Upload inventory CSV or XLSX (optional)", type=["csv","xlsx"])
        if inv_file:
            try:
                if inv_file.type == "text/csv":
                    inv = pd.read_csv(inv_file)
                else:
                    inv = pd.read_excel(inv_file)
                st.session_state.inventory = inv
                st.success("Inventory uploaded.")
                st.dataframe(inv.head())
            except Exception as e:
                st.error("Could not parse inventory file.")

    # ---------------- STEP 10: Real Estate ----------------
    elif step == 10:
        st.header("Step 10 — Real Estate Upload")
        re_file = st.file_uploader("Upload property docs (deeds, appraisal) (optional)", accept_multiple_files=True)
        if re_file:
            st.session_state.real_estate_files = [f.name for f in re_file]
            st.success("Real estate docs uploaded.")
            st.write(st.session_state.real_estate_files)

    # ---------------- STEP 11: Asset Data Preview ----------------
    elif step == 11:
        st.header("Step 11 — Asset Data Preview")
        st.write("Consolidated preview of asset extraction results.")
        primary = st.session_state.get("primary_data", {})
        assets_confirmed = st.session_state.assets.get("confirmed", {})
        market = st.session_state.market_research or {}
        st.subheader("Primary Financials")
        st.write(primary)
        st.subheader("Assets Confirmed")
        st.write(assets_confirmed)
        st.subheader("Market Research Summary")
        st.write(market)
        if st.button("Generate Mock Teaser / CIM (Teaser PDF)"):
            ctx = {
                "business_name": st.session_state.business_meta.get("name","Demo Business"),
                "location": st.session_state.business_meta.get("location","N/A"),
                "industry": st.session_state.business_meta.get("industry","N/A"),
                "primary_data": st.session_state.get("primary_data", {}),
                "market_research": st.session_state.market_research or {},
                "highlights": ["Recurring contracts", "High margin services", "Low customer churn"],
                "one_liner": "Confidential business opportunity — summary available upon ND.",
                "broker_contact": "broker@antlabs.example"
            }
            cim_bytes = generate_cim_pdf(ctx)
            st.markdown(download_link(cim_bytes, "CIM_Teaser.pdf", "Download CIM / Teaser (mock)"), unsafe_allow_html=True)
            st.success("CIM / Teaser generated (mock).")

    # ---------------- STEP 12: Research Results & Valuation Models ----------------
    elif step == 12:
        st.header("Step 12 — Valuation Models & Final Report")
        st.info("Select valuation models to run, review model outputs, validate and generate final report.")
        primary = st.session_state.get("primary_data")
        if not primary:
            st.warning("Primary financial data is missing. Please confirm parsed data in Step 2.")
        else:
            assets_confirmed = st.session_state.assets.get("confirmed", {})
            primary_with_assets = primary.copy()
            primary_with_assets.update(assets_confirmed)
            st.subheader("Valuation Models")
            run_BE = st.checkbox("Basic Evaluation (BE)", value=True)
            run_APEEV = st.checkbox("Assets + Excess Earnings (APEEV)", value=True)
            run_IVB = st.checkbox("Investment Value of Business (IVB)", value=True)
            run_CMA = st.checkbox("Comparative Market Analysis (CMA)", value=True)

            valuations = compute_valuation_models(primary_with_assets)
            selected = {}
            if run_BE: selected['BE'] = valuations['BE']
            if run_APEEV: selected['APEEV'] = valuations['APEEV']
            if run_IVB: selected['IVB'] = valuations['IVB']
            if run_CMA: selected['CMA'] = valuations['CMA']

            st.subheader("Model Outputs (mock)")
            for k,v in selected.items():
                st.metric(k, format_usd(v))

            st.subheader("Model Validation")
            adjustments = {}
            for k,v in selected.items():
                adj = st.number_input(f"Adjusted {k} value", value=int(v))
                adjustments[k] = adj
            if st.button("Confirm Models & Generate Final Report"):
                context = {
                    "business_name": st.session_state.business_meta.get("name","Demo Business"),
                    "seller_contact": st.session_state.business_meta.get("contact","Seller"),
                    "primary_data": primary_with_assets,
                    "valuations": adjustments,
                    "notes": st.text_area("Notes / Recommended Value and rationale", value="Selected recommended value based on weighted median of models.")
                }
                pdf_bytes = generate_final_pdf(context)
                st.session_state.final_pdf = pdf_bytes
                st.success("Final report generated.")
                st.markdown(download_link(pdf_bytes, "Final_Valuation_Report.pdf", "Download Final_Valuation_Report.pdf"), unsafe_allow_html=True)

# ---------------- TOP NAV: BrokerIQ Dashboard & DealReady ----------------
st.sidebar.markdown("---")
view = st.sidebar.selectbox("Quick View", ["Workflow", "BrokerIQ Dashboard", "DealReady (SMB)"])

if view == "BrokerIQ Dashboard":
    st.header("BrokerIQ — Dashboard (Demo)")
    demo_deals = pd.DataFrame([
        {"Business":"Auto Paving", "Valuation":250000, "Matched Buyers":3, "Status":"Negotiation"},
        {"Business":"Coffee Chain", "Valuation":120000, "Matched Buyers":0, "Status":"Data Collection"},
        {"Business":"IT Services", "Valuation":500000, "Matched Buyers":2, "Status":"Marketing"}
    ])
    st.table(demo_deals)
    st.subheader("Deal Analytics (mock)")
    st.line_chart({"Deal Value":[250000,120000,500000],"Matched Buyers":[3,0,2]})
    if st.button("Export Portfolio Report (Demo)"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial","B",14)
        pdf.cell(0,6,"BrokerIQ Portfolio Report (Demo)", ln=True)
        pdf.ln(4)
        for i,r in demo_deals.iterrows():
            pdf.set_font("Arial","",11)
           safe_multicell(pdf,f"{r['Business']} — Valuation: ${int(r['Valuation']):,} — Status: {r['Status']} — Matched Buyers: {r['Matched Buyers']}")

        st.markdown(download_link(pdf.output(dest="S").encode("latin1"), "BrokerIQ_Portfolio_Report.pdf", "Download Portfolio Report"), unsafe_allow_html=True)

elif view == "DealReady (SMB)":
    st.header("DealReady — SMB Owner Tool (Demo)")
    st.write("Enter your business data to get an instant estimate and exit-prep suggestions.")
    name = st.text_input("Business Name", value="Demo SMB")
    rev = st.number_input("Annual Revenue ($)", value=300000)
    profit = st.number_input("Net Profit ($)", value=45000)
    assets_val = st.number_input("Total Assets ($)", value=20000)
    if st.button("Estimate Value"):
        est = int(rev * 0.8 + profit * 3 + assets_val * 0.5)
        st.metric("Estimated Business Value", f"${est:,}")
        st.markdown("**Exit Prep Suggestions:**")
        st.markdown("- Improve recurring revenue share\n- Formalize contracts & processes\n- Clean up one-time expenses and records\n- Prepare professional marketing materials")
        owner_ctx = {
            "business_name": name,
            "primary_data": {"TTM Revenue": rev, "Net Income": profit, "Assets": assets_val},
            "valuations": {"QuickEstimate": est},
            "notes": "Owner-facing simplified valuation and exit prep checklist."
        }
        pdf_bytes = generate_final_pdf(owner_ctx)
        st.markdown(download_link(pdf_bytes, f"{name}_DealReady_Report.pdf", "Download Owner Report"), unsafe_allow_html=True)

# Footer quick help
st.sidebar.markdown("---")
st.sidebar.markdown("Prototype by Ruslan — Simulated outputs. Connect AI models / parsers to replace mock computations.")
