import streamlit as st
import pandas as pd

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Bill Category Finder",
    layout="wide"
)

st.title("🔍 Bill Category Finder")
st.write("Upload your sales Excel file and search for categories.")

# -----------------------------
# Upload File
# -----------------------------
uploaded = st.file_uploader(
    "Upload Excel File",
    type=["xls", "xlsx"]
)

if uploaded is not None:

    # -----------------------------
    # Read Excel (tries different headers)
    # -----------------------------
    df = None

    for header_row in [0, 1, 2, 3]:
        try:
            uploaded.seek(0)

            temp = pd.read_excel(uploaded, header=header_row)

            cols = {str(c).strip().lower(): c for c in temp.columns}

            if "billno" in cols and "category" in cols:

                df = temp.rename(columns={
                    cols["billno"]: "BillNo",
                    cols["category"]: "Category"
                })

                break

        except:
            pass

    if df is None:
        st.error("Could not find BillNo and Category columns.")
        st.stop()

    # -----------------------------
    # Clean Data
    # -----------------------------
    df["Category"] = (
        df["Category"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    df["BillNo"] = (
        df["BillNo"]
        .fillna("")
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )

    df = df[df["Category"] != ""]

    # -----------------------------
    # Combine Categories Bill-wise
    # -----------------------------
    grouped = (
        df.groupby("BillNo")
        .agg(
            CombinedCategories=(
                "Category",
                lambda x: ", ".join(sorted(set(x)))
            )
        )
        .reset_index()
    )

    # -----------------------------
    # Build category lookup
    # -----------------------------
    category_sets = (
        df.groupby("BillNo")["Category"]
        .apply(lambda x: set(x))
        .to_dict()
    )

    # -----------------------------
    # Search Box
    # -----------------------------
    search = st.text_input(
        "Search Category",
        placeholder="Example: bio or bio, acti"
    )

    if search:

        # Split multiple search terms
        wanted = [
            x.strip().upper()
            for x in search.split(",")
            if x.strip()
        ]

        matched_bills = []

        for bill, cats in category_sets.items():

            match = True

            for word in wanted:

                # Partial match
                found = any(word in cat for cat in cats)

                if not found:
                    match = False
                    break

            if match:
                matched_bills.append(bill)

        result = grouped[
            grouped["BillNo"].isin(matched_bills)
        ]

        st.subheader(f"Results ({len(result)})")

        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.subheader("All Bills")

        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )