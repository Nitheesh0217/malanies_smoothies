# Import python packages
import streamlit as st
import requests
from snowflake.snowpark.functions import col
import pandas as pd
from urllib.parse import quote_plus
import re

st.title(":cup_with_straw: Customize your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

cnx = st.connection("snowflake")
session = cnx.session()

# Name input
name_on_order = st.text_input("Name on Smoothie:")

# Pull FRUIT_OPTIONS (GUI label + API search term)
sp_df = session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS").select(col("FRUIT_NAME"), col("SEARCH_ON"))
pd_df = sp_df.to_pandas()

# Multiselect from GUI labels
ingredients_list = st.multiselect(
    "Pick your favorite fruits:",
    options=pd_df["FRUIT_NAME"].tolist(),
    max_selections=5,
)

if ingredients_list:
    # Show per-fruit nutrition using SEARCH_ON mapping
    for fruit_chosen in ingredients_list:
        # lookup SEARCH_ON (fallback to label if missing)
        match = pd_df.loc[pd_df["FRUIT_NAME"] == fruit_chosen, "SEARCH_ON"]
        search_on = match.iloc[0] if not match.empty and pd.notna(match.iloc[0]) else fruit_chosen

        st.subheader(f"{fruit_chosen} Nutrition Information")
        url = f"https://my.smoothiefroot.com/api/fruit/{quote_plus(str(search_on))}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 404:
                st.info(f"'{search_on}' isn’t in SmoothieFroot.")
                continue
            r.raise_for_status()
            st.dataframe(r.json(), use_container_width=True)
        except requests.RequestException as e:
            st.error(f"API call failed for {fruit_chosen}: {e}")

# ✅ Submit order when ready (store GUI labels, space-separated)
if ingredients_list and name_on_order and st.button("Submit Order"):
    # join with single ASCII spaces and sanitize
    ingredients_str = " ".join(ingredients_list)
    ingredients_str = ingredients_str.replace("\u00A0", " ")            # kill NBSP
    ingredients_str = re.sub(r"\s+", " ", ingredients_str).strip()      # collapse spaces
    safe_name = name_on_order.replace("'", "''")
    safe_ing  = ingredients_str.replace("'", "''")

    insert_stmt = f"""
        INSERT INTO SMOOTHIES.PUBLIC.ORDERS (NAME_ON_ORDER, INGREDIENTS)
        VALUES ('{safe_name}', '{safe_ing}')
    """
    session.sql(insert_stmt).collect()
    st.success("✅ Your Smoothie is ordered!", icon="🥤")
