import io
import os
import zipfile
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Photo Manager", layout="centered")

st.title("👕 Photo Manager Web App")

# Main Screen Options (Radio buttons to switch between features)
app_mode = st.radio(
    "Choose Mode:",
    ["📂 Sort & Filter Photos (Excel Match)", "✏️ Advanced Bulk Rename Photos"],
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
# MODE 2: ADVANCED BULK RENAME PHOTOS
# ==========================================
elif app_mode == "✏️ Advanced Bulk Rename Photos":
  st.header("✏️ Advanced Bulk Rename Photo Files")
  st.write(
      "Upload your photos, apply multiple rules (like replacing w26 with w25),"
      " and download them renamed!"
  )

  rename_images = st.file_uploader(
      "Upload pictures to rename (multiple allowed)",
      type=["jpg", "jpeg", "png"],
      accept_multiple_files=True,
      key="rename_images",
  )

  if rename_images:
    st.info(f"Loaded {len(rename_images)} images for renaming.")

    # Show options layout
    st.markdown("### Renaming Rules")
    col1, col2 = st.columns(2)

    with col1:
      text_to_find = st.text_input(
          "Find text (e.g. w26):", placeholder="Text you want to change"
      )
    with col2:
      text_replace = st.text_input(
          "Replace with (e.g. w25):", placeholder="New text (leave blank to delete)"
      )

    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
      remove_prefix = st.text_input(
          "Remove from START (Prefix):", placeholder="e.g. ABC-"
      )
    with col4:
      remove_suffix = st.text_input(
          "Remove from END (Suffix before extension):", placeholder="e.g. -Copy"
      )

    st.markdown("---")
    case_option = st.selectbox(
        "Change Text Case (Optional):", ["None", "UPPERCASE", "lowercase"]
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

          # 1. Find and Replace (e.g. w26 -> w25)
          if text_to_find:
            name_part = name_part.replace(text_to_find, text_replace)

          # 2. Remove Prefix from start
          if remove_prefix and name_part.startswith(remove_prefix):
            name_part = name_part[len(remove_prefix) :]

          # 3. Remove Suffix from end
          if remove_suffix and name_part.endswith(remove_suffix):
            name_part = name_part[: -len(remove_suffix)]

          # 4. Change Case
          if case_option == "UPPERCASE":
            name_part = name_part.upper()
          elif case_option == "lowercase":
            name_part = name_part.lower()

          new_filename = name_part + ext

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
