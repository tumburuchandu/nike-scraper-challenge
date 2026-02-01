import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- SETUP ---
URL = "https://qqphryasfpifeqsxztnw.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFxcGhyeWFzZnBpZmVxc3h6dG53Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5MjkzMDgsImV4cCI6MjA4NTUwNTMwOH0.U65-NR_C4JHG9b7O9HoYFyCmp_KZ9zrNZesQ-NC9g-8"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Nike Data Scraper", layout="wide")

st.title("👟 Nike Scraped Product Catalog")

# --- FETCH DATA ---
@st.cache_data
def load_data():
    try:
        # Fetch data from Supabase
        response = supabase.table("products").select("*").execute()
        data = response.data
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()

df = load_data()

# --- VALIDATION ---
if df.empty:
    st.warning("⚠️ No data found. Please check if your Supabase table 'products' has rows and if RLS policies allow public access.")
    st.info("💡 Run this in Supabase SQL Editor: ALTER TABLE products DISABLE ROW LEVEL SECURITY;")
else:
    # Normalize column names (removes spaces and cases issues)
    # This maps your exact CSV headers to the logic below
    cols = df.columns.tolist()

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filter Products")
    
    # Safe check for Product_Tagging
    tag_col = "Product_Tagging"
    if tag_col in df.columns:
        tag_options = df[tag_col].dropna().unique()
        selected_tags = st.sidebar.multiselect("Select Tagging", options=tag_options)
        if selected_tags:
            df = df[df[tag_col].isin(selected_tags)]
    else:
        st.sidebar.warning(f"Column '{tag_col}' not found in database.")

    # --- MAIN TABLE VIEW ---
    st.subheader("Product Overview")
    st.write(f"Showing {len(df)} products. Click a row to see full details.")

    # column_config protects against errors if a column is missing
    safe_config = {
        "Product_Image_URL": st.column_config.ImageColumn("Image"),
        "Product_URL": st.column_config.LinkColumn("Nike Link"),
        "Product_Name": "Name",
        "Discount_Price": "Price",
        "Rating_Score": "⭐ Rating"
    }
    
    # Only configure columns that actually exist in the dataframe
    active_config = {k: v for k, v in safe_config.items() if k in df.columns}

    event = st.dataframe(
        df,
        column_config=active_config,
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    # --- DETAIL VIEW ---
    if event.selection.rows:
        selected_index = event.selection.rows[0]
        row = df.iloc[selected_index]
        
        st.divider()
        col1, col2 = st.columns([1, 2])
        
        with col1:
            img_url = row.get("Product_Image_URL", "")
            if img_url:
                st.image(img_url, use_container_width=True)
        
        with col2:
            st.header(row.get("Product_Name", "N/A"))
            st.write(f"**Description:** {row.get('Product_Description', 'No description available.')}")
            
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.write(f"**Style Code:** {row.get('Style_Code', 'N/A')}")
                st.write(f"**Color Shown:** {row.get('Color_Shown', 'N/A')}")
                st.write(f"**Sizes:** {row.get('Sizes_Available', 'N/A')}")
            with d_col2:
                st.write(f"**Vouchers:** {row.get('Vouchers', 'None')}")
                st.write(f"**Rating:** {row.get('Rating_Score', 'N/A')} ({row.get('Review_Count', '0')} reviews)")
                st.write(f"**Original Price:** {row.get('Original_Price', 'N/A')}")