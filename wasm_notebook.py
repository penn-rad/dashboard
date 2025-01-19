import marimo

__generated_with = "0.8.22"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import pandas as pd
    import json
    import io
    import pickle
    import altair as alt
    return alt, io, json, mo, pd, pickle


@app.cell
def __(mo):
    qg = mo.ui.file()
    ps = mo.ui.file()
    rs = mo.ui.file()
    run_button = mo.ui.run_button()

    mo.vstack([
        mo.md("##Upload files:"),
        mo.vstack(["qgenda file:", qg]),
        mo.vstack(["powerscribe file:", ps]),
        mo.vstack(["resident file:", rs]),
        mo.md("##Once all of the files have been uploaded, click to run"),
        run_button
    ])
    return ps, qg, rs, run_button


@app.cell
def __(io, pickle):
    def load_file(f):
        # Access the first file in the list (assumes single file upload)
        uploaded_file = f.value[0]

        # Create an in-memory stream from the binary data
        with io.BytesIO(uploaded_file.contents) as g:
            # Unpickle the DataFrame
            loaded_df = pickle.load(g)

        return loaded_df
    return (load_file,)


@app.cell
def __(load_file, ps, qg, rs, run_button):
    if run_button.value:
        ps_df = load_file(ps)
        qg_df = load_file(qg)
        rs_df = load_file(rs)
    return ps_df, qg_df, rs_df


@app.cell
def __(qg_df):
    # Filter for specific shifts
    weekday_shifts = [
        "RES - Chest",
        "RES - PAH Chest",
        "RES - Cardiovascular",
        "RES- CMR",
        "AI RES - CT",
        "RES - PAH CT",
        "AI RES - MRI PCAM 4",
        "RES - PAH MR/body",
        "AI RES - US",
        "RES - PAH US",
        "AI RES - Junior Fluoro",
        "AI RES - Senior Fluoro",
        "RES - PAH FL",
        "RES - MSK",
        "RES - PAH MSK",
        "RES - Neuro",
        "RES - PAH Neuro",
        "RES - IR",
        "RES - PAH IR",
        "RES - Nucs",
        "RES - PAH Nucs",
        "RES - PET",
        "RES Cardiac Nucs PCAM",
        "RES - CHOP",
        "RES - Breast HUP",
        "RES - Breast PAH",
        "RES - VA General",
        "RES - VA Fluoro",
    ]

    off_shifts = [
        "RES - Research",
        "VAC - Vacation",
        "RES - Away Conference",
        "RES - DEPT - Personal",
        "DEPT - FMLA"
    ]

    call_shifts = [
        "RES - Baby Call",
        "RES - HUP Nightfloat",
        "RES - PAH Nightfloat",
        "RES - HUP Dayfloat",
        "RES - PAH Dayfloat",

        "RES - Call PAH Swing",
        "RES - Private Practice",
        "RES - Presby Night",

        "AI FEL - Body Call",
        "RES - Call Body Wknd",
        "RES - Call Neuro Wknd (5pm-9pm)",
    ]

    rotation_schedule = qg_df[
        (qg_df['cancelled'] == False) &
        (
            (
                qg_df['shift_name'].isin(weekday_shifts) &
                ~qg_df['date'].dt.dayofweek.isin([5, 6])  # 5 and 6 represent Saturday and Sunday
            ) | (
                qg_df['shift_name'].isin(call_shifts)
            ) | (
                qg_df['shift_name'].isin(off_shifts)
            )
        )
    ]

    # filtered_schedule = filtered_schedule.sort_values(by='date')

    # # 1. Filter out cancelled shifts and create a copy
    # f_df = qgenda_df[qgenda_df['cancelled'] == False].copy()  # Use .copy() here

    # 2. Calculate the running count of days for each resident on each service
    rotation_schedule.loc[:, 'Day Count'] = rotation_schedule.groupby(['staff_email', 'shift_name'])['date'].rank(method='dense', ascending=True).astype(int)
    return call_shifts, off_shifts, rotation_schedule, weekday_shifts


@app.cell
def __(mo, ps_df):
    procedures = mo.sql(
        f"""
        SELECT
            ProcedureDescList,
            COUNT(*) AS ProcedureCount
        FROM
            ps_df
        GROUP BY
            ProcedureDescList
        ORDER BY
            ProcedureCount DESC;
        """
    )
    return (procedures,)


@app.cell
def __(mo, procedures, rs_df):
    selected_procedures = mo.ui.table(procedures)
    selected_residents = mo.ui.table(rs_df)
    next_run_button = mo.ui.run_button()

    mo.vstack([
        mo.md("## Use this table to select which procedures you would like to analyze volume for"),
        selected_procedures,
        mo.md("## Use this table to select which residents you would like to analyze volume for"),
        selected_residents,
        mo.md("## Click this button once you've made your selections"),
        next_run_button
    ])
    return next_run_button, selected_procedures, selected_residents


@app.cell
def __(
    alt,
    next_run_button,
    ps_df,
    selected_procedures,
    selected_residents,
):
    if next_run_button.value:
        filtered_df = ps_df
        # Display the updated 'reports' DataFrame
        filtered_df = filtered_df[filtered_df["ProcedureDescList"].isin(selected_procedures.value["ProcedureDescList"])]
        filtered_df = filtered_df[filtered_df["DictatorAcctID"].isin(selected_residents.value["powerscribe"])]

        # Group by DictatorAcctID and ProcedureDescList, then count occurrences
        studies_per_person = filtered_df.groupby(["DictatorAcctID", "ProcedureDescList"]).size().reset_index(name="Count")

        # Create an Altair chart
        chart = alt.Chart(studies_per_person).mark_bar().encode(
            y=alt.Y("DictatorAcctID:O", title="Person (DictatorAcctID)"),
            x=alt.X("sum(Count):Q", title="Number of Studies"),  # Sum counts for each study type
            color=alt.Color("ProcedureDescList:N", title="Study Type", legend=None),  # Differentiate by study type
            tooltip=["DictatorAcctID", "ProcedureDescList", "sum(Count)"],
        ).properties(
            title="Study Types Per Person",
            width=1200,
            height=400,
        ).interactive()
    return chart, filtered_df, studies_per_person


@app.cell
def __(chart, mo):
    # Display the chart in Marimo
    mo.ui.altair_chart(chart)
    return


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
