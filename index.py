import streamlit as st
import pandas as pd
import numpy as np

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&display=swap');

.stApp {
    font-family: 'Cinzel', serif;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Cinzel', serif !important;
}

p {
    font-family: 'Cinzel', serif !important;
}
</style>

<div style='text-align: center;'>
    <h1>Project INSAAF</h1>
    <p style='font-size:18px;'>
        BECAUSE JUSTICE DELAYED IS JUSTICE DENIED.
    </p>
</div>
""", unsafe_allow_html=True)

st.set_page_config(page_title="PROJECT INSAAF",layout="wide")

st.divider()

page = st.sidebar.radio(label = "" ,options = ["Dashboard","Add case","Judge Allocation"])

def sortCases(df):
    df = df.sort_values(by="Priority Score", ascending=False).reset_index(drop=True)
    return df
def prioritize_cases(df):
    W_CASETYPE = 25
    W_VULNERABLE = 15
    W_AGE = 20
    W_MATTER = 20
    W_UNDERTRIAL = 20

    case_map = {
        "Heinous": 1.0,
        "Serious": 0.8,
        "Moderate": 0.4
    }

    df["case_value"] = df["Offense"].map(case_map)

    df["vulnerable_value"] = df["Vulnerable"].apply(
        lambda x: 0 if x == "None" else 1
    )

    def age_score(x):
        if x <= 4:
            return 0.2
        elif x <= 8:
            return 0.5
        elif x <= 15:
            return 0.8
        else:
            return 1.0

    df["AgeofCase"] = pd.to_numeric(df["AgeofCase"], errors="coerce")
    df["age_value"] = df["AgeofCase"].apply(age_score)
    df["matter_value"] = df["BailMatter"].apply(
        lambda x : 1 if x == "Yes" else 0
    )

    df["undertrial_value"] = df["UnderTrial"].apply(
        lambda x : 1 if x == "Yes" else 0
    )

    df["Priority Score"] = (
        df["case_value"] * W_CASETYPE +
        df["vulnerable_value"] * W_VULNERABLE +
        df["age_value"] * W_AGE +
        df["matter_value"] * W_MATTER +
        df["undertrial_value"] * W_UNDERTRIAL
    ).round(2)

    df = df.drop(columns=[
        "case_value",
        "vulnerable_value",
        "age_value",
        "matter_value",
        "undertrial_value"
    ])

    df["Hearings Required"] = df["Offense"].map({
        "Heinous": 5,
        "Serious": 3,
        "Moderate": 2
    })

    df["Hearings Completed"] = 0
    df["Status"] = "Pending"

    return sortCases(df)
def allocate_judges(df):

    MAX_CAPACITY = 5

    judges = [
        {"name": "Justice A", "level": "Senior", "cases": 0},
        {"name": "Justice B", "level": "Senior", "cases": 0},
        {"name": "Justice C", "level": "Mid", "cases": 0},
        {"name": "Justice D", "level": "Mid", "cases": 0},
        {"name": "Justice E", "level": "Junior", "cases": 0},
    ]

    df = df.copy()
    df = df.sort_values(by="Priority Score", ascending=False)

    assigned = []

    for x, row in df.iterrows():

        offense = row["Offense"]

        if offense == "Heinous":
            eligible = [j for j in judges if j["level"] == "Senior"]
        elif offense == "Serious":
            eligible = [j for j in judges if j["level"] in ["Senior", "Mid"]]
        else:
            eligible = judges

        eligible = [j for j in eligible if j["cases"] < MAX_CAPACITY]

        if not eligible:
            assigned.append("No Judge Available")
            continue

        selected = min(eligible, key=lambda x: x["cases"])
        selected["cases"] += 1
        assigned.append(selected["name"])

    df["Assigned Judge"] = assigned

    return df, judges, MAX_CAPACITY

def simulate_daily_hearings(df, adjournment_rate=0.3):

    df = df.copy()

    for idx, row in df.iterrows():

        if row["Status"] == "Disposed":
            continue

        if np.random.rand() < adjournment_rate:
            continue

        df.at[idx, "Hearings Completed"] += 1

        if df.at[idx, "Hearings Completed"] >= row["Hearings Required"]:
            df.at[idx, "Status"] = "Disposed"

    return df

dataset = pd.read_csv("insaafdataset.csv")

df_prioritized = prioritize_cases(dataset)
print(df_prioritized)

if page == "Dashboard":
    st.dataframe(df_prioritized,hide_index=True)

if page == "Add case":
    st.write("Add a case")
    with st.form("my_form"):
        caseNo = st.number_input("Enter case number: ")
        offense = st.selectbox("Select Offense type: ", ["Heinous","Serious","Moderate"])
        vulnerable = st.selectbox("Select Vulnerable Party: ",["None","Woman","Child","Senior Citizen","Disabled Person"])
        age = st.slider("Pick Age of Case: ",1,30)
        bail = st.checkbox("Bail involved?")
        bail = "Yes" if bail is True else "No"
        trial = st.checkbox("Under trial involved?")
        trial = "Yes" if trial is True else "No"
        submit = st.form_submit_button('Add Case')

    if submit:
        st.write("Added new case")
        new_case = {
            "CaseNo": caseNo,
            "Offense": offense,
            "Vulnerable": vulnerable,
            "AgeofCase": age,
            "BailMatter" : bail,
            "UnderTrial": trial
        }

        newCaseDf = pd.DataFrame([new_case])
        newCaseDf.to_csv("insaafdataset.csv", mode="a", header=False, index=False)
        newCaseDf = prioritize_cases(newCaseDf)
        df_prioritized = pd.concat([df_prioritized,newCaseDf],ignore_index=True)
        df_prioritized = sortCases(df_prioritized)

if page == "Judge Allocation":

    st.subheader("Judge Allocation Overview")

    allocated_df, judges, capacity = allocate_judges(df_prioritized)

    col1, col2 = st.columns(2)

    col1.metric("Total Judges", len(judges))
    col2.metric("Capacity Per Judge", capacity)

    st.divider()

    st.subheader("️Judge Workload Summary")

    judge_summary = pd.DataFrame(judges)
    judge_summary["Remaining Capacity"] = capacity - judge_summary["cases"]

    st.dataframe(judge_summary, hide_index=True)

    st.divider()
    st.subheader("Daily Court Simulation")

    if "simulated_df" not in st.session_state:
        st.session_state.simulated_df = df_prioritized.copy()

    if "disposed_total" not in st.session_state:
        st.session_state.disposed_total = 0

    if st.button("Run One Court Day"):
        updated_df = simulate_daily_hearings(
            st.session_state.simulated_df
        )

        disposed_today = len(
            updated_df[updated_df["Status"] == "Disposed"]
        )

        st.session_state.disposed_total += disposed_today

        updated_df = updated_df[
            updated_df["Status"] != "Disposed"
            ]

        reallocated_df, judges, capacity = allocate_judges(updated_df)

        st.session_state.simulated_df = reallocated_df

        st.success("One Day Simulated & Reallocated")


    st.divider()

    pending = len(st.session_state.simulated_df)

    col1, col2 = st.columns(2)
    col1.metric("Pending Cases", pending)
    col2.metric("Total Disposed Cases", st.session_state.disposed_total)

    st.subheader("Active Cases After Simulation")
    st.dataframe(st.session_state.simulated_df, hide_index=True)