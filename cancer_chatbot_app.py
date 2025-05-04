import streamlit as st
import fitz  # PyMuPDF
import docx
import re
import os
import unicodedata
from tnm_staging import determine_tnm_stage
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

EMAIL_SENDER = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"

st.set_page_config(page_title="Cancer Staging Chatbot", layout="centered")
st.title("🤖 Cancer Staging Chatbot")
st.markdown("Upload your PET/CT report to get TNM staging, treatment guidance, and summary.")

uploaded_file = st.file_uploader("📤 Upload PET/CT Report (.pdf or .docx)", type=["pdf", "docx"])

DOWNLOAD_COUNTER_FILE = "download_count.txt"

def get_download_count():
    if os.path.exists(DOWNLOAD_COUNTER_FILE):
        with open(DOWNLOAD_COUNTER_FILE, "r") as f:
            return int(f.read().strip())
    return 0

def increment_download_count():
    count = get_download_count() + 1
    with open(DOWNLOAD_COUNTER_FILE, "w") as f:
        f.write(str(count))

def extract_text(file):
    if file.name.endswith(".pdf"):
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        return "\n".join([page.get_text() for page in pdf])
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

def extract_features(text):
    text = text.lower()
    features = {
        "cancer_type": "",
        "tumor_size_cm": 0,
        "lymph_nodes_involved": 0,
        "distant_metastasis": False,
        "liver_invasion": False,
        "tumor_depth": ""
    }
    if "gallbladder" in text:
        features["cancer_type"] = "gallbladder"
    elif "esophagus" in text:
        features["cancer_type"] = "esophageal"
    elif "breast" in text:
        features["cancer_type"] = "breast"
    elif "lung" in text:
        features["cancer_type"] = "lung"
    elif "colon" in text or "rectum" in text:
        features["cancer_type"] = "colorectal"
    elif "oral cavity" in text or "oropharynx" in text:
        features["cancer_type"] = "head and neck"
    size_match = re.search(r'(\d+(\.\d+)?)\s*(cm|mm)', text)
    if size_match:
        size_val = float(size_match.group(1))
        if "mm" in size_match.group(3):
            size_val /= 10
        features["tumor_size_cm"] = size_val
    features["lymph_nodes_involved"] = len(re.findall(r"lymph\s+node", text))
    features["distant_metastasis"] = "metastasis" in text or "metastases" in text
    features["liver_invasion"] = "liver invasion" in text or "involving segments" in text
    for keyword in ["mucosa", "submucosa", "muscularis", "subserosa", "serosa", "adventitia"]:
        if keyword in text:
            features["tumor_depth"] = keyword
            break
    return features

def generate_summary(stage, cancer_type):
    msg = f"Based on the report, this appears to be {stage} {cancer_type.capitalize()} Cancer.\n\n"
    if "IV" in stage:
        msg += "This indicates advanced disease with distant spread.\n"
    elif "III" in stage:
        msg += "This is a locally advanced stage.\n"
    elif "II" in stage:
        msg += "This is an early regional stage.\n"
    else:
        msg += "This appears to be an early stage disease.\n"
    msg += "\nPlease consult your oncologist before making any treatment decisions."
    msg += "\n\nThis is an AI-generated summary and may not reflect the complete clinical context."
    return msg

def sanitize_text(text):
    return ''.join(c for c in text if unicodedata.category(c)[0] != 'C')

def create_pdf_summary(summary_text, filename="cancer_summary.pdf"):
    pdf = FPDF()
    pdf.add_page()
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", size=12)
    except RuntimeError:
        pdf.set_font("Arial", size=12)
    clean_text = sanitize_text(summary_text)
    for line in clean_text.strip().split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)
    return filename

def send_email_with_attachment(recipient, subject, body_text, file_path):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_SENDER
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(body_text, "plain"))
    with open(file_path, "rb") as file:
        part = MIMEApplication(file.read(), Name=file_path)
        part['Content-Disposition'] = f'attachment; filename="{file_path}"'
        msg.attach(part)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

if uploaded_file:
    text = extract_text(uploaded_file)
    features = extract_features(text)
    st.write("🧪 Extracted features:", features)
    cancer_type = features.get("cancer_type", "unknown")
    staging = determine_tnm_stage(cancer_type, features)
    st.write("🧪 TNM staging result:", staging)

    explanation = generate_summary(staging['Stage'], cancer_type)

    summary_text = f"""Cancer Type: {cancer_type.capitalize()}
Stage: {staging['Stage']}
TNM: T={staging['T']}, N={staging['N']}, M={staging['M']}

Explanation:
{explanation}

Treatment:
{staging['Treatment']}

This staging and treatment plan is generated by an AI model and is not a substitute for medical advice. Please consult your oncologist.
"""

    st.subheader("🤖 Ask a Question")
    question = st.radio("What would you like to know?", ["What is my cancer stage?", "What treatment is usually given?", "Give me a full summary."])
    if question == "What is my cancer stage?":
        st.info(f"Stage: {staging['Stage']} (T={staging['T']}, N={staging['N']}, M={staging['M']})")
    elif question == "What treatment is usually given?":
        st.info(staging['Treatment'])
    else:
        st.success(explanation)

    pdf_filename = create_pdf_summary(summary_text)

    st.subheader("📄 Download Your Report")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 Download as TXT", summary_text, file_name="cancer_summary.txt")
    with col2:
        with open(pdf_filename, "rb") as f:
            st.download_button("📄 Download as PDF", f, file_name=pdf_filename, mime="application/pdf")

    st.subheader("📧 Email Your Report")
    email_input = st.text_input("Enter your email address to receive the PDF report:")
    if st.button("Send Email"):
        if email_input:
            try:
                send_email_with_attachment(
                    recipient=email_input,
                    subject="Your Report Summary",
                    body_text="Please find attached your AI-generated PET/CT summary.",
                    file_path=pdf_filename
                )
                st.success("✅ Email sent successfully!")
            except Exception as e:
                st.error(f"❌ Failed to send email: {str(e)}")
        else:
            st.warning("Please enter a valid email address.")
