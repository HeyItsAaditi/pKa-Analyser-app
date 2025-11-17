import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import datetime
import base64
import io

# Updated CSS: WHITE background and soft, tasteful colors
st.markdown("""
<style>
    /* White background for main app content */
    .main {
        background-color: #ffffff !important;
        color: #222222;
    }

    /* Title styling */
    h1 {
        color: #5e35b1;  /* Medium purple */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
    }

    /* Section headers */
    h2, h3 {
        color: #3f51b5;  /* Indigo blue */
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }

    /* Input boxes - soft purple border with subtle shadow */
    .stTextInput>div>div>input, 
    .stNumberInput>div>div>input, 
    .stSelectbox>div>div>div[role="combobox"] {
        border-radius: 5px !important;
        border: 2px solid #9575cd !important;  /* Soft purple */
        box-shadow: 0 0 5px #d1c4e9;
        padding: 8px;
        color: #333333;
        background-color: #f9f9fb;
    }

    /* Buttons with pastel gradient */
    .stButton>button, .stDownloadButton>button {
        background: linear-gradient(45deg, #7986cb, #f48fb1) !important; /* Soft blue-pink */
        color: #fff !important;
        font-weight: bold;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        border: none !important;
        transition: background 0.3s ease;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background: linear-gradient(45deg, #5c6bc0, #f06292) !important; /* Darker hover */
    }

    /* Success and error messages */
    .stSuccess {
        color: #4caf50 !important; /* Green */
        font-weight: 600;
    }

    .stError {
        color: #e53935 !important; /* Red */
        font-weight: 600;
    }

    /* Table borders */
    table {
        border-collapse: collapse !important;
        width: 100% !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    th, td {
        border: 1px solid #b39ddb !important;
        padding: 8px !important;
        text-align: center !important;
        color: #444444 !important;
    }
    th {
        background-color: #ede7f6 !important; /* Light purple */
    }

</style>
""", unsafe_allow_html=True)

# Initialize session state (Same as your logic)
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

# Your functions (unchanged)
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

# Main Streamlit app structure (fully same logic as before, just color updated on plots)

st.title("pKa Analysis of Cooling Fluids")

st.header("Enter Details")
student_name = st.text_input("Student Name")
roll_number = st.text_input("Roll Number")
division = st.text_input("Division")
year = st.text_input("Year")
course = st.text_input("Course")
sample_name = st.text_input("Sample/Fluid Name")
instructor = st.text_input("Instructor")
date = datetime.date.today().strftime("%Y-%m-%d")

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

                # Store in session state
                st.session_state.analysis_done = True
                st.session_state.volumes = volumes
                st.session_state.pHs = pHs
                st.session_state.V_eq = V_eq
                st.session_state.V_half = V_half
                st.session_state.pKa = pKa
                
                # Colorful plots with pleasant colors
                fig1, ax1 = plt.subplots()
                ax1.plot(volumes, dpHdV, color='#4a148c', linewidth=2, label='dpH/dV')  # Purple line
                ax1.scatter(volumes[eq_index], dpHdV[eq_index], color='#f06292', s=100, label='Equivalence Point')  # Pink dot
                ax1.set_xlabel('Volume (mL)', color='#283593')  # Indigo labels
                ax1.set_ylabel('dpH/dV', color='#283593')
                ax1.set_title('Derivative Curve', color='#6a1b9a')  # Purple title
                ax1.legend()
                ax1.grid(True, color='#aed581')  # Light green grid
                st.session_state.fig1 = fig1

                fig2, ax2 = plt.subplots()
                ax2.plot(volumes, pHs, color='#283593', linewidth=2, label='pH vs Volume')  # Indigo line
                ax2.scatter(V_half, pKa, color='#81c784', s=100, label=f'Half-Equivalence (pKa={pKa:.2f})')  # Light green dot
                ax2.scatter(V_eq, interpolate_pH(volumes, pHs, V_eq), color='#f06292', s=100, label='Equivalence Point')  # Pink dot
                ax2.set_xlabel('Volume (mL)', color='#283593')
                ax2.set_ylabel('pH', color='#283593')
                ax2.set_title('Titration Curve', color='#6a1b9a')
                ax2.legend()
                ax2.grid(True, color='#aed581')
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
        custom_pka = st.number_input("Enter custom standard pKa value:", value=0.0)
        std_pka = custom_pka
    else:
        std_pka = standards[selected_standard]

    diff = abs(std_pka - pKa)
    accuracy = max(0, 100 - (diff / abs(std_pka) * 100)) if std_pka != 0 else 0
    st.write(f"**Selected Standard:** {selected_standard}")
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
    <p><strong>Selected Standard:</strong> {selected_standard}</p>
    <p><strong>Standard pKa:</strong> {std_pka:.2f}</p>
    <p><strong>Calculated pKa:</strong> {pKa:.2f}</p>
    <p><strong>Difference:</strong> {diff:.2f}</p>
    <p><strong>Accuracy:</strong> {accuracy:.2f}%</p>
    """

    html_content = f"""
    <html>
    <head><title>pKa Analysis Report</title></head>
    <body>
        <h1>pKa Analysis of Cooling Fluids Report</h1>
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
        <img src="data:image/png;base64,{img1_base64}" alt="Derivative Curve">
        <h3>Titration Curve</h3>
        <img src="data:image/png;base64,{img2_base64}" alt="Titration Curve">
        {comparison_html}
    </body>
    </html>
    """

    st.download_button(
        label="Download Full HTML Report",
        data=html_content,
        file_name="pka_analysis_report.html",
        mime="text/html"
    )