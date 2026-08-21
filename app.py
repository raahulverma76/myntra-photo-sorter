import io
import os
import re
import zipfile
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Photo Manager", layout="centered")

st.title("👕 Photo Manager Web App")

# Main Screen Options (Radio buttons for 3 features)
app_mode = st.radio(
    "Choose Mode:",
    [
        "📂 Sort & Filter Photos (Excel Match)",
        "✏️ Advanced Bulk Rename Photos",
        "📁 Organize Photos by Style ID (New)",
    ],
    horizontal=True,
)

st.markdown("---")


# Helper function to extract images from either single files or a ZIP upload
def load_uploaded_images(uploaded_files, uploaded_zip):
  image_list = []  # List of tuples: (filename, bytes_content)

  if uploaded_files:
    for f in uploaded_files:
      image_list.append((f.name, f.getvalue()))

  if uploaded_zip:
    try:
      with zipfile.ZipFile(uploaded_zip, "r") as z:
        for filename in z.namelist():
          if filename.lower().endswith((".jpg", ".jpeg", ".png")) and not filename.startswith("__MACOSX/"):
            # Extract just the file name without folder paths inside the zip
            base_name = os.path.basename(filename)
            if base_name:
              image_list.append((base_name, z.read(filename)))
    except Exception as e:
      st.error(f"Error reading ZIP file: {e}")

  return image_list


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

      st.header("3. Upload Pictures (Multiple Files OR ZIP)")
      up_files = st.file_uploader(
          "Upload individual pictures:",
          type=["jpg", "jpeg", "png"],
          accept_multiple_files=True,
          key="sort_images",
      )
      up_zip = st.file_uploader(
          "OR Upload a ZIP file containing pictures:",
          type=["zip"],
          key="sort_zip",
      )

      all_imgs = load_uploaded_images(up_files, up_zip)

      if all_imgs:
        st.info(f"Loaded {len(all_imgs)} total images to process.")

        if st.button("Match and Separate Images"):
          matched_files = []
          zip_buffer = io.BytesIO()
          seen_names = {}

          with zipfile.ZipFile(
              zip_buffer, "w", zipfile.ZIP_DEFLATED
          ) as zip_file:
            for name, content in all_imgs:
              if name in target_files:
                # Handle duplicates cleanly
                final_name = name
                if final_name in seen_names:
                  seen_names[final_name] += 1
                  name_part, ext = os.path.splitext(name)
                  final_name = f"{name_part}_{seen_names[name]}{ext}"
                else:
                  seen_names[final_name] = 0

                zip_file.writestr(final_name, content)
                matched_files.append(final_name)

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
      "Upload your photos (or a ZIP), apply rules, and download them renamed!"
  )

  up_files = st.file_uploader(
      "Upload individual pictures to rename:",
      type=["jpg", "jpeg", "png"],
      accept_multiple_files=True,
      key="rename_images",
  )
  up_zip = st.file_uploader(
      "OR Upload a ZIP file to rename:", type=["zip"], key="rename_zip"
  )

  rename_images = load_uploaded_images(up_files, up_zip)

  if rename_images:
    st.info(f"Loaded {len(rename_images)} images for renaming.")

    st.markdown("### Renaming Rules")
    col1, col2 = st.columns(2)

    with col1:
      text_to_find = st.text_input(
          "Find text (e.g. w26):", placeholder="Text you want to change"
      )
    with col2:
      text_replace = st.text_input(
          "Replace with (e.g. w25):",
          placeholder="New text (leave blank to delete)",
      )

    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
      remove_prefix = st.text_input(
          "Remove from START (Prefix):", placeholder="e.g. ABC-"
      )
    with col4:
      remove_suffix = st.text_input(
          "Remove specific text from END:", placeholder="e.g. -Copy"
      )

    st.markdown("---")
    remove_last_n = st.number_input(
        "Remove N characters from the END (Last characters):",
        min_value=0,
        max_value=50,
        value=0,
        step=1,
    )

    st.markdown("---")
    case_option = st.selectbox(
        "Change Text Case (Optional):", ["None", "UPPERCASE", "lowercase"]
    )

    if st.button("Process & Rename Files"):
      rename_zip_buffer = io.BytesIO()
      renamed_count = 0
      seen_names = {}

      with zipfile.ZipFile(
          rename_zip_buffer, "w", zipfile.ZIP_DEFLATED
      ) as zip_file:
        for original_name, content in rename_images:
          name_part, ext = os.path.splitext(original_name)

          if text_to_find:
            name_part = name_part.replace(text_to_find, text_replace)
          if remove_prefix and name_part.startswith(remove_prefix):
            name_part = name_part[len(remove_prefix) :]
          if remove_suffix and name_part.endswith(remove_suffix):
            name_part = name_part[: -len(remove_suffix)]
          if remove_last_n > 0:
            if len(name_part) > remove_last_n:
              name_part = name_part[:-remove_last_n]
            else:
              name_part = ""

          if case_option == "UPPERCASE":
            name_part = name_part.upper()
          elif case_option == "lowercase":
            name_part = name_part.lower()

          new_filename = name_part + ext

          # Prevent duplicate filename overwrites inside ZIP
          if new_filename in seen_names:
            seen_names[new_filename] += 1
            new_filename = f"{name_part}_{seen_names[new_filename]}{ext}"
          else:
            seen_names[new_filename] = 0

          zip_file.writestr(new_filename, content)
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

