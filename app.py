import io
import os
import zipfile
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Myntra Photo Manager", layout="centered")

st.title("👕 Myntra Photo Manager Web App")

# Main Screen Options (Radio buttons to switch between features)
app_mode = st.radio(
    "Choose Mode:",
    ["📂 Sort & Filter Photos (Excel Match)", "✏️ Bulk Rename Photos"],
    horizontal=True,
)

st.markdown("---")

# ==========================================
# MODE 1: SORT & FILTER PHOTOS
# ==========================================
if app_mode == "📂 Sort & Filter Photos (Excel Match)":
  st.header("1. Upload Excel File")
  excel_file = st.file_uploader(
      "Choose an Excel file (.xlsx)", type=["xlsx"], key="sort_excel"
  )

  if excel_file:
    try:
      df = pd.read_excel(excel_file)
      st.success("Excel file successfully loaded!")

      st.header("2. Choose Column with Filenames")
      column_name = st.selectbox(
          "Select the column that contains the picture names:",
          df.columns,
          key="sort_col",
      )

      target_files = (
          df[column_name].dropna().astype(str).str.strip().tolist()
      )
      st.info(f"Found {len(target_files)} filenames listed in that column.")

      st.header("3. Upload Pictures")
      uploaded_images = st.file_uploader(
          "Upload all the picture files (you can select multiple)",
          type=["jpg", "jpeg", "png"],
          accept_multiple_files=True,
          key="sort_images",
      )

      if uploaded_images:
        st.info(f"Uploaded {len(uploaded_images)} images to process.")

        if st.button("Match and Separate Images"):
          matched_files = []
          unmatched_count = 0

          zip_buffer = io.BytesIO()
          with zipfile.ZipFile(
              zip_buffer, "w", zipfile.ZIP_DEFLATED
          ) as zip_file:
            for img in uploaded_images:
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

          st.download_button(
              label="📥 Download Separated Pictures (ZIP)",
              data=zip_buffer,
              file_name="matched_myntra_photos.zip",
              mime="application/zip",
          )

    except Exception as e:
      st.error(f"Error reading Excel file: {e}")

# ==========================================
# MODE 2: BULK RENAME PHOTOS
# ==========================================
elif app_mode == "✏️ Bulk Rename Photos":
  st.header("✏️ Bulk Rename Photo Files")
  st.write(
      "Upload your photos, specify what to find/remove, and download them"
      " renamed!"
  )

  rename_images = st.file_uploader(
      "Upload pictures to rename (multiple allowed)",
      type=["jpg", "jpeg", "png"],
      accept_multiple_files=True,
      key="rename_images",
  )

  if rename_images:
    st.info(f"Loaded {len(rename_images)} images for renaming.")

    col1, col2 = st.columns(2)
    with col1:
      text_to_remove = st.text_input(
          "Text to find / remove:",
          placeholder="e.g. -WHITE or unwanted word",
      )
    with col2:
      text_to_add = st.text_input(
          "Replace with (leave blank to remove):",
          placeholder="leave empty to delete",
      )

    if st.button("Process & Rename Files"):
      rename_zip_buffer = io.BytesIO()
      renamed_count = 0

      with zipfile.ZipFile(
          rename_zip_buffer, "w", zipfile.ZIP_DEFLATED
      ) as zip_file:
        for img in rename_images:
          original_name = img.name
          name_part, ext = os.path.splitext(original_name)

          # Perform find and replace
          new_name_part = name_part.replace(text_to_remove, text_to_add)
          new_filename = new_name_part + ext

          zip_file.writestr(new_filename, img.getvalue())
          renamed_count += 1

      rename_zip_buffer.seek(0)

      st.success(
          f"Successfully renamed {renamed_count} files! Click below to download."
      )

      st.download_button(
          label="📥 Download Renamed Pictures (ZIP)",
          data=rename_zip_buffer,
          file_name="renamed_myntra_photos.zip",
          mime="application/zip",
      )
