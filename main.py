import pandas as pd
import psycopg2
import os
from create_tables import *
from gen_fix_table import gen_fix_table_split, gen_fix_table # split - с генерацией индивидуальных коэффициентов для положительных и отрицательных значений
from gen_koefs_csv import gen_koefs_csv
from gen_clean_table import gen_clean_table
from gen_corrs_csv import gen_corrs_csv

# ===============================

year = 2020
okved = "" # При пустом значении берутся все ОКВЭД, если заполнять, то более низкоуровневые оквэд войдут в группу более высокого уровня
# Например: ОКВЭД "01" включит в себя ОКВЭДы: "01", "01.1", "01.11.2"
main_table = "fin_data"
name = "fin" # Для идентификации при создании отличающихся друг от друга таблиц
# (если отличаются только: год, оквэд, то менять параметр не обязательно, а вот если меняли код в скрипте, то лучше это обозначить в названии)
main_code = "1600" # 1600 для gen_fix_table и 1600p для gen_fix_table_split

name_year_parm = None
# name_year_parm = ["fin", 2019] # Требуется существование table_fix соответствующего года. Можно отключить, указав None
# ВАЖНО: советую явно обозначить использование данного параметра в "name", поскольку он автоматически не подставляется в название

to_do_list = {
    "fix"   : True, # Таблица без выбросов, с починенными положительными/отрицательными значениями
    "koefs" : True,  # По методу наименьших квадратов генерируются коэффициенты a и b для уравнений code = a + b * main_code
    "clean" : True,  # Мера влияния main_code на каждый code вычитается: code_clean = code - b * main_code
    "corrs" : True   # Парные корреляции между каждыми двумя code_clean
}

drop_tables_at_end = {
    "pure" : False,  # Создается в начале для более быстрой обработки следующей таблицы (сырые данные)
    "fix"  : False,  # Содержит очищенные от выбросов и неправильных знаков данные
    "clean" : False  # Содержит очищенные от влияния main_code данные
}

# ===============================
name = f"{name}_{okved}"
name = name.rstrip("_")

def vacuum_full_table (table):
    connection_v = psycopg2.connect(**db_config)
    connection_v.autocommit = True
    cursor_v = connection_v.cursor()
    try:
        cursor_v.execute(f"vacuum full {table}")
    except Exception as e:
        print(f"Failed vacuum full {table} : {e}")
    finally:
        cursor_v.close()
        connection_v.close()

def get_actual_codes (year):
    cur.execute(f"""
        SELECT DISTINCT jsonb_object_keys(data) AS key
        FROM {name}_{year}_fix;
    """)

    codes_actual = [a[0] for a in cur.fetchall()]
    codes_actual.sort()
    if all(str(x).lstrip("-").isdigit() for x in codes_actual):
        codes_actual = [int(x) for x in codes_actual]

    return codes_actual

db_config = {}
with open("db_config.txt", "r") as file:
    for line in file:
        line = line.strip()
        if not line: continue
        key, value= line.split('=', 1)
        db_config[key] = value

if okved == "":
    create_fin_table(year, main_table, name)
else:
    create_fin_table_with_okved(year, main_table, name, okved)

codes = pd.read_csv("counts.csv")
codes = codes[codes["count"] > 10_000]
codes = codes["code"].tolist()

fix_list = pd.read_csv("codes_plus_minus.csv")
fix_list = fix_list.set_index("code")
fix_dict = {key : fix_list.loc[key, "sign"] for key in fix_list.index}
del fix_list

# ==== no blows, fix +-, (split) ====
if to_do_list["fix"]:
    drop_fix_table(year, name)

    create_fix_table(year, name)
    gen_fix_table(year, codes, fix_dict, name)
    # gen_fix_table_split(year, codes, fix_dict, name)
    vacuum_full_table(f"{name}_{year}_fix")

# ============= koefs =============
if to_do_list["koefs"]:
    if not os.path.isdir("koefs"):
        os.mkdir("koefs")

    codes_actual = get_actual_codes(year)

    koefs = gen_koefs_csv(year, codes_actual, main_code, name, name_year_parm)
    koefs = koefs.set_index("code")

# ======== clean - no main_code =======
if to_do_list["clean"]:
    drop_clean_table(year, name)
    if not to_do_list["koefs"]:
        codes_actual = get_actual_codes(year)
        if name_year_parm:
            koefs = pd.read_csv(f"koefs/{name}_c{main_code}_MNK_factors_y{year}-{name_year_parm[1]}.csv")
        else:
            koefs = pd.read_csv(f"koefs/{name}_c{main_code}_MNK_factors_y{year}.csv")
        koefs = koefs.set_index("code")

    create_clean_table(year, name)
    # gen_clean_table(year, main_code, codes_actual, koefs, name, name_year_parm)
    gen_clean_table(year, main_code, codes_actual, koefs, name, name_year_parm)
    vacuum_full_table(f"{name}_{year}_clean")

# ========= corrs and counts =======
if to_do_list["corrs"]:
    if not os.path.isdir("corrs"):
        os.mkdir("corrs")

    gen_corrs_csv(year, codes, name)

if any([drop_tables_at_end[key] for key in drop_tables_at_end]):
    print(" Drop tables ".center(60, "="))
for key in drop_tables_at_end:
    if drop_tables_at_end[key]:
        key = "" if key == "pure" else key
        table = f"{name}_{year}_{key}"
        table = table.rstrip("_")
        drop_table(table)

print("ALL DONE".center(60))