# ==========================================
# MODE 3: ORGANIZE PHOTOS BY STYLE ID
# ==========================================
elif app_mode == "📁 Organize Photos by Style ID (New)":
  st.header("📁 Create Style ID Folders & Sort Images")
  st.write(
      "Upload Excel and images (or a ZIP folder) to sort them automatically"
      " into Style ID folders, handling duplicates like `(2)`."
  )

  excel_file_3 = st.file_uploader(
      "Choose Excel file (.xlsx)", type=["xlsx"], key="style_excel"
  )

  if excel_file_3:
    try:
      df_style = pd.read_excel(excel_file_3)
      st.success("Excel loaded successfully!")

      cols = df_style.columns.tolist()
      c1, c2 = st.columns(2)
      with c1:
        style_col = st.selectbox(
            "Select STYLE ID Column:", cols, key="style_id_col"
        )
      with c2:
        name_col = st.selectbox(
            "Select Image/Reference Name Column (e.g. VAN/SKU):",
            cols,
            key="img_ref_col",
        )

      up_files_3 = st.file_uploader(
          "Upload individual image files:",
          type=["jpg", "jpeg", "png"],
          accept_multiple_files=True,
          key="style_images",
      )
      up_zip_3 = st.file_uploader(
          "OR Upload a ZIP file of images:", type=["zip"], key="style_zip"
      )

      uploaded_imgs_3 = load_uploaded_images(up_files_3, up_zip_3)

      if uploaded_imgs_3:
        st.info(f"Loaded {len(uploaded_imgs_3)} images.")

        if st.button("Generate Style Folders & Zip"):
          with st.spinner("Organizing into Style ID folders..."):
            mapping = {}
            for _, row in df_style.iterrows():
              s_id = str(row[style_col]).strip()
              r_val = str(row[name_col]).strip().upper()
              mapping[r_val] = s_id

            matched_count = 0
            zip_buffer_3 = io.BytesIO()
            seen_in_folder = {}

            with zipfile.ZipFile(
                zip_buffer_3, "w", zipfile.ZIP_DEFLATED
            ) as zip_file:
              for orig_name, content in uploaded_imgs_3:
                base_ext = os.path.splitext(orig_name)[0]
                clean_name = re.sub(r"\(\d+\)$", "", base_ext).strip().upper()

                if clean_name in mapping:
                  style_folder = mapping[clean_name]

                  # Handle duplicate names inside the same folder path
                  final_name = orig_name
                  folder_key = f"{style_folder}/{final_name}"
                  if folder_key in seen_in_folder:
                    seen_in_folder[folder_key] += 1
                    n_part, ext = os.path.splitext(orig_name)
                    final_name = f"{n_part}_{seen_in_folder[folder_key]}{ext}"
                  else:
                    seen_in_folder[folder_key] = 0

                  zip_path = f"{style_folder}/{final_name}"
                  zip_file.writestr(zip_path, content)
                  matched_count += 1

            zip_buffer_3.seek(0)
            st.success(
                f"Successfully sorted {matched_count} images into Style ID"
                " folders!"
            )

            st.download_button(
                label="📥 Download Style Folders (ZIP)",
                data=zip_buffer_3,
                file_name="Style_ID_Folders.zip",
                mime="application/zip",
            )

    except Exception as e:
      st.error(f"Error: {e}")
