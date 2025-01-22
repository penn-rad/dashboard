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
def __(io, pd, pickle):
    def load_file(f):
        # Access the first file in the list (assumes single file upload)
        uploaded_file = f.value[0]

        # Create an in-memory stream from the binary data
        with io.BytesIO(uploaded_file.contents) as g:
            # Unpickle the DataFrame
            loaded_df = pickle.load(g)

        return loaded_df

    def preprocess_qgenda(qgenda_df):
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
        
        rotation_schedule = qgenda_df[
            (qgenda_df['cancelled'] == False) &
            (
                (
                    qgenda_df['shift_name'].isin(weekday_shifts) &
                    ~qgenda_df['date'].dt.dayofweek.isin([5, 6])  # 5 and 6 represent Saturday and Sunday
                ) | (
                    qgenda_df['shift_name'].isin(call_shifts)
                ) | (
                    qgenda_df['shift_name'].isin(off_shifts)
                )
            )
        ]

        rotation_schedule.loc[:, 'Day Count'] = rotation_schedule.groupby(['staff_email', 'shift_name'])['date'].rank(method='dense', ascending=True).astype(int)
        
        return rotation_schedule

    def create_combined_studies_by_shift_df(rotation_df, powerscribe_df, resident_df):
        rotation_df = rotation_df.copy()
        rotation_df['date'] = pd.to_datetime(rotation_df['date']).dt.date
        rotation_df = pd.merge(rotation_df, resident_df[['email', 'powerscribe']], left_on='staff_email', right_on='email', how='left')

        powerscribe_df = powerscribe_df.copy()
        powerscribe_df['date'] = powerscribe_df['CreateDate'].dt.date

        combined_df = pd.merge(rotation_df, powerscribe_df, left_on=['date', 'powerscribe'], right_on=['date', 'DictatorAcctID'], how='outer').drop(columns=["cancelled", "isRotationTask", "staff_email", 'lastModified', 'FillerOrderNumber'])
        return combined_df
    return create_combined_studies_by_shift_df, load_file, preprocess_qgenda


@app.cell
def __(
    create_combined_studies_by_shift_df,
    load_file,
    mo,
    preprocess_qgenda,
    ps,
    qg,
    rs,
    run_button,
):
    if run_button.value:
        ps_df = load_file(ps)
        qg_df = load_file(qg)
        rs_df = load_file(rs)

        # preprocessing
        rotation_schedule = preprocess_qgenda(qg_df)
        combined_df = create_combined_studies_by_shift_df(rotation_schedule, ps_df, rs_df)

        # resident selector
        selected_residents = mo.ui.table(rs_df, page_size=20)

        # analysis selector
        analysis_selector = mo.ui.tabs({
            "Total Volume": mo.md("# Visualizing Total Volume by Resident"),
            "Per Rotation Volume": mo.md("# Visualizing Rotation Volumes by Day")
        })
    return (
        analysis_selector,
        combined_df,
        ps_df,
        qg_df,
        rotation_schedule,
        rs_df,
        selected_residents,
    )


@app.cell
def __(mo, selected_residents):
    mo.vstack([
        mo.md("## Use this table to select which residents you would like to analyze volume for"),
        selected_residents
    ])
    return


@app.cell
def __(analysis_selector, mo, selected_residents):
    def _():
        if len(selected_residents.value) > 0:
            return analysis_selector
        else:
            return mo.md("Please select at least one resident to continue...")
    _()
    return


@app.cell
def __(analysis_selector, mo, ps_df, selected_residents):
    def _create_total_volume_analysis_ui():
        if len(selected_residents.value) > 0 and analysis_selector.value == "Total Volume":
            selected_procedures = mo.ui.table(ps_df["ProcedureDescList"].value_counts().reset_index())
            total_volume_run_button = mo.ui.run_button(label="Update Procedures")

            return mo.vstack([
                mo.md("## Use this table to select which procedures you would like to analyze volume for"),
                selected_procedures,
                total_volume_run_button
            ]), selected_procedures, total_volume_run_button
        else:
            return mo.md(""), None, None
            
    total_volume_analysis_ui, selected_procedures, total_volume_run_button = _create_total_volume_analysis_ui()

    total_volume_analysis_ui
    return (
        selected_procedures,
        total_volume_analysis_ui,
        total_volume_run_button,
    )


@app.cell
def __(
    alt,
    mo,
    ps_df,
    selected_procedures,
    selected_residents,
    total_volume_run_button,
):
    def _():
        if total_volume_run_button and total_volume_run_button.value:
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
                width=900,
                height=400,
            ).interactive()

            return mo.ui.altair_chart(chart)
        else:
            return mo.md("")
    _()
    return


