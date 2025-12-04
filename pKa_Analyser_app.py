import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import datetime
import base64
import io

# Updated CSS:
# White main background with a subtle light purple secondary background behind inputs/sections
# Clean, light, and bright look - no dark colors

st.markdown("""
<style>
    /* Set the main background to white */
    .main {
        background-color: #ffffff !important;
        color: #222222;
        padding: 1.5rem 1rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* For containers (sections) inside the app: light purple background with gentle rounding */
    .block-container {
        background: #ede7f6;  /* Very light purple */
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 3px 12px rgba(100, 80, 180, 0.1);
        margin-bottom: 2rem;
    }

    /* Title styling */
    h1 {
        color: #5e35b1;  /* Medium purple */
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
    }

    /* Section headers */
    h2, h3 {
        color: #512da8;  /* Purple */
        margin-top: 1.5rem;
        margin-bottom: 0.7rem;
    }

    /* Input boxes - crisp with subtle purple border and white background */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>div[role="combobox"] {
        border-radius: 6px !important;
        border: 2px solid #9575cd !important;  /* Soft purple border */
        box-shadow: none !important;
        background-color: #ffffff !important;
        padding: 8px;
        color: #222222;
        font-weight: 500;
    }

    /* Buttons - pastel purple gradient */
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(45deg, #7e57c2, #ba68c8) !important; /* Purple pastel */
        color: white !important;
        font-weight: 600;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 24px !important;
        cursor: pointer;
        transition: background 0.3s ease;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background: linear-gradient(45deg, #673ab7, #9c27b0) !important; /* Darker purple hover */
    }

    /* Success and error messages */
    .stSuccess {
        color: #388e3c !important; /* Green */
        font-weight: 600;
    }

    .stError {
        color: #e53935 !important; /* Red */
        font-weight: 600;
    }

    /* Tables - white bg with purple header */
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
        border: 1px solid #d1c4e9 !important;  /* Light purple border */
        padding: 10px !important;
        text-align: center !important;
        color: #444444 !important;
    }
    th {
        background-color: #b39ddb !important; /* Medium light purple */
        color: #2e2e2e !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialization of session state for persistence (same)
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


# Functions as before
def compute_derivative(volumes, pHs):
    dpHdV = np.gradient(pHs, volumes)
    return dpHdV

def find_equivalence_point(volumes, dpHdV):
    peaks, _ = find_peaks(dpHdV, prominence=np.max(dpHdV) * 0.1)
    if len(peaks) == 0:
        st.error("No clear equivalence point found. Check data.")
        return None, None
    eq_index = peaks[0]
    V_eq = volumes[eq_index]
    return V_eq, eq_index

def interpolate_pH(volumes, pHs, target_volume):
    return np.interp(target_volume, volumes, pHs)

def plot_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return img_base64


# App Content

st.title("pKa Analysis of Cooling Fluids")

with st.container():
    st.header("Enter Details")
    student_name = st.text_input("Student Name")
    roll_number = st.text_input("Roll Number")
    division = st.text_input("Division")
    year = st.text_input("Year")
    course = st.text_input("Course")
    sample_name = st.text_input("Sample/Fluid Name")
    instructor = st.text_input("Instructor")
    date = datetime.date.today().strftime("%Y-%m-%d")

with st.container():
    st.header("Enter Titration Data")
    n = st.number_input("Number of data points (n)", min_value=1, step=1, value=5)
    volumes = []
    pHs = []
    if n > 0:
        st.subheader("Enter Volume and pH pairs")
        cols = st.columns(2)
        for i in range(n):
            with cols[0]:
                v = st.number_input(f"Volume {i+1} (mL)", key=f"vol_{i}")
            with cols[1]:
                p = st.number_input(f"pH {i+1}", key=f"ph_{i}")
            volumes.append(v)
            pHs.append(p)

volumes = np.array(volumes)
pHs = np.array(pHs)

if st.button("Run Analysis"):
    if len(volumes) != n or len(pHs) != n:
        st.error("Please enter all volume and pH values.")
    else:
        try:
            dpHdV = compute_derivative(volumes, pHs)
            V_eq, eq_index = find_equivalence_point(volumes, dpHdV)
            if V_eq is not None:
                st.success(f"Equivalence Point Volume: {V_eq:.2f} mL")
                V_half = V_eq / 2
                st.success(f"Half-Equivalence Volume: {V_half:.2f} mL")
                pKa = interpolate_pH(volumes, pHs, V_half)
                st.success(f"pKa: {pKa:.2f}")

                # Save for session persistence
                st.session_state.analysis_done = True
                st.session_state.volumes = volumes
                st.session_state.pHs = pHs
                st.session_state.V_eq = V_eq
                st.session_state.V_half = V_half
                st.session_state.pKa = pKa

                fig1, ax1 = plt.subplots()
                ax1.plot(volumes, dpHdV, color='#512da8', linewidth=2, label='dpH/dV')  # Purple line
                ax1.scatter(volumes[eq_index], dpHdV[eq_index], color='#f48fb1', s=100, label='Equivalence Point')  # Pink dot
                ax1.set_xlabel('Volume (mL)', color='#283593')  # Indigo label
                ax1.set_ylabel('dpH/dV', color='#283593')
                ax1.set_title('Derivative Curve', color='#673ab7')  # Purple title
                ax1.legend()
                ax1.grid(True, color='#c5cae9')  # Light blue grid
                st.session_state.fig1 = fig1

                fig2, ax2 = plt.subplots()
                ax2.plot(volumes, pHs, color='#283593', linewidth=2, label='pH vs Volume')  # Indigo line
                ax2.scatter(V_half, pKa, color='#81c784', s=100, label=f'Half-Equivalence (pKa={pKa:.2f})')  # Light green dot
                ax2.scatter(V_eq, interpolate_pH(volumes, pHs, V_eq), color='#f48fb1', s=100, label='Equivalence Point')  # Pink dot
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
        "Sample/Fluid Name": sample_name,
        "Instructor": instructor
    }
    for key, value in details.items():
        st.write(f"**{key}:** {value}")

    st.header("Compare with Standard Solution")
    standards = {
        "Acetic Acid": 4.76,
        "Carbonic Acid (pKa1)": 6.35,
        "Phosphoric Acid (pKa1)": 2.15,
        "Ammonia": 9.25,
        "Hydrochloric Acid": -6.3,
        "Sodium Hydroxide": 15.7,
        "Other (Enter Custom)": None
    }
    selected_standard = st.selectbox("Select a standard solution to compare:", list(standards.keys()))

    if selected_standard == "Other (Enter Custom)":
        custom_name = st.text_input("Enter custom acid name:", value="")
        custom_pka = st.number_input("Enter custom standard pKa value:", value=0.0)
        std_pka = custom_pka
        display_name = custom_name if custom_name else "Custom Acid"
    else:
        std_pka = standards[selected_standard]
        display_name = selected_standard

    diff = abs(std_pka - pKa)
    # Updated accuracy calculation: 100 - (diff / pKa * 100) to match your expectation (e.g., for pKa=4.12, std=2.06, diff=2.06, 2.06/4.12≈0.5, so 100-50=50%)
    accuracy = max(0, 100 - (diff / pKa * 100)) if pKa != 0 else 0
    st.write(f"**Selected Standard:** {display_name}")
    st.write(f"**Standard pKa:** {std_pka:.2f}")
    st.write(f"**Calculated pKa:** {pKa:.2f}")
    st.write(f"**Difference:** {diff:.2f}")
    st.write(f"**Accuracy:** {accuracy:.2f}%")

    st.header("Download Full Report")

    img1_base64 = plot_to_base64(fig1)
    img2_base64 = plot_to_base64(fig2)

    data_html = "<table border='1'><tr><th>Volume (mL)</th><th>pH</th></tr>"
    for v, p in zip(volumes, pHs):
        data_html += f"<tr><td>{v:.2f}</td><td>{p:.2f}</td></tr>"
    data_html += "</table>"

    comparison_html = f"""
    <h3>pKa Comparison with Selected Standard</h3>
    <p><strong>Selected Standard:</strong> {display_name}</p>
    <p><strong>Standard pKa:</strong> {std_pka:.2f}</p>
    <p><strong>Calculated pKa:</strong> {pKa:.2f}</p>
    <p><strong>Difference:</strong> {diff:.2f}</p>
    <p><strong>Accuracy:</strong> {accuracy:.2f}%</p>
    """

    html_content = f"""
    <html>
    <head><title>pKa Analysis Report</title></head>
    <body style="background-color:#ede7f6; font-family:Segoe UI, Tahoma, Geneva, Verdana, sans-serif; color: #222;">
        <h1 style="color:#5e35b1; text-align:center;">pKa Analysis of Cooling Fluids Report</h1>
        <div style="max-width:800px; margin:auto; background:#fff; padding:20px; border-radius:12px; box-shadow: 0px 4px 10px rgba(0,0,0,0.05);">
            <h2>Details</h2>
            <ul>
                {"".join(f"<li>{key}: {value}</li>" for key, value in details.items())}
            </ul>
            <h2>Input Data</h2>
            {data_html}
            <h2>Results</h2>
            <p>Equivalence Point Volume: {V_eq:.2f} mL</p>
            <p>Half-Equivalence Volume: {V_half:.2f} mL</p>
            <p>pKa: {pKa:.2f}</p>
            <h2>Graphs</h2>
            <h3>Derivative Curve</h3>
            <img src="data:image/png;base64,{img1_base64}" alt="Derivative Curve" style="max-width:100%;">
            <h3>Titration Curve</h3>
            <img src="data:image/png;base64,{img2_base64}" alt="Titration Curve" style="max-width:100%;">
            {comparison_html}
        </div>
    </body>
    </html>
    """

    st.download_button(
        label="Download Full HTML Report",
        data=html_content,
        file_name="pka_analysis_report.html",
        mime="text/html"
    )

