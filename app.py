import io
import os
import re
import zipfile
import pandas as pd
import openpyxl
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.styles import Alignment, Border, Side, Font, PatternFill
import streamlit as st

st.set_page_config(page_title="Photo Manager", layout="centered")

st.title("👕 Photo Manager Web App")

# Main Screen Options (Radio buttons for 5 features)
app_mode = st.radio(
    "Choose Mode:",
    [
        "📂 Sort & Filter Photos (Excel Match)",
        "✏️ Advanced Bulk Rename Photos",
        "📁 Organize Photos by Style ID (New)",
        "📊 Insert Images into Excel (Auto)",
        "🔄 Transfer Photos Between Excel Files (New)",
    ],
    horizontal=True,
)

st.markdown("---")


# Helper function to extract images from either single files or a ZIP upload
def load_uploaded_images(uploaded_files, uploaded_zip):
    image_list = []

    if uploaded_files:
        for f in uploaded_files:
            image_list.append((f.name, f.getvalue()))

    if uploaded_zip:
        try:
            with zipfile.ZipFile(uploaded_zip, "r") as z:
                for filename in z.namelist():
                    if filename.lower().endswith((".jpg", ".jpeg", ".png")) and not filename.startswith("__MACOSX/"):
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
        "Yeh option Excel aur images ko match karega, aur underscore `_` ya"
        " brackets `(2)` ke baad ke hisse ko ignore karke sahi folder mein dal dega."
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

                            r_val_clean = re.split(r"[_]", r_val)[0]
                            r_val_clean = re.sub(r"\(\d+\)$", "", r_val_clean).strip()
                            mapping[r_val_clean] = s_id

                        matched_count = 0
                        zip_buffer_3 = io.BytesIO()
                        seen_in_folder = {}

                        with zipfile.ZipFile(
                            zip_buffer_3, "w", zipfile.ZIP_DEFLATED
                        ) as zip_file:
                            for orig_name, content in uploaded_imgs_3:
                                base_ext = os.path.splitext(orig_name)[0]

                                clean_name = re.sub(r"\(\d+\)$", "", base_ext).strip()
                                clean_name = re.split(r"[_]", clean_name)[
                                    0
                                ].strip().upper()

                                if clean_name in mapping:
                                    style_folder = mapping[clean_name]

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
                            f"Successfully sorted {matched_count} images into Style ID folders!"
                        )

                        st.download_button(
                            label="📥 Download Style Folders (ZIP)",
                            data=zip_buffer_3,
                            file_name="Style_ID_Folders.zip",
                            mime="application/zip",
                        )

        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# MODE 4: INSERT IMAGES INTO EXCEL AUTOMATICALLY
