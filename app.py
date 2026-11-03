from datetime import datetime, time, timedelta
import pandas as pd
import plotly.express as px
from PIL import Image
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Diabetes 24-Hour Daily Log", page_icon="📈", layout="wide"
)

st.title("🩸 Daily Blood Glucose & Health Log (08:00 - 08:00)")
st.markdown(
    "Track your 24-hour cycles starting at 8:00 AM and closing at 8:00 AM the following morning."
)

# Initialize Session State
if "log_data" not in st.session_state:
    st.session_state.log_data = pd.DataFrame(
        columns=[
            "Date",
            "Time",
            "Blood Glucose (mmol/L)",
            "Category",
            "Details",
            "Insulin (units)",
            "Cause / Notes",
            "Snapshot",
        ]
    )

# --- SIDEBAR: DATA ENTRY FORM ---
st.sidebar.header("📝 Add New Entry")

with st.sidebar.form("entry_form", clear_on_submit=True):
    entry_date = st.date_input("Log Date", datetime.today())
    entry_time = st.time_input("Time", value=time(8, 0))

    bg_level = st.number_input(
        "Blood Glucose (mmol/L)", min_value=1.0, max_value=30.0, value=6.0, step=0.1
    )

    category = st.selectbox(
        "Log Type", ["Food", "Illness", "Activity", "General Log", "Medication"]
    )

    details = st.text_input("Description (e.g., Lunch, Flu symptoms, Walk)")
    insulin = st.number_input(
        "Insulin (units)", min_value=0.0, max_value=100.0, value=0.0, step=0.5
    )
    cause = st.text_input("Cause / Triggers / Notes")

    # Image upload attachment directly inside the form
    uploaded_file = st.file_uploader(
        "Attach Meter Snapshot / Food Photo", type=["jpg", "jpeg", "png"]
    )

    submitted = st.form_submit_button("Add Entry")

    if submitted:
        photo_name = uploaded_file.name if uploaded_file else "None"
        new_row = {
            "Date": entry_date,
            "Time": entry_time.strftime("%H:%M"),
            "Blood Glucose (mmol/L)": bg_level,
            "Category": category,
            "Details": details,
            "Insulin (units)": insulin,
            "Cause / Notes": cause,
            "Snapshot": photo_name,
        }
        st.session_state.log_data = pd.concat(
            [st.session_state.log_data, pd.DataFrame([new_row])]
        ).reset_index(drop=True)
        st.sidebar.success("Entry added successfully!")

# --- MAIN DASHBOARD ---
df = st.session_state.log_data

if not df.empty:
    df["DateTime"] = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Time"].astype(str)
    )
    df = df.sort_values("DateTime").reset_index(drop=True)

    st.subheader("📊 24-Hour Cycle Filter")
    unique_dates = df["Date"].unique()

    selected_date = st.selectbox(
        "Select Starting Date (Cycle starts at 08:00 AM):",
        options=unique_dates,
        format_func=lambda x: pd.to_datetime(x).strftime("%Y-%m-%d"),
    )

    cycle_start = pd.to_datetime(f"{selected_date} 08:00:00")
    cycle_end = cycle_start + timedelta(days=1, hours=0, minutes=0)

    cycle_df = df[
        (df["DateTime"] >= cycle_start) & (df["DateTime"] < cycle_end)
    ]

    st.markdown(
        f"**Active Cycle Window:** {cycle_start.strftime('%Y-%m-%d %H:%M')} to {cycle_end.strftime('%Y-%m-%d %H:%M')}"
    )

    # Metrics Summary
    col1, col2, col3, col4 = st.columns(4)
    if not cycle_df.empty:
        avg_bg = cycle_df["Blood Glucose (mmol/L)"].mean()
        high_count = len(cycle_df[cycle_df["Blood Glucose (mmol/L)"] > 10])
        low_count = len(cycle_df[cycle_df["Blood Glucose (mmol/L)"] < 5])
        total_insulin = cycle_df["Insulin (units)"].sum()

        col1.metric("Average BG", f"{avg_bg:.1f} mmol/L")
        col2.metric("Highs (> 10 mmol/L)", f"{high_count}")
        col3.metric("Lows (< 5 mmol/L)", f"{low_count}")
        col4.metric("Total Insulin", f"{total_insulin} units")

        # --- GRAPHING ---
        st.subheader("📈 Blood Glucose Trend & High/Low Thresholds")


        def get_status(bg):
            if bg > 10:
                return "High (> 10)"
            elif bg < 5:
                return "Low (< 5)"
            else:
                return "Target Range (5 - 10)"


        cycle_df["Status"] = cycle_df["Blood Glucose (mmol/L)"].apply(
            get_status
        )

        fig = px.scatter(
            cycle_df,
            x="DateTime",
            y="Blood Glucose (mmol/L)",
            color="Status",
            color_discrete_map={
                "High (> 10)": "#FF4B4B",
                "Low (< 5)": "#1C83E1",
                "Target Range (5 - 10)": "#00CC96",
            },
            hover_data=[
                "Time",
                "Category",
                "Details",
                "Insulin (units)",
                "Cause / Notes",
                "Snapshot",
            ],
            labels={
                "DateTime": "Time of Day",
                "Blood Glucose (mmol/L)": "Blood Glucose (mmol/L)",
            },
        )

        fig.add_scatter(
            x=cycle_df["DateTime"],
            y=cycle_df["Blood Glucose (mmol/L)"],
            mode="lines",
            line=dict(color="gray", width=1, dash="dot"),
            showlegend=False,
        )

        fig.add_hline(
            y=10,
            line_dash="dash",
            line_color="red",
            annotation_text="High Threshold (10 mmol/L)",
            annotation_position="top left",
        )
        fig.add_hline(
            y=5,
            line_dash="dash",
            line_color="blue",
            annotation_text="Low Threshold (5 mmol/L)",
            annotation_position="bottom left",
        )

        fig.update_layout(
            xaxis_title="Time", yaxis_title="Blood Glucose (mmol/L)", hovermode="x"
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- LOG TABLE ---
        st.subheader("📋 Log Entries for Current Cycle")
        st.dataframe(
            cycle_df[
                [
                    "Time",
                    "Blood Glucose (mmol/L)",
                    "Category",
                    "Details",
                    "Insulin (units)",
                    "Cause / Notes",
                    "Snapshot",
                ]
            ],
            use_container_width=True,
        )

    else:
        st.info("No log entries found within this 24-hour cycle window.")

    st.markdown("---")
    if st.download_button(
        "📥 Download Full Log as CSV",
        df.to_csv(index=False).encode("utf-8"),
        "diabetes_full_log.csv",
        "text/csv",
    ):
        st.success("Downloaded successfully!")

else:
    st.info(
        "👈 Get started by adding your first entry using the sidebar form on the left."
    )
