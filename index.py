import streamlit as st
import pandas as pd

st.markdown("""
    <div style='text-align: center;'>
        <h1>Project INSAAF</h1>
        <p style='font-size:18px; color:gray;'>
            BECUASE JUSTICE DELAYED, IS JUSTICE DENIED
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

    return sortCases(df)

dataset = pd.read_csv("insaafdataset.csv")


df_prioritized = prioritize_cases(dataset)
print(df_prioritized)

if page == "Dashboard":
    st.dataframe(df_prioritized)


if page == "Add case":
    st.write("Add a case")
    with st.form("my_form"):
        caseNo = st.text_input("Enter case number: ")
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


