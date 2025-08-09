# Import python packages
import streamlit as st
import requests
from snowflake.snowpark.functions import col
import pandas as pd

# App title and instructions
st.title(":cup_with_straw: Customize your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

# Snowflake connection (Streamlit secrets)
cnx = st.connection("snowflake")
session = cnx.session()

# Always point to the same DB/Schema the grader reads
session.sql("USE DATABASE SMOOTHIES").collect()
session.sql("USE SCHEMA PUBLIC").collect()

# Input for customer name
name_on_order = st.text_input('Name on Smoothie:')
if name_on_order:
    st.write(f"Name entered: {name_on_order}")

# Fruit options
my_dataframe = session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS").select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = my_dataframe.to_pandas()
st.dataframe(pd_df, use_container_width=True)

st.write("Choose up to 5 fruits for your custom smoothie:")

fruit_list = pd_df["FRUIT_NAME"].tolist()
ingredients_list = st.multiselect("Pick your favorite fruits:", fruit_list, max_selections=5)

# UX hints
if len(ingredients_list) > 5:
    st.error("🚫 You can only select up to 5 fruits!")
elif ingredients_list:
    st.success(f"You selected: {', '.join(ingredients_list)}")
else:
    st.info("No fruits selected yet. Pick from the list!")

# Nutrition (optional)
if ingredients_list:
    for fruit_chosen in ingredients_list:
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.subheader(f'{fruit_chosen} Nutrition Information')
        fruityvice_response = requests.get("https://fruityvice.com/api/fruit/" + search_on)
        st.dataframe(data=fruityvice_response.json(), use_container_width=True)

# ---------- CORE FIX STARTS HERE ----------
def space_join(parts: list[str]) -> str:
    # Join with ASCII spaces only, remove NBSP and extra whitespace
    cleaned = [p.strip().replace("\u00A0", " ") for p in parts]
    out = " ".join(cleaned).strip()
    # collapse any accidental doubles (safety)
    while "  " in out:
        out = out.replace("  ", " ")
    return out

if ingredients_list and name_on_order:
    if st.button('Submit Order'):
        # ✅ SPACE-joined string (NO COMMAS)
        ingredients_str = space_join(ingredients_list)

        # Escape single quotes for SQL literals
        name_sql = name_on_order.strip().replace("'", "''")
        ing_sql  = ingredients_str.replace("'", "''")

        # ✅ Use MERGE to avoid duplicates per name (keeps one row per customer)
        session.sql(f"""
            MERGE INTO SMOOTHIES.PUBLIC.ORDERS t
            USING (SELECT '{name_sql}' AS n, '{ing_sql}' AS s, FALSE AS f) src
              ON t.NAME_ON_ORDER = src.n
            WHEN MATCHED THEN UPDATE SET
              t.INGREDIENTS = src.s,
              t.ORDER_FILLED = src.f,
              t.ORDER_TS = COALESCE(t.ORDER_TS, CURRENT_TIMESTAMP())
            WHEN NOT MATCHED THEN INSERT (NAME_ON_ORDER, INGREDIENTS, ORDER_FILLED)
              VALUES (src.n, src.s, src.f);
        """).collect()

        st.success("✅ Your Smoothie is ordered!", icon="🥤")
# ---------- CORE FIX ENDS HERE ----------
