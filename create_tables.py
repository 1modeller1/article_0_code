import psycopg2, re

db_config = {}
with open("db_config.txt", "r") as file:
    for line in file:
        line = line.strip()
        if not line: continue
        key, value= line.split('=', 1)
        db_config[key] = value

connection = psycopg2.connect(**db_config)
cur = connection.cursor()

def create_fin_table (year, main_table, name):
    cur.execute(f"""
    create table if not exists {name}_{year}
    as
    select
        inn,
        data
    from {main_table}
    where year = {year};
    
    alter table {name}_{year}
    add column if not exists data jsonb;
    """)
    connection.commit()


def create_fin_table_with_okved(year, main_table, name, okved):
    substring = re.sub(r"\d", r"\\d", okved)
    cur.execute(f"""
    create table if not exists {name}_{year}
    as
    select
        inn,
        data
    from {main_table}
    where year = {year}
    and substring(okved_main from '{substring}') = '{okved}';

    alter table {name}_{year}
    add column if not exists data jsonb;
    """)
    connection.commit()

def create_fix_table (year, name):
    cur.execute(f"""
    create table if not exists {name}_{year}_fix
    as
    select
        inn
    from {name}_{year};

    alter table {name}_{year}_fix
    add column if not exists data jsonb;
    """)
    connection.commit()

def create_clean_table (year, name):
    cur.execute(f"""
    create table if not exists {name}_{year}_clean
    as
    select
        inn
    from {name}_{year}_fix;

    alter table {name}_{year}_clean
    add column if not exists data_clean jsonb;
    """)
    connection.commit()

def drop_fix_table(year, name):
    cur.execute(f"""
    drop table if exists {name}_{year}_fix;
    """)
    connection.commit()

def drop_clean_table(year, name):
    cur.execute(f"""
    drop table if exists {name}_{year}_clean;
    """)
    connection.commit()

def drop_table (table):
    # cur.execute(f"""
    # drop table if exists {table};
    # """)
    # connection.commit()
    connection_v = psycopg2.connect(**db_config)
    connection_v.autocommit = True
    cursor_v = connection_v.cursor()
    try:
        cursor_v.execute(f"drop table if exists {table}")
    except Exception as e:
        print(f"Drop table {table} : {e}")
    finally:
        cursor_v.close()
        connection_v.close()