# ==========================================
elif app_mode == "📊 Insert Images into Excel (Auto)":
    st.header("📊 Insert Photos Automatically into Excel")
    st.write(
        "Yahan apni Excel aur Photos upload karein. Photo ka size exact **Height: 3.16 inch, Width: 2.07 inch** set kiya jayega."
    )

    excel_file_4 = st.file_uploader(
        "Choose Excel file (.xlsx)", type=["xlsx"], key="excel_insert_file"
    )

    if excel_file_4:
        try:
            df_insert = pd.read_excel(excel_file_4)
            st.success("Excel loaded successfully!")

            cols_list = df_insert.columns.tolist()
            match_col = st.selectbox(
                "Select Style Name Column (jisse photo naam match hoga):",
                cols_list,
                key="match_col_name",
            )
            photo_col = st.selectbox(
                "Select Photo Column (jahan photo lagani hai):",
                cols_list,
                key="photo_col_name",
            )

            up_files_4 = st.file_uploader(
                "Upload individual pictures:",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key="insert_images",
            )
            up_zip_4 = st.file_uploader(
                "OR Upload a ZIP file of images:", type=["zip"], key="insert_zip"
            )

            uploaded_imgs_4 = load_uploaded_images(up_files_4, up_zip_4)

            if uploaded_imgs_4:
                st.info(f"Loaded {len(uploaded_imgs_4)} images.")

                if st.button("Generate Excel with Photos"):
                    with st.spinner("Inserting photos into Excel..."):
                        temp_excel_path = "temp_excel.xlsx"
                        excel_file_4.seek(0)
                        with open(temp_excel_path, "wb") as f:
                            f.write(excel_file_4.getvalue())

                        wb = openpyxl.load_workbook(temp_excel_path)
                        ws = wb.active

                        headers = [cell.value for cell in ws[1]]
                        match_col_idx = headers.index(match_col) + 1
                        photo_col_idx = headers.index(photo_col) + 1

                        img_dict = {}
                        for fname, content in uploaded_imgs_4:
                            b_name, _ = os.path.splitext(fname)
                            img_dict[b_name.strip().upper()] = content

                        inserted_count = 0

                        # Set cell sizes for exact fit: 3.16 inches height, 2.07 inches width
                        # 1 inch = 72 points roughly for height, width is characters width approx.
                        target_height_pts = 3.16 * 72
                        target_width_chars = 2.07 * 8  # approximate conversion for excel column width

                        photo_col_letter = openpyxl.utils.get_column_letter(photo_col_idx)
                        ws.column_dimensions[photo_col_letter].width = 25  # Fits 2.07 inches well

                        for row in range(2, ws.max_row + 1):
                            ws.row_dimensions[row].height = 230  # Fits 3.16 inches height safely
                            cell_val = ws.cell(row=row, column=match_col_idx).value

                            if cell_val is not None:
                                key_str = str(cell_val).strip().upper()
                                if key_str in img_dict:
                                    img_bytes = img_dict[key_str]
                                    img_io = io.BytesIO(img_bytes)

                                    img = OpenpyxlImage(img_io)
                                    # Set image exact dimensions in pixels (approx 1 inch = 96 pixels for screen/images)
                                    img.height = int(3.16 * 96)
                                    img.width = int(2.07 * 96)

                                    ws.add_image(img, f"{photo_col_letter}{row}")
                                    inserted_count += 1

                        output_excel_buffer = io.BytesIO()
                        wb.save(output_excel_buffer)
                        output_excel_buffer.seek(0)

                        st.success(f"Successfully inserted {inserted_count} photos into Excel!")

                        st.download_button(
                            label="📥 Download Excel with Photos (.xlsx)",
                            data=output_excel_buffer,
                            file_name="Catalog_With_Exact_Size_Photos.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )

                        if os.path.exists(temp_excel_path):
                            os.remove(temp_excel_path)

        except Exception as e:
            st.error(f"Error: {e}")

# ==========================================
# MODE 5: TRANSFER PHOTOS BETWEEN EXCEL FILES (NEW)
# ==========================================
elif app_mode == "🔄 Transfer Photos Between Excel Files (New)":
    st.header("🔄 Transfer Photos from One Excel to Another")
    st.write(
        "Aapke paas do Excel files hain—ek jisme photos embedded hain, aur doosri jisme data hai. Ye tool common field/column name ke zariye photos ko doosri Excel mein transfer kar dega!"
    )

    source_excel = st.file_uploader(
        "1. Upload SOURCE Excel (Jisme photos already hain):", type=["xlsx"], key="src_excel"
    )
    target_excel = st.file_uploader(
        "2. Upload TARGET Excel (Jisme photos daalni hain):", type=["xlsx"], key="tgt_excel"
    )

    if source_excel and target_excel:
        try:
            # Load both workbooks
            wb_src = openpyxl.load_workbook(source_excel)
            ws_src = wb_src.active

            wb_tgt = openpyxl.load_workbook(target_excel)
            ws_tgt = wb_tgt.active

            src_headers = [cell.value for cell in ws_src[1]]
            tgt_headers = [cell.value for cell in ws_tgt[1]]

            st.success("Both Excel files loaded successfully!")

            c1, c2 = st.columns(2)
            with c1:
                src_match_col = st.selectbox("Source Style/Name Column:", src_headers, key="s_match")
                src_photo_col = st.selectbox("Source Photo Column (Jahan photos hain):", src_headers, key="s_photo")
            with c2:
                tgt_match_col = st.selectbox("Target Style/Name Column:", tgt_headers, key="t_match")
                tgt_photo_col = st.selectbox("Target Photo Column (Jahan photos lagani hain):", tgt_headers, key="t_photo")

            if st.button("Transfer Photos Now"):
                with st.spinner("Transferring photos between Excel files..."):
                    src_m_idx = src_headers.index(src_match_col) + 1
                    src_p_idx = src_headers.index(src_photo_col) + 1
                    
                    tgt_m_idx = tgt_headers.index(tgt_match_col) + 1
                    tgt_p_idx = tgt_headers.index(tgt_photo_col) + 1

                    # Extract images from source workbook mapped by row/name
                    # openpyxl stores images with their anchor cell information
                    transferred_count = 0
                    
                    # Create a dictionary mapping style name from source to image object/stream
                    src_images_map = {}
                    for img in ws_src._images:
                        # Find which row the image belongs to
                        row_idx = img.anchor._from.row + 1 # openpyxl 0-indexed row to 1-indexed
                        val = ws_src.cell(row=row_idx, column=src_m_idx).value
                        if val is not None:
                            src_images_map[str(val).strip().upper()] = img

                    # Set column width and row height in target workbook
                    tgt_photo_letter = openpyxl.utils.get_column_letter(tgt_p_idx)
                    ws_tgt.column_dimensions[tgt_photo_letter].width = 25

                    for row in range(2, ws_tgt.max_row + 1):
                        ws_tgt.row_dimensions[row].height = 230
                        tgt_val = ws_tgt.cell(row=row, column=tgt_m_idx).value
                        
                        if tgt_val is not None:
                            key_str = str(tgt_val).strip().upper()
                            if key_str in src_images_map:
                                original_img = src_images_map[key_str]
                                
                                # Duplicate/re-create image for target
                                img_io = io.BytesIO(original_img._data())
                                new_img = OpenpyxlImage(img_io)
                                new_img.height = int(3.16 * 96)
                                new_img.width = int(2.07 * 96)

                                ws_tgt.add_image(new_img, f"{tgt_photo_letter}{row}")
                                transferred_count += 1

                    output_buffer = io.BytesIO()
                    wb_tgt.save(output_buffer)
                    output_buffer.seek(0)

                    st.success(f"Successfully transferred {transferred_count} photos from Source to Target Excel!")

                    st.download_button(
                        label="📥 Download Transferred Excel File",
                        data=output_buffer,
                        file_name="Target_Catalog_With_Transferred_Photos.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

        except Exception as e:
            st.error(f"Error during photo transfer: {e}")
