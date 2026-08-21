import io
import os
import re
import zipfile
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Photo Manager", layout="centered")
st.title("👕 Photo Manager Web App")

# Main Screen Options (Radio buttons to switch between features)
app_mode = st.radio(
    "Choose Mode:",
    [
        "📂 Sort & Filter Photos (Excel Match)",
        "✏️ Advanced Bulk Rename Photos",
    ],
    horizontal=True,
)
st.markdown("---")

# ==========================================
# MODE 1: SORT & FILTER PHOTOS
# ==========================================
if app_mode == "📂 Sort & Filter Photos (Excel Match)":
  st.header("1. Upload Excel File & Images")
  excel_file = st.file_uploader(
      "Choose an Excel file (.xlsx)", type=["xlsx"], key="sort_excel"
  )

  if excel_file:
    try:
      df = pd.read_excel(excel_file)
      st.success("Excel file successfully loaded!")

      # Display column selection
      columns = df.columns.tolist()
      st.write("Preview of your Excel data:")
      st.dataframe(df.head(3))

      col1, col2 = st.columns(2)
      with col1:
        style_col = st.selectbox(
            "Select Style ID Column",
            columns,
            index=0 if len(columns) > 0 else 0,
        )
      with col2:
        # Assuming you have an image name column or want to match against a specific text column like 'VAN' or SKU
        image_ref_col = st.selectbox(
            "Select Column containing Image/Reference Name",
            columns,
            index=2 if len(columns) > 2 else 0,
        )

      # Image folder upload
      uploaded_images = st.file_uploader(
          "Upload all corresponding image files",
          type=["jpg", "jpeg", "png"],
          accept_multiple_files=True,
          key="match_images",
      )

      if uploaded_images:
        st.info(f"Loaded {len(uploaded_images)} images from folder.")

        if st.button("Process & Organize Photos"):
          with st.spinner("Sorting images into Style ID folders..."):
            # Create an in-memory zip file to store folders
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(
                zip_buffer, "w", zipfile.ZIP_DEFLATED
            ) as zip_file:
              # Map clean reference values from Excel to Style IDs
              # We will build a dictionary: clean_ref -> style_id
              mapping = {}
              for _, row in df.iterrows():
                s_id = str(row[style_col]).strip()
                ref_val = str(row[image_ref_col]).strip()
                mapping[ref_val.upper()] = s_id

              matched_count = 0

              for img_file in uploaded_images:
                original_filename = img_file.name
                # Strip file extension for matching
                base_name_ext = os.path.splitext(original_filename)[0]

                # Remove suffixes like (2), (3) to match Excel data e.g. M20126BEIGE(2) -> M20126BEIGE
                clean_base_name = re.sub(
                    r"\(\d+\)$", "", base_name_ext
                ).strip()

                # Find if this clean base name exists in our Excel mapping
                upper_key = clean_base_name.upper()
                if upper_key in mapping:
                  style_folder = mapping[upper_key]
                  # Path inside the zip file
                  zip_path = f"{style_folder}/{original_filename}"
                  zip_file.writestr(zip_path, img_file.getvalue())
                  matched_count += 1

            zip_buffer.seek(0)
            st.success(
                f"Successfully matched and organized {matched_count} images!"
            )

            st.download_button(
                label="📥 Download Organized Folders (ZIP)",
                data=zip_buffer,
                file_name="Organized_Style_Folders.zip",
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
