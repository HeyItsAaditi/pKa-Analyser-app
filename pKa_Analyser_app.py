import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import datetime
import base64
import io
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Updated CSS: White background, light colors, and colorful text/elements
st.markdown("""
<style>
    /* White main background */
    .main {
        background-color: #ffffff !important;
        color: #000000;  /* Black text for readability */
        padding: 1.5rem 1rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Light gray containers for sections (changed from light purple to decent light gray) */
    .block-container {
        background: #f5f5f5;  /* Light gray */
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 3px 12px rgba(100, 80, 180, 0.1);
        margin-bottom: 2rem;
    }

    /* Title: Purple */
    h1 {
        color: #6a1b9a;  /* Purple */
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
    }

    /* Section headers: Blue */
    h2, h3 {
        color: #1976d2;  /* Blue */
        margin-top: 1.5rem;
        margin-bottom: 0.7rem;
    }

    /* Input boxes: Light blue border, black text */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>div[role="combobox"] {
        border-radius: 6px !important;
        border: 2px solid #602882 !important;  /* purple border */
        box-shadow: none !important;
        background-color: #ffffff !important;
        padding: 8px;
        color: #000000;  /* Black text */
        font-weight: 500;
    }

    /* Buttons: Purple gradient */
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(45deg, #7e57c2, #ba68c8) !important; /* Purple */
        color: white !important;
        font-weight: 600;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 24px !important;
        cursor: pointer;
        transition: background 0.3s ease;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background: linear-gradient(45deg, #5e35b1, #9c27b0) !important; /* Darker purple */
    }

    /* Success messages: Green */
    .stSuccess {
        color: #388e3c !important; /* Green */
        font-weight: 600;
    }

    /* Error messages: Red */
    .stError {
        color: #d32f2f !important; /* Red */
        font-weight: 600;
    }

    /* Tables: White bg, blue borders, purple headers */
    table {
        border-collapse: collapse !important;
        width: 100% !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: #ffffff;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    th, td {
        border: 1px solid #42a5f5 !important;  /* Blue border */
        padding: 10px !important;
        text-align: center !important;
        color: #000000 !important;  /* Black text */
    }
    th {
        background-color: #ba68c8 !important; /* Purple header */
        color: #ffffff !important;  /* White text on purple */
    }

    /* Markdown text: Blue for bold/emphasis */
    .stMarkdown strong {
        color: #1976d2 !important;  /* Blue for bold text */
    }
</style>
""", unsafe_allow_html=True)

if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'volumes' not in st.session_state:
    st.session_state.volumes = []
if 'pHs' not in st.session_state:
    st.session_state.pHs = []
if 'V_eq' not in st.session_state:
    st.session_state.V_eq = None
if 'V_half' not in st.session_state:
    st.session_state.V_half = None
if 'pKa' not in st.session_state:
    st.session_state.pKa = None
if 'fig1' not in st.session_state:
    st.session_state.fig1 = None
if 'fig2' not in st.session_state:
    st.session_state.fig2 = None

def compute_derivative(volumes, pHs):
    # Calculate change in pH divided by change in volume (0.5 for each step)
    return np.diff(pHs) / np.diff(volumes)

def find_equivalence_point(volumes, pHs):
    dpHdV = compute_derivative(volumes, pHs)
    peaks, _ = find_peaks(dpHdV, prominence=np.max(dpHdV) * 0.5)  # Higher prominence for sharper, fewer peaks
    if len(peaks) == 0:
        st.error("No clear equivalence point found. Check data.")
        return None, None
    # Select the peak with the maximum dpHdV value for a single sharp peak
    max_peak_index = np.argmax(dpHdV[peaks])
    eq_index = peaks[max_peak_index]
    V_eq = volumes[eq_index + 1]  # Since dpHdV is at intervals, equivalence at end of interval
    return V_eq, eq_index + 1

def interpolate_pH(volumes, pHs, target_volume):
    return np.interp(target_volume, volumes, pHs)

def plot_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return img_base64

def plot_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    return buf

