# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col, when_matched

# Helpful documentation links
helpful_links = [
    "https://docs.streamlit.io",
    "https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit",
    "https://github.com/Snowflake-Labs/snowflake-demo-streamlit",
    "https://docs.snowflake.com/en/release-notes/streamlit-in-snowflake"
]

# App title and instructions
st.title(":cup_with_straw: Customize your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your custom Smoothie!")

cnx = st.connection("snowflake")  # Uses Snowflake connection from Streamlit secrets
session = cnx.session()
# Input for customer name
name_on_order = st.text_input('Name on Smoothie:')
if name_on_order:
    st.write(f"Name entered: {name_on_order}")

# Establish Snowflake session and fetch fruit options
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'))

# Instruction for selecting fruits
st.write("Choose up to 5 fruits for your custom smoothie:")

# Convert fruits to list for multiselect
fruit_list = my_dataframe.to_pandas()["FRUIT_NAME"].tolist()
ingredients_list = st.multiselect(
    "Pick your favorite fruits:",
    fruit_list,
    max_selections=5
)

# Enforce max 5 selection manually
if len(ingredients_list) > 5:
    st.error("🚫 You can only select up to 5 fruits!")
elif ingredients_list:
    st.success(f"You selected: {', '.join(ingredients_list)}")
else:
    st.info("No fruits selected yet. Pick from the list!")

# ✅ Submit order when ready
if ingredients_list and name_on_order:
    if st.button('Submit Order'):
        ingredients_str = ', '.join(ingredients_list).strip()
        
        # ✅ Correct insert (exclude auto-generated fields)
        insert_stmt = f"""
            INSERT INTO SMOOTHIES.PUBLIC.ORDERS 
            (NAME_ON_ORDER, INGREDIENTS)
            VALUES ('{name_on_order}', '{ingredients_str}')
        """
        
        session.sql(insert_stmt).collect()
        st.success("✅ Your Smoothie is ordered!", icon="🥤")
import requests

smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")

# Optional: show raw response
st.text(smoothiefroot_response)

# Optional: show parsed JSON
if smoothiefroot_response.status_code == 200:
    fruit_data = smoothiefroot_response.json()
    st.write(fruit_data)
else:
    st.error(f"Error {smoothiefroot_response.status_code}: Could not fetch data")
