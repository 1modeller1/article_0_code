import sys

import pandas as pd
import psycopg2

db_config = {}
with open("db_config.txt", "r") as file:
    for line in file:
        line = line.strip()
        if not line: continue
        key, value= line.split('=', 1)
        db_config[key] = value

connection = psycopg2.connect(**db_config)
cur = connection.cursor()

def update_table (code, year, main_code, koefs, name):
    b = koefs[koefs["code"] == code]["b"].tolist()[0]
    cur.execute(f"""
    with tab as (
        select
            (data ->> '{code}')::float8 as p1,
            (data ->> '{main_code}')::float8 as p2,
            {b} as b,
            inn
        from {name}_{year}_fix f
        where (data ->> '{code}')::float8 <> 0 and (data ->> '{main_code}')::float8 <> 0
    )
    update {name}_{year}_clean as fs
    set data_clean = jsonb_set(
        coalesce(fs.data_clean, '{{}}'::jsonb),
        '{{{code}}}',
        to_jsonb((p1 - b * p2)::float8),
        true
    )
    from tab as t
    where t.inn = fs.inn;
    """)
    connection.commit()

def gen_clean_table (year, main_code, codes_split, koefs, name):
    print(f" Gen clean table y{year} ".center(60, '='))
    for i, code in enumerate(codes_split):
        update_table(code, year, main_code, koefs, name)

        print(f"\r{i} / {len(codes_split)}", end="")
    print("")
    cur.close()
    connection.close()