def generate_pdf(details, volumes, pHs, V_eq, V_half, pKa, fig1, fig2, comparison_text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    # Page 1: Details
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 100, "Interpretation of pKa values of a cooling fluid Report")
    c.setFont("Helvetica", 12)
    y = height - 150
    for key, value in details.items():
        c.drawString(100, y, f"{key}: {value}")
        y -= 20
    c.showPage()
    # Page 2: Input Data with Bordered Table
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 100, "Input Data")
    c.setFont("Helvetica", 12)
    y = height - 150
    # Table headers
    c.drawString(100, y, "Volume (mL)")
    c.drawString(200, y, "pH")
    # Draw borders for headers
    c.line(90, y-5, 90, y+15)  # Left vertical for Volume
    c.line(90, y-5, 180, y-5)  # Bottom horizontal for Volume
    c.line(180, y-5, 180, y+15)  # Right vertical for Volume
    c.line(90, y+15, 180, y+15)  # Top horizontal for Volume
    c.line(190, y-5, 190, y+15)  # Left vertical for pH
    c.line(190, y-5, 280, y-5)  # Bottom horizontal for pH
    c.line(280, y-5, 280, y+15)  # Right vertical for pH
    c.line(190, y+15, 280, y+15)  # Top horizontal for pH
    y -= 20
    for v, p in zip(volumes, pHs):
        c.drawString(100, y, f"{v:.2f}")
        c.drawString(200, y, f"{p:.2f}")
        # Draw borders for each row
        c.line(90, y-5, 90, y+15)  # Left vertical for Volume
        c.line(90, y-5, 180, y-5)  # Bottom horizontal for Volume
        c.line(180, y-5, 180, y+15)  # Right vertical for Volume
        c.line(90, y+15, 180, y+15)  # Top horizontal for Volume
        c.line(190, y-5, 190, y+15)  # Left vertical for pH
        c.line(190, y-5, 280, y-5)  # Bottom horizontal for pH
        c.line(280, y-5, 280, y+15)  # Right vertical for pH
        c.line(190, y+15, 280, y+15)  # Top horizontal for pH
        y -= 20
        if y < 100:
            c.showPage()
            y = height - 100
    c.showPage()
    # Page 3: Both Graphs on One Page
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 100, "Graphs")
    img1_buf = plot_to_bytes(fig1)
    c.drawImage(ImageReader(img1_buf), 50, height - 300, width=300, height=200)  # Derivative Curve
    img2_buf = plot_to_bytes(fig2)
    c.drawImage(ImageReader(img2_buf), 50, height - 550, width=300, height=200)  # Titration Curve below
    c.showPage()
    # Page 4: Results + pKa Comparison
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 100, "Results and pKa Comparison")
    c.setFont("Helvetica", 12)
    y = height - 150
    c.drawString(100, y, f"Equivalence Point Volume: {V_eq:.2f} mL")
    y -= 20
    c.drawString(100, y, f"Half-Equivalence Volume: {V_half:.2f} mL")
    y -= 20
    c.drawString(100, y, f"pKa: {pKa:.2f}")
    y -= 40
    for line in comparison_text.strip().split('\n'):
        c.drawString(100, y, line.strip())
        y -= 20
    c.save()
    buffer.seek(0)
    return buffer

st.title("Interpretation of pKa values of a cooling fluid")

with st.container():
    st.header("Enter Details")
    student_name = st.text_input("Student Name")
    roll_number = st.text_input("Roll Number")
    division = st.text_input("Division")
    year = st.text_input("Year")
    course = st.text_input("Course")
    program = st.text_input("Program")
    branch = st.text_input("Branch")
    sample_name = st.text_input("Sample/Fluid Name")
    date = datetime.date.today().strftime("%Y-%m-%d")

with st.container():
    st.header("Enter Titration Data")
    n = st.number_input("Number of data points (n)", min_value=1, step=1, value=21)
    if n > 0:
        default_volumes = [i * 0.5 for i in range(n)]
        data = pd.DataFrame({
            'Volume (mL)': default_volumes,
            'pH': [0.0] * n
        })
        edited_data = st.data_editor(data, num_rows="fixed", use_container_width=True)
        volumes = edited_data['Volume (mL)'].values
        pHs = edited_data['pH'].values

volumes = np.array(volumes)
pHs = np.array(pHs)

