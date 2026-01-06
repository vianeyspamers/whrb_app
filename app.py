import streamlit as st
import pandas as pd
import json

# ===============================
# Password for fault memory
# ===============================
FAULT_PASSWORD = "Boiler2026"  # <-- change this to your preferred password

# ===============================
# Fault Memory (RAG Knowledge Base)
# ===============================
FAULT_FILE = "fault_memory.json"

def load_fault_memory():
    try:
        with open(FAULT_FILE, "r") as f:
            memory = json.load(f)
            # Ensure every fault has required keys; skip legacy faults in analysis
            valid_memory = []
            for f_item in memory:
                if all(k in f_item for k in ["name", "variable", "operator", "threshold", "solution"]):
                    valid_memory.append(f_item)
            return memory, valid_memory
    except:
        return [], []

def save_fault_memory(memory):
    with open(FAULT_FILE, "w") as f:
        json.dump(memory, f, indent=4)

# Load fault memory
fault_memory, valid_fault_memory = load_fault_memory()

# ===============================
# Fault Evaluation Logic
# ===============================
def evaluate_fault(row, fault):
    """Return True if this fault is triggered for this row"""
    try:
        value = float(row[fault["variable"]])
        threshold = float(fault["threshold"])
        op = fault["operator"]

        if op == "<":
            return value < threshold
        elif op == ">":
            return value > threshold
        elif op == "<=":
            return value <= threshold
        elif op == ">=":
            return value >= threshold
        elif op == "==":
            return value == threshold
    except:
        return False

def analyze_data(df, fault_memory):
    """Analyze each row in df against all valid faults"""
    results = []

    for idx, row in df.iterrows():
        triggered_faults = []

        for fault in fault_memory:
            # Skip faults missing keys (legacy faults)
            if not all(k in fault for k in ["variable", "operator", "threshold"]):
                continue

            if fault["variable"] in df.columns:
                if evaluate_fault(row, fault):
                    triggered_faults.append(fault)

        results.append((idx, triggered_faults))

    return results

# ===============================
# Streamlit UI
# ===============================
st.set_page_config(page_title="DR WHRB Fault Diagnostic", layout="wide")
st.title("🔥 DR Waste Heat Recovery Boiler – Fault Diagnostic App")

# ===============================
# Upload Excel Data
# ===============================
uploaded_file = st.file_uploader("Upload WHRB Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("📊 Uploaded Data")
    st.dataframe(df, use_container_width=True)

    # Run analysis
    st.subheader("🛠 Fault Analysis Results")
    results = analyze_data(df, valid_fault_memory)

    any_faults = False
    for idx, faults in results:
        if faults:
            any_faults = True
            with st.expander(f"Row {idx} – {len(faults)} fault(s) detected"):
                for fault in faults:
                    st.warning(f"⚠ {fault['name']}")
                    st.write(f"**Variable:** {fault['variable']}")
                    st.write(f"**Condition:** {fault['operator']} {fault['threshold']}")
                    st.info(f"🔧 **Recommended action:** {fault['solution']}")

    if not any_faults:
        st.success("✅ No faults detected for current data.")

else:
    st.info("⬆ Upload an Excel file to start analysis.")

# ===============================
# Sidebar – Password Protected Fault Memory
# ===============================
st.sidebar.header("🔒 Fault Memory Access")
password_input = st.sidebar.text_input("Enter password to view/add faults", type="password")

if password_input == FAULT_PASSWORD:
    # --- Fault memory manager ---
    st.sidebar.subheader("📚 Stored Faults")
    if fault_memory:
        for i, fault in enumerate(fault_memory):
            fault_name = fault.get("name", f"Legacy fault {i+1}")
            with st.sidebar.expander(f"{i+1}. {fault_name}"):
                st.write(f"Variable: {fault.get('variable', 'N/A')}")
                st.write(f"Condition: {fault.get('operator', '?')} {fault.get('threshold', '?')}")
                st.write(f"Action: {fault.get('solution', 'N/A')}")
                if st.button(f"❌ Delete Fault {i+1}", key=f"del_{i}"):
                    fault_memory.pop(i)
                    save_fault_memory(fault_memory)
                    st.experimental_rerun()
    else:
        st.sidebar.info("No faults stored yet.")

    # --- Add new fault ---
    st.sidebar.subheader("➕ Add New Fault")
    name = st.sidebar.text_input("Fault name")
    variable = st.sidebar.text_input("Variable name (must match Excel column)")
    operator = st.sidebar.selectbox("Operator", ["<", ">", "<=", ">=", "=="])
    threshold = st.sidebar.number_input("Threshold", value=0.0)
    solution = st.sidebar.text_area("Recommended action")

    if st.sidebar.button("Add Fault"):
        if name and variable and solution:
            new_fault = {
                "name": name,
                "variable": variable,
                "operator": operator,
                "threshold": threshold,
                "solution": solution
            }
            fault_memory.append(new_fault)
            save_fault_memory(fault_memory)
            st.sidebar.success("✅ Fault added to memory")
            st.experimental_rerun()
        else:
            st.sidebar.error("Fault name, variable, and solution are required")
else:
    st.sidebar.info("Enter the correct password to view or edit faults.")

# ===============================
# Footer
# ===============================
st.markdown("---")
st.caption("Developed for DR WHRB temperature monitoring and fault diagnostics")
