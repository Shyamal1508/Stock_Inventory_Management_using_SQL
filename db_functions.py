import mysql.connector
def connect_to_db():
    return mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="new_schema",
    allow_local_infile=True,
    # Add these two lines below:
    auth_plugin='mysql_native_password' # Force the driver to use the method you just set
)
def get_basic_info(cursor):
    queries={
    "Total supplier": "select count(*) as Total_supplier from suppliers;",
    "Total product": "select count(*) as Total_product from products;",
    "Total Category": "select count(distinct category) as total_category from products;",
    "Total sales value made in last  3 months":"""select round(sum(abs(se.change_quantity)*p.price),2) as total_sales_in_last_3_months from stock_entries as se 
 join products as p
 on se.product_id=p.product_id
 where se.change_type="Sale"
 and se.entry_date>=
 (
   select date_sub(max(entry_date),interval 3 month )from stock_entries
);
""",
"Below reorder and no pending reorder":"""select count(*) from
products as p
where p.stock_quantity<p.reorder_level and
product_id not in
(
select distinct product_id from reorders where status="pending"
)""",
}
    result={}
    for label,query in queries.items():
        cursor.execute(query)
        row=cursor.fetchone()
        result[label]=list(row.values())[0]
    return result


def get_additional_tables(cursor):
    queries={
        " supplier and their contact details":"select supplier_name,contact_name,email,phone from suppliers;",
        "product with supplier and stock":"""select p.product_name,s.supplier_name,p.stock_quantity,p.reorder_level from suppliers s join  products p on
s.supplier_id=p.supplier_id
order by p.product_name;""",
    "product needing reorder":"""select product_id,product_name,stock_quantity,reorder_level from products
where stock_quantity<reorder_level;""",
    }
    tables={}   
    for label,query in queries.items():
        cursor.execute(query)
        tables[label]=cursor.fetchall()
    return tables    
def get_categories(cursor):
    cursor.execute("select distinct category from products order by category asc")
    rows=cursor.fetchall()
    return [row["category"] for row in rows]
def get_supplier(cursor):
    cursor.execute("select supplier_id,supplier_name from suppliers order by supplier_name asc")
    return cursor.fetchall()
def add_new_manual_id(cursor,db,p_name,p_category,p_price,p_stock,p_reorder,p_supplier):
   
    proc_call="call AddNewProductManualID(%s,%s,%s,%s,%s,%s)"
    paras=(p_name,p_category,p_price,p_stock,p_reorder,p_supplier)
    cursor.execute(proc_call,paras)
    db.commit()
def get_categories(cursor):
    cursor.execute("select distinct category from products order by category asc")
    rows=cursor.fetchall()
    return [row["category"] for row in rows] 
def get_all_products(cursor):
    cursor.execute("select product_id,product_name from products order by product_name")
    return cursor.fetchall()


def get_products_history(cursor,product_id):
    query="select * from product_inventory_history where product_id= %s order by record_date desc "
    cursor.execute(query,(product_id,))
    return cursor.fetchall()

def place_reorder(cursor,db,product_id,quantity):
    query="""
            insert into reorders (reorder_id,product_id,reorder_quantity,reorder_date,status)
            select max(reorder_id)+1,
            %s,
            %s,
            curdate(),
            "Ordered"
            from reorders;
    """
    cursor.execute(query,(product_id,quantity))
    db.commit()
def get_pending_reorders(cursor):
    cursor.execute("""select r.reorder_id,p.product_name
                   from reorders as r join products as p
                   on r.product_id=p.product_id
    """)
    return cursor.fetchall()

def mark_reorder_as_received(cursor,db,reorder_id):
    cursor.callproc("MarkReorderAsReceived",[reorder_id])
    db.commit()
   