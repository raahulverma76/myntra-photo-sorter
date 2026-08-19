import io
import os
import zipfile
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Myntra Photo Sorter", layout="centered"
)

st.title("👕 Myntra Photo Sorter Web App")
st.write(
    "Upload your Excel sheet and select your image folder to filter and group matching pictures automatically."
)

# 1. Upload Excel File
st.header("1. Upload Excel File")
excel_file = st.file_uploader(
    "Choose an Excel file (.xlsx)", type=["xlsx"]
)

# 2. Select Column Name containing filenames
if excel_file:
  try:
    df = pd.read_excel(excel_file)
    st.success("Excel file successfully loaded!")

    # Show column selection
    st.header("2. Choose Column with Filenames")
    column_name = st.selectbox(
        "Select the column that contains the picture names:", df.columns
    )

    # Get target filenames list
    target_files = df[column_name].dropna().astype(str).str.strip().tolist()
    st.info(f"Found {len(target_files)} filenames listed in that column.")

    # 3. Upload Images
    st.header("3. Upload Pictures")
    uploaded_images = st.file_uploader(
        "Upload all the picture files (you can select multiple)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
    )

    if uploaded_images:
      st.info(f"Uploaded {len(uploaded_images)} images to process.")

      if st.button("Match and Separate Images"):
        matched_files = []
        unmatched_count = 0

        # Create an in-memory zip file for easy downloading
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, "w", zipfile.ZIP_DEFLATED
        ) as zip_file:
          for img in uploaded_images:
            # Check if this image name matches any entry in the excel column
            if img.name in target_files:
              zip_file.writestr(img.name, img.getvalue())
              matched_files.append(img.name)
            else:
              unmatched_count += 1

        zip_buffer.seek(0)

        st.success(
            f"Done! Found {len(matched_files)} matching pictures out of"
            f" {len(target_files)} targeted items."
        )

        # Download button for matching files
        st.download_button(
            label="📥 Download Separated Pictures (ZIP)",
            data=zip_buffer,
            file_name="matched_myntra_photos.zip",
            mime="application/zip",
        )

  except Exception as e:
    st.error(f"Error reading Excel file: {e}")
