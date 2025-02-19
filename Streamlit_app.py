import streamlit as st
import pandas as pd
import os
from io import BytesIO

# Set page configuration
st.set_page_config(page_title="Data Sweeper", layout="wide")

# Main page title and description
st.title("Data Sweeper")
st.write(
    """
    Transform your files between CSV and Excel formats with built-in data cleaning,
    column selection, conversion, visualization, and more!
    """
)

# Sidebar widgets for options
clean_data_option = st.sidebar.checkbox("Clean Data", value=False)
st.sidebar.markdown("### Column Options")

# File uploader on the main page
uploaded_files = st.file_uploader(
    "Upload your file (CSV or Excel):",
    type=["csv", "xlsx"],
    accept_multiple_files=True
)

def basic_cleaning(df):
    """
    Apply basic data cleaning:
    - Drop duplicate rows
    - Fill missing numeric values with the median
    - Fill missing text values with a placeholder "Missing"
    """
    df_clean = df.drop_duplicates()
    
    # Fill missing numeric values
    numeric_cols = df_clean.select_dtypes(include=['number']).columns
    for col in numeric_cols:
        median_val = df_clean[col].median()
        df_clean[col].fillna(median_val, inplace=True)
    
    # Fill missing text values
    object_cols = df_clean.select_dtypes(include=['object']).columns
    for col in object_cols:
        df_clean[col].fillna("Missing", inplace=True)
    
    return df_clean

def convert_df_to_excel(df):
    """
    Convert a DataFrame to Excel format and return the binary content.
    """
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()  # Use close() instead of save()
    processed_data = output.getvalue()
    return processed_data

if uploaded_files:
    # Process each uploaded file
    for file in uploaded_files:
        file_ext = os.path.splitext(file.name)[-1].lower()
        st.write(f"**Processing file:** {file.name}")
        df = None  # Initialize DataFrame
        
        if file_ext == ".csv":
            try:
                df = pd.read_csv(file)
                st.success("CSV file loaded successfully!")
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")
        elif file_ext == ".xlsx":
            try:
                df = pd.read_excel(file)
                st.success("Excel file loaded successfully!")
            except Exception as e:
                st.error(f"Error reading Excel file: {e}")
        else:
            st.error(f"Unsupported file type: {file_ext}")

        if df is not None:
            st.write("### Original DataFrame")
            st.dataframe(df)

            # If the file is CSV, add an option to convert it to Excel and show download button
            if file_ext == ".csv":
                st.write("#### Convert CSV to Excel")
                if st.button(f"Convert {file.name} to Excel"):
                    excel_data = convert_df_to_excel(df)
                    st.download_button(
                        label="Download Excel File",
                        data=excel_data,
                        file_name=file.name.replace(".csv", ".xlsx"),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            # Apply cleaning if the option is selected
            if clean_data_option:
                df = basic_cleaning(df)
                st.success("Data cleaning applied!")
                st.write("### Cleaned DataFrame")
                st.dataframe(df)
            else:
                st.info("Data cleaning not applied. Toggle the 'Clean Data' checkbox in the sidebar to clean your data.")

            # Sidebar: Column selection to keep
            all_columns = list(df.columns)
            selected_columns = st.sidebar.multiselect("Select columns to keep", all_columns, default=all_columns)
            if selected_columns:
                df = df[selected_columns]
                st.write("### DataFrame After Column Selection")
                st.dataframe(df)
            
            # Sidebar: Option to convert selected columns to numeric
            columns_for_conversion = st.sidebar.multiselect("Select columns to convert to numeric", options=df.columns, default=[])
            if columns_for_conversion:
                for col in columns_for_conversion:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                st.success("Conversion to numeric applied!")
                st.write("### DataFrame After Conversion")
                st.dataframe(df)
            
            st.write("### Preview (Head) of the DataFrame")
            st.dataframe(df.head())
            
            # --- Sum Visualization ---
            st.write("### Sum Visualization for Numeric Columns")
            numeric_columns = df.select_dtypes(include='number').columns
            if len(numeric_columns) > 0:
                # Calculate the sum of each numeric column
                sum_data = df[numeric_columns].sum()
                st.bar_chart(sum_data)
            else:
                st.info("No numeric columns available for sum visualization.")
            
            # --- Date Visualization ---
            st.write("### Date Visualization")
            # Attempt to find potential date columns
            date_columns = []
            for col in df.columns:
                try:
                    converted = pd.to_datetime(df[col], errors='coerce')
                    # If more than half of the values convert to a date, consider it a date column
                    if converted.notna().sum() > len(converted) / 2:
                        date_columns.append(col)
                except Exception:
                    pass
                    
            if date_columns:
                selected_date_column = st.sidebar.selectbox("Select a date column for visualization", date_columns)
                # Convert the selected column to datetime
                df[selected_date_column] = pd.to_datetime(df[selected_date_column], errors='coerce')
                # Group by the date column and count records (you can modify aggregation as needed)
                date_counts = df.groupby(selected_date_column).size()
                st.line_chart(date_counts)
            else:
                st.info("No suitable date columns found for date visualization.")
else:
    st.info("Please upload a CSV or Excel file.")