@app.cell
def __():
    # # cell to merge the different dataframes into a single dataframe that is easier to use for downstream tasks

    # _rotation_schedule = rotation_schedule.copy()
    # _rotation_schedule['date'] = pd.to_datetime(rotation_schedule['date']).dt.date
    # _rotation_schedule = pd.merge(_rotation_schedule, rs_df[['email', 'powerscribe']], left_on='staff_email', right_on='email', how='left')

    # _ps_df = ps_df.copy()
    # _ps_df['date'] = _ps_df['CreateDate'].dt.date

    # combined_df = pd.merge(_rotation_schedule, _ps_df, left_on=['date', 'powerscribe'], right_on=['date', 'DictatorAcctID'], how='outer').drop(columns=["cancelled", "isRotationTask", "staff_email", 'lastModified', 'FillerOrderNumber'])
    return


@app.cell
def __(mo):
    mo.md(r"""# Visualizing Rotation Volumes by Day""")
    return


@app.cell
def __(analysis_selector, mo, rotation_schedule):
    def _create_shift_selector_ui():
        if analysis_selector.value == "Per Rotation Volume":
            shift_picklist = mo.ui.table(list(rotation_schedule['shift_name'].drop_duplicates()), selection='single')

            return mo.vstack([
                mo.md("### Select which shifts to analyze (only one shift can be selected at a time):"),
                shift_picklist
            ]), shift_picklist
        else:
            return mo.md(""), None

    shift_selector_ui, shift_picklist = _create_shift_selector_ui()
    shift_selector_ui
    return shift_picklist, shift_selector_ui


@app.cell
def __(combined_df, mo, shift_picklist):
    # Create a function to filter the dataframe and return the filtered table
    def _create_procedure_picklist(combined_df, shift_picklist):
        if shift_picklist:
            if not shift_picklist.value:
                return mo.md("Please select a shift"), None
        
            # Filter the dataframe
            filtered_df = combined_df[
                (combined_df['shift_name'] == shift_picklist.value[0])
            ]
        
            # Create the procedure picklist table
            procedure_table = mo.ui.table(filtered_df['ProcedureDescList'].value_counts().reset_index())
        
            return mo.vstack([
                mo.md("### Select which procedures to analyze volumes for:"),
                mo.md("The procedures are sorted by frequency filtered by volume read by residents on days they were on this rotation. Note that there is some data contamination from days that they had evening calls on top of their day shift. This table allows you to do some manual filtering to remove some of that contamination."),
                procedure_table
            ]), procedure_table
        else:
            return mo.md(""), None

    # Use the function and store the result in a variable
    procedure_picklist_ui, procedure_picklist = _create_procedure_picklist(combined_df, shift_picklist)

    # Display the UI
    procedure_picklist_ui
    return procedure_picklist, procedure_picklist_ui


@app.cell
def __(
    alt,
    combined_df,
    mo,
    procedure_picklist,
    selected_residents,
    shift_picklist,
):
    _filtered_volumes = combined_df[
      (combined_df['shift_name'] == shift_picklist.value[0]) &
      (combined_df['email'].isin(selected_residents.value["email"]) &
      (combined_df['ProcedureDescList'].isin(procedure_picklist.value['ProcedureDescList'])))
    ].groupby(["email", "Day Count"], as_index=False).size()

    # Create Altair scatter plot
    scatter = alt.Chart(_filtered_volumes).mark_circle(size=100).encode(
        x=alt.X("Day Count:O", title="Day #"),  # X-axis: Day Count
        y=alt.Y("size:Q", title="# Studies Read"),  # Y-axis: Number of Studies
        color=alt.Color("email:N", title="Resident", legend=None),  # Color by Resident
        tooltip=["email", "Day Count", "size"],  # Tooltip with details
    ).properties(
        width=800,
        height=400,
        title="# of Filtered Studies Read by Selected Resident(s) on Each Day of Selected Rotation"
    ).interactive()

    chrt = mo.ui.altair_chart(scatter)
    chrt
    return chrt, scatter


@app.cell
def __(chrt, mo):
    selection = mo.ui.table(chrt.value, selection='single')
    def _():
        if len(chrt.value) > 1:
            return selection
    _()
    return (selection,)


@app.cell
def __(chrt, combined_df, selection, shift_picklist):
    def _():
        if len(chrt.value) == 1:
            selected_row = chrt.value.iloc[0]
            return combined_df[
                (combined_df['shift_name'] == shift_picklist.value[0]) &
                (combined_df['email'] == selected_row['email']) &
                (combined_df['Day Count'] == selected_row['Day Count'])
            ]
        elif len(chrt.value) > 1 and len(selection.value) == 1:
            selected_row = selection.value.iloc[0]
            return combined_df[
                (combined_df['shift_name'] == shift_picklist.value[0]) &
                (combined_df['email'] == selected_row['email']) &
                (combined_df['Day Count'] == selected_row['Day Count'])
            ]
        else:
            return "please select a point"
    _()
    return


if __name__ == "__main__":
    app.run()
