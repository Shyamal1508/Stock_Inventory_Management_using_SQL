import streamlit as st
import numpy as np
import pandas as pd
from db_functions import (
    connect_to_db, get_basic_info, get_additional_tables, 
    get_categories, get_supplier, add_new_manual_id, 
    get_all_products, get_products_history, place_reorder,
    get_pending_reorders,mark_reorder_as_received
)


st.sidebar.title("Inventory Management Dashboard")
option = st.sidebar.radio("Select option:", ["Basic information", "Operational Tasks"])

st.title("Inventory and supply chain dashboard")
db = connect_to_db()
cursor = db.cursor(dictionary=True)

# Basic information
if option == "Basic information":
    st.header("Basic metrics")
    basic_info = get_basic_info(cursor)

    cols = st.columns(3)
    keys = list(basic_info.keys())

    for i in range(min(3, len(keys))):
        cols[i].metric(label=keys[i], value=basic_info[keys[i]])
    
    cols = st.columns(3)
    for i in range(3, min(5, len(keys))):
        cols[i-3].metric(label=keys[i], value=basic_info[keys[i]])

    st.divider()
    tables = get_additional_tables(cursor)
    for label, data in tables.items():
        st.header(label)
        df = pd.DataFrame(data)
        st.dataframe(df)
        st.divider()

elif option == "Operational Tasks":
    st.header("Operational Tasks")
    select_task = st.selectbox("Choose a task", ["Add new Product", "Product History", "Place Order", "Receive Reorder","Place Reorder"])
    
    if select_task == "Add new Product":
        categories = get_categories(cursor)
        suppliers = get_supplier(cursor)    
     
        with st.form("Add_Product_Form"):
            product_name = st.text_input("Product Name")
            product_category = st.selectbox("Category", categories)
            product_price = st.number_input("Price", min_value=0.00)
            product_stock = st.number_input("Stock Quantity", min_value=0, step=1)
            product_level = st.number_input("Reorder Level", min_value=0, step=1)

            supplier_ids = [s["supplier_id"] for s in suppliers]
            supplier_names = [s["supplier_name"] for s in suppliers]

            supplier_id = st.selectbox("Supplier", options=supplier_ids, format_func=lambda x: supplier_names[supplier_ids.index(x)])
            submitted = st.form_submit_button("Add Product")

            if submitted:
                if not product_name:
                    st.error("Please enter the product name")
                else:
                    try:
                        add_new_manual_id(cursor, db, product_name, product_category, product_price, product_stock, product_level, supplier_id)
                        st.success(f"Product: {product_name} added successfully")
                    except Exception as e:
                        st.error(f"Error adding product: {e}")

    if select_task == "Product History":
        st.header("Product Inventory History")
        products = get_all_products(cursor)
        product_names = [p["product_name"] for p in products]
        product_id_list = [p["product_id"] for p in products]

        selected_product_name = st.selectbox("Select Product", options=product_names)
        if selected_product_name:
            selected_product_id = product_id_list[product_names.index(selected_product_name)]
            history = get_products_history(cursor, selected_product_id)
            if history:
                df = pd.DataFrame(history)
                st.dataframe(df)
            else:
                st.info("No inventory history found for the selected product.")

    if select_task == "Place Reorder":
        st.header("Place a Reorder")
        products = get_all_products(cursor)
        product_names = [p["product_name"] for p in products]
        product_ids = [p["product_id"] for p in products]

        # FIX: Changed 'options=product_name' (singular/input string) to 'product_names' (list)
        selected_product_name = st.selectbox("Select Product to Reorder", options=product_names)
        reorder_qty = st.number_input("Reorder Quantity", min_value=1, step=1)
        
        if st.button("Place Reorder"):
            if not selected_product_name:
                st.error("Please select a product")
            elif reorder_qty <= 0:
                st.error("Reorder quantity must be greater than zero")
            else:
                selected_product_id = product_ids[product_names.index(selected_product_name)]
                try:
                    place_reorder(cursor, db, selected_product_id, reorder_qty)
                    st.success(f"Order placed for {selected_product_name} (ID: {selected_product_id}) with quantity {reorder_qty}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error placing reorder: {e}")
    if select_task=="Receive Reorder":
        st.header("Mark Reorder as Received") 
        pending_reorders=get_pending_reorders(cursor)  
        if not pending_reorders:
            st.info("No pending reorders found")
        else:
            reorder_ids=[r["reorder_id"] for r in pending_reorders]    
            reorder_label=[f"ID {r['reorder_id']} - {r['product_name']}" for r in pending_reorders]
            select_label=st.selectbox("Select reorder to mark as received",options=reorder_label)

            if select_label:
                selected_reorder_id=reorder_ids[reorder_label.index(select_label)]

                if st.button("Mark as Received"):
                    try:
                        mark_reorder_as_received(cursor,db,selected_reorder_id)
                        st.success(f"Mark reorder {selected_reorder_id} as received ")
                    except Exception as e:
                        st.error(f"Error {e}")
                    

                
 




       
  
