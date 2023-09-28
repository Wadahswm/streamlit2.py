
import streamlit as st
import pandas as pd
import sqlite3
import datetime

st.title('Daily readings')
st.text('This app shows the data and graphs of the wells')
cnx = sqlite3.connect('C:/Users/Lenovo/PycharmProjects/Texteditor/Daily.db')

# Allow the user to select the percentage change threshold using a slider
percentage_threshold = st.sidebar.slider("# **Select the Percentage Change %**", 1, 100, 40)

# Allow the user to select the period (daily, weekly, monthly) using a radio button
period = st.sidebar.radio("Select the Period", ["Daily", "Weekly", "Monthly"])

# Determine the date range based on the selected period
if period == "Daily":
    date_range = datetime.timedelta(days=2)
elif period == "Weekly":
    date_range = datetime.timedelta(weeks=1)
else:
    date_range = datetime.timedelta(days=30)  # Default to monthly

# Calculate the start date based on the selected period
start_date = datetime.date.today() - date_range

# Query the database to select wells with a percentage change above the selected threshold within the specified period
query = f"""
    SELECT DISTINCT Well
    FROM (
        SELECT
            Well,
            DATE,
            PI,
            PD,
            TM,
            WHP,
            LAG(PI) OVER (PARTITION BY Well ORDER BY DATE) AS Prev_PI,
            LAG(PD) OVER (PARTITION BY Well ORDER BY DATE) AS Prev_PD,
            LAG(TM) OVER (PARTITION BY Well ORDER BY DATE) AS Prev_TM,
            LAG(WHP) OVER (PARTITION BY Well ORDER BY DATE) AS Prev_WHP
        FROM DailyReadings
        WHERE DATE >= DATE('{start_date}')
    )
    WHERE
        (PI - Prev_PI) / Prev_PI >= {percentage_threshold / 100}
        OR (PD - Prev_PD) / Prev_PD >= {percentage_threshold / 100}
        OR (TM - Prev_TM) / Prev_TM >= {percentage_threshold / 100}
        OR (WHP - Prev_WHP) / Prev_WHP >= {percentage_threshold / 100}
"""
wells_with_changes = pd.read_sql_query(query, cnx)

# Create a drop-down list of wells with significant changes
selected_well = st.selectbox("**Select a well with significant changes**", wells_with_changes["Well"].tolist())

# Query the data for the selected well
df = pd.read_sql_query(f"SELECT  Well, DATE, HZ,B,PI, PD, Ti, Tm, WHP, FLP,VibX FROM DailyReadings WHERE Well = '{selected_well}'", cnx)
df['Tm'] = df['Tm'].astype(float)
# Display the data for the selected well


changed_columns = []
for column in ['Pi', 'Pd', 'Tm', 'WHP']:
    change_percentage = ((df[column] - df[column].shift(1)) / df[column].shift(1)).abs()
    if (change_percentage >= (percentage_threshold / 100)).any():
        changed_columns.append(column)

if changed_columns:
    st.sidebar.write(f"The following columns have changed more than {percentage_threshold}%:")
    st.sidebar.write(changed_columns)
else:
    st.sidebar.write("No columns have changed more than the selected threshold.")

# Draw line charts for selected well
col1,col2=st.columns(2)

with col1:
      st.write('# PIP and PD')
      st.line_chart(df[['Date', 'Pi', 'Pd']], x='Date', y=['Pi', 'Pd'],color=["#cc0000", "#0b5394"], use_container_width=True)
      st.write('# WHP and FLP')
      st.line_chart(df[['Date', 'FLP', 'WHP']], x='Date', y=['FLP', 'WHP'],color=["#cc0000", "#0b5394"], use_container_width=True)
with col2:

      st.write('# AMP and FRQ')
      df['AMP']=df['B']
      st.line_chart(df[['Date','HZ','AMP']], x='Date', y=[ 'HZ','AMP'],color=["#0c343d", "#e06666"],use_container_width=True)


      st.write('# Vibration')
      st.line_chart(df[['Date', 'VibX']], x='Date', y=['VibX'], use_container_width=True)


      st.write('# TM')
      st.line_chart(df[['Date', 'Tm']], x='Date', y=['Tm'], use_container_width=True)

st.write(df[['WELL','Date','HZ','AMP','Pi','Pd','Ti','Tm','WHP','FLP','VibX']])
