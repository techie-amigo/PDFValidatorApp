# streamlit_pdf_validator.py
import streamlit as st
import pdfplumber
import re
import pandas as pd
from datetime import datetime

# ---------------- PDF Patterns ----------------
reference_patterns = {
    "L Number": r"L Number:\s*-\s*(\d+)",
    "N": r"N:\s*-\s*([A-Za-z ]+)",
    "C Number": r"C number:\s*-\s*([\d-]+)",
    "F Date": r"F date:\s*-\s*([\d/]+)",
    "M Date": r"M Date:\s*-\s*([\d/]+)",
    "A Date": r"A date:\s*-\s*([\d/]+)",
    "P P Date": r"P P date:\s*-\s*([\d/]+)",
    "S": r"S:\s*-\s*([\d.]+)"
}

# ---------------- PDF Processing ----------------
def extract_reference_from_page1(text):
    reference = {}
    for field, pat in reference_patterns.items():
        match = re.search(pat, text)
        reference[field] = match.group(1) if match else ""
    return reference

def validate_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        page1_text = pdf.pages[0].extract_text() or ""
        reference = extract_reference_from_page1(page1_text)
        results = []

        for field, ref_value in reference.items():
            match_pages = []
            not_match_pages = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if ref_value and ref_value in text:
                    match_pages.append(i + 1)
                else:
                    not_match_pages.append(i + 1)

            results.append({
                "Field": field,
                "Reference": ref_value,
                "Match Pages": ",".join(map(str, match_pages)) if match_pages else "",
                "Not Match Pages": ",".join(map(str, not_match_pages)) if not_match_pages else ""
            })
    return results

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="Yuvaraj Validator", layout="wide")
st.title("Yuvaraj")

pdf_file = st.file_uploader("Upload PDF File", type=["pdf"])

if pdf_file:
    st.success("PDF uploaded successfully!")

    if st.button("Validate PDF"):
        with st.spinner("Validating..."):
            results = validate_pdf(pdf_file)
            df = pd.DataFrame(results)

            # Color styling
            def highlight_cells(val, col):
                if col == "Match Pages" and val:
                    return 'background-color: #c4ffcf; Color: black'  # green
                elif col == "Not Match Pages" and val:
                    return 'background-color: #ffc9c9; color: black'  # red
                return ''

            styled_df = df.style.applymap(lambda v: 'background-color: #c4ffcf; color: black', subset=['Match Pages']) \
                                .applymap(lambda v: 'background-color: #ffc9c9; color: black', subset=['Not Match Pages'])

            st.subheader("Validation Results")
            st.dataframe(styled_df, use_container_width=True)

            # Export buttons
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"Validation_Report_{timestamp}.xlsx"
            df.to_excel(excel_filename, index=False)

            st.download_button(
                label="Download Excel Report",
                data=open(excel_filename, "rb").read(),
                file_name=excel_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