if st.button("Run Analysis"):
    if len(volumes) != n or len(pHs) != n:
        st.error("Please enter all volume and pH values.")
    else:
        try:
            V_eq, eq_index = find_equivalence_point(volumes, pHs)
            st.success(f"Equivalence Point Volume: {V_eq:.2f} mL")
            V_half = V_eq / 2
            st.success(f"Half-Equivalence Volume: {V_half:.2f} mL")
            pKa = interpolate_pH(volumes, pHs, V_half)
            st.success(f"pKa: {pKa:.2f}")
            st.session_state.analysis_done = True
            st.session_state.volumes = volumes
            st.session_state.pHs = pHs
            st.session_state.V_eq = V_eq
            st.session_state.V_half = V_half
            st.session_state.pKa = pKa
            dpHdV = compute_derivative(volumes, pHs)
            fig1, ax1 = plt.subplots()
            ax1.plot(volumes[:-1], dpHdV, color='#512da8', linewidth=2, label='dpH/dV')  # Plot at volumes[:-1] for accurate x-axis
            ax1.scatter(volumes[eq_index - 1], dpHdV[eq_index - 1], color='#f48fb1', s=100, label='Equivalence Point')  # Adjusted scatter
            ax1.set_xlabel('Volume (mL)', color='#283593')
            ax1.set_ylabel('dpH/dV', color='#283593')
            ax1.set_title('Derivative Curve', color='#673ab7')
            ax1.legend()
            ax1.grid(True, color='#c5cae9')
            st.session_state.fig1 = fig1
            fig2, ax2 = plt.subplots()
            ax2.plot(volumes, pHs, color='#283593', linewidth=2, label='pH vs Volume')
            ax2.scatter(V_half, pKa, color='#81c784', s=100, label=f'Half-Equivalence (pKa={pKa:.2f})')
            ax2.scatter(V_eq, interpolate_pH(volumes, pHs, V_eq), color='#f48fb1', s=100, label='Equivalence Point')
            ax2.set_xlabel('Volume (mL)', color='#283593')
            ax2.set_ylabel('pH', color='#283593')
            ax2.set_title('Titration Curve', color='#673ab7')
            ax2.legend()
            ax2.grid(True, color='#c5cae9')
            st.session_state.fig2 = fig2
        except Exception as e:
            st.error(f"An error occurred: {str(e)}. Please check your data and try again.")

if st.session_state.analysis_done:
    volumes = st.session_state.volumes
    pHs = st.session_state.pHs
    V_eq = st.session_state.V_eq
    V_half = st.session_state.V_half
    pKa = st.session_state.pKa
    fig1 = st.session_state.fig1
    fig2 = st.session_state.fig2
    st.header("Graphs")
    st.pyplot(fig1)
    st.pyplot(fig2)
    st.header("Details")
    details = {
        "Student Name": student_name,
        "Roll Number": roll_number,
        "Division": division,
        "Year": year,
        "Date": date,
        "Course": course,
        "Program": program,
        "Branch": branch,
        "Sample/Fluid Name": sample_name
    }
    for key, value in details.items():
        st.write(f"{key}:** {value}")
    st.header("Compare with Standard Solution")
    standards = {
        "Benzoic Acid": 4.2,  # Added as default
        "Acetic Acid": 4.76,
        "Carbonic Acid (pKa1)": 6.35,
        "Phosphoric Acid (pKa1)": 2.15,
        "Ammonia": 9.25,
        "Hydrochloric Acid": -6.3,
        "Sodium Hydroxide": 15.7,
        "Other (Enter Custom)": None
    }
    selected_standard = st.selectbox("Select a standard solution to compare:", list(standards.keys()), index=0)  # Default to Benzoic Acid
    if selected_standard == "Other (Enter Custom)":
        custom_name = st.text_input("Enter custom acid name:", value="")
        custom_pka = st.number_input("Enter custom standard pKa value:", value=0.0)
        std_pka = custom_pka
        display_name = custom_name if custom_name else "Custom Acid"
    else:
        std_pka = standards[selected_standard]
        display_name = selected_standard
    diff = abs(std_pka - pKa)
    accuracy = max(0, 100 - (diff / std_pka * 100)) if std_pka != 0 else 0
    st.write(f"*Selected Standard:* {display_name}")
    st.write(f"*Standard pKa:* {std_pka:.2f}")
    st.write(f"*Calculated pKa:* {pKa:.2f}")
    st.write(f"*Difference:* {diff:.2f}")
    st.write(f"*Accuracy:* {accuracy:.2f}%")
    comparison_text = f"Selected Standard: {display_name}\nStandard pKa: {std_pka:.2f}\nCalculated pKa: {pKa:.2f}\nDifference: {diff:.2f}\nAccuracy: {accuracy:.2f}%"
    st.header("Download Full Report")
    pdf_buffer = generate_pdf(details, volumes, pHs, V_eq, V_half, pKa, fig1, fig2, comparison_text)
    st.download_button(label="Download Full PDF Report", data=pdf_buffer, file_name="pka_analysis_report.pdf", mime="application/pdf")
       