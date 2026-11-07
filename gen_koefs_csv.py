import math
import os
import psycopg2
import pandas as pd
from scipy.stats import t

folder = "koefs"

db_config = {}
with open("db_config.txt", "r") as file:
    for line in file:
        line = line.strip()
        if not line: continue
        key, value= line.split('=', 1)
        db_config[key] = value

connection = psycopg2.connect(**db_config)
cur = connection.cursor()

def get_koefs (code, year, main_code, name):
    cur.execute(f"""
        with tab as (
            select
                (data ->> '{code}')::float8  as p1,
                (data ->> '{main_code}')::float8 as p2
            from {name}_{year}_fix f
            where (data ->> '{code}')::float8 <> 0 and (data ->> '{main_code}')::float8 <> 0
        )
        select
            ( avg(p1 * p2) - avg(p1)*avg(p2) ) / nullif( avg(p2*p2) - avg(p2)*AVG(p2), 0 ) as b,
            avg(p1) - ( avg(p1 * p2) - avg(p1)*avg(p2) ) / nullif( avg(p2*p2) - avg(p2)*AVG(p2), 0 ) * avg(p2) as a,
            SUM(p2 * p2) - COUNT(*) * (AVG(p2) * AVG(p2)) as sst,
            count(*) as n
        from tab t;
    """)
    b, a, sst, n = cur.fetchall()[0]
    return [b, a, sst, n]

def get_koefs_other_year (code, year, main_code, name, name_year_parm):
    cur.execute(f"""
        with tab as (
            select
                (f.data ->> '{code}')::float8  as p1,
                (f2.data ->> '{main_code}')::float8 as p2
            from {name}_{year}_fix f
            join {name_year_parm[0]}_{name_year_parm[1]}_fix f2 on f.inn = f2.inn
            where (f.data ->> '{code}')::float8 <> 0 and (f2.data ->> '{main_code}')::float8 <> 0
        )
        select
            ( avg(p1 * p2) - avg(p1)*avg(p2) ) / nullif( avg(p2*p2) - avg(p2)*AVG(p2), 0 ) as b,
            avg(p1) - ( avg(p1 * p2) - avg(p1)*avg(p2) ) / nullif( avg(p2*p2) - avg(p2)*AVG(p2), 0 ) * avg(p2) as a,
            SUM(p2 * p2) - COUNT(*) * (AVG(p2) * AVG(p2)) as sst,
            count(*) as n
        from tab t;
    """)
    b, a, sst, n = cur.fetchall()[0]
    return [b, a, sst, n]

def get_mse (code, b, a, year, main_code, name):
    cur.execute(f"""
        with tab as (
            select
                (data ->> '{code}')::float8 as p1,
                (data ->> '{main_code}')::float8 as p2,
                {b} as b,
                {a} as a
            from {name}_{year}_fix f
            where (data ->> '{code}')::float8 <> 0 and (data ->> '{main_code}')::float8 <> 0
        )
        select
            sum( power((p1 -  a - b * p2), 2) ) / (count(*) - 2) as mse
        from tab t;
    """)
    return cur.fetchall()[0][0]

def get_mse_other_year (code, b, a, year, main_code, name, name_year_parm):
    cur.execute(f"""
        with tab as (
            select
                (f.data ->> '{code}')::float8 as p1,
                (f2.data ->> '{main_code}')::float8 as p2,
                {b} as b,
                {a} as a
            from {name}_{year}_fix f
            join {name_year_parm[0]}_{name_year_parm[1]}_fix f2 on f.inn = f2.inn
            where (f.data ->> '{code}')::float8 <> 0 and (f2.data ->> '{main_code}')::float8 <> 0
        )
        select
            sum( power((p1 -  a - b * p2), 2) ) / (count(*) - 2) as mse
        from tab t;
    """)
    return cur.fetchall()[0][0]

def gen_koefs_csv (year : int, codes, main_code, name, name_year_parm = None):
    print(f" Gen koefs csv y{year} ".center(60, '='))
    if name_year_parm:
        file_name = f"{name}_c{main_code}_MNK_factors_y{year}-{name_year_parm[1]}.csv"
    else:
        file_name = f"{name}_c{main_code}_MNK_factors_y{year}.csv"

    matrix = []
    for i, code in enumerate(codes):
        if code == main_code:
            koefs = {"code": code, "b": 1, "a": 0}
            matrix.append(koefs)
            continue
        try:
            if name_year_parm:
                b, a, sst, n = get_koefs_other_year(code, year, main_code, name, name_year_parm)
            else:
                b, a, sst, n = get_koefs(code, year, main_code, name)
            if not b:
                koefs = {"code" : code, "b" : 0, "a" : 0}
                matrix.append(koefs)
                continue
            if b == 1:
                koefs = {"code": code, "b": 1, "a": 0}
                matrix.append(koefs)
                continue
            if name_year_parm:
                mse = get_mse_other_year(code, b, a, year, main_code, name, name_year_parm)
            else:
                mse = get_mse(code, b, a, year, main_code, name)

            se = math.sqrt(mse / sst)
            t_factor = b / se
            p_val = 2 * (1 - t.cdf(abs(t_factor), n - 2))

            koefs = {"code" : code, "b" : b, "a" : a, "sst" : sst, "n" : n, "mse" : mse, "se" : se, "t_factor" : t_factor, "p_value" : p_val}
            matrix.append(koefs)
        except Exception as e:
            print(f"code : {code} | e : {e}")
        print(f"\r{i} / {len(codes)}", end="")
    print("")
    df = pd.DataFrame(matrix)
    df.to_csv(folder + '/' + file_name)
    # cur.close()
    # connection.close()
    return df