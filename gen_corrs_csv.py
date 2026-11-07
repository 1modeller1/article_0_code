import sys
import psycopg2
import pandas as pd

folder = "corrs"

db_config = {}
with open("db_config.txt", "r") as file:
    for line in file:
        line = line.strip()
        if not line: continue
        key, value= line.split('=', 1)
        db_config[key] = value

connection = psycopg2.connect(**db_config)
cur = connection.cursor()

def corr_run (row_1, row_2, year, name):
    cur.execute(f"""
        with tab as (
            select
            coalesce( data_clean ->> '{str(row_1) + 'p'}', data_clean ->> '{str(row_1) + 'm'}', data_clean ->> '{row_1}')::float8 as p1,
            coalesce( data_clean ->> '{str(row_2) + 'p'}', data_clean ->> '{str(row_2) + 'm'}', data_clean ->> '{row_2}')::float8 as p2
            from {name}_{year}_clean as f
        )
        select
            corr (p1, p2),
            count(*)
        from tab
        where p1 <> 0 and p2 <> 0;
    """)
    return cur.fetchall()[0]

def export_csv (matrix:list, name:str):
    df = pd.DataFrame(matrix)
    cols = ["code"] + [c for c in df.columns if c != "code"]
    df = df[cols]

    df = df.drop_duplicates(subset=["code"], keep="last")
    df.to_csv(folder + '/' + name)

def gen_corrs_csv (year, codes, name):
    print(f" Gen corrs csv y{year} ".center(60, '='))
    file_name_corr = f"{name}_corrs_y{year}_clean.csv"
    file_name_count = f"{name}_corrs_y{year}_clean_count.csv"
    matrix_corr = []
    matrix_count = []

    l = len(codes)
    c = int(l * (l + 1) / 2)
    w = 0
    for i, code_0 in enumerate(codes):
        row_corr = {"code" : code_0}
        row_count = {"code" : code_0}
        for j, code_1 in enumerate(codes):
            if j < i:
                continue
            w += 1
            corr, count = corr_run(code_0, code_1, year, name)
            row_corr[code_1] = corr
            row_count[code_1] = count
            if j % 10 == 0:
                print(f"\r{w} / {c}  ({round(w / c * 100)}%)", end = "")
        matrix_corr.append(row_corr)
        matrix_count.append(row_count)

    export_csv(matrix_corr, file_name_corr)
    export_csv(matrix_count, file_name_count)
    print("")
    # cur.close()
    # connection.close()

