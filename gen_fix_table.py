import pandas as pd
import psycopg2
import sys

db_config = {}
with open("db_config.txt", "r") as file:
    for line in file:
        line = line.strip()
        if not line: continue
        key, value= line.split('=', 1)
        db_config[key] = value

connection = psycopg2.connect(**db_config)
cur = connection.cursor()

def gen_exceptions (code, bad_values):
    return ' and '.join([f"code(data, '{code}') <> {value}" for value in bad_values])

def get_bad_values (code, year, name):
    cur.execute(f"""
    select
        value
    from (
        select
            count(*) as c,
            count(*) * 100 / sum(count(*)) over () as c_p,
            code(data, '{code}') as value
        from {name}_{year}
        where code(data, '{code}') <> 0
        group by code(data, '{code}')
        order by count(*) desc
    )
    where c_p > 1;
    """)
    return [a[0] for a in cur.fetchall()]

def check_split (code, year, name):
    cur.execute(f"""
    select
    count(*) filter (where code(data, '{code}') > 0) as plus,
    count(*) filter (where code(data, '{code}') < 0) as minus
    from {name}_{year}
    where code(data, '{code}') <> 0
    """)
    return cur.fetchall()[0]

def update_table (code, split, bad_values, year, name):
    sign = f"sign(code(data, '{code}'))"
    if split == "plus":
        p = ">"
        p2 = "p"
    elif split == "minus":
        p = "<"
        p2 = "m"
    elif split == "only_plus":
        p = "<>"
        p2 = "p"
        sign = "1.0"
    elif split == "only_minus":
        p = "<>"
        p2 = "m"
        sign = "-1.0"
    elif split == "plus_minus":
        p = "<>"
        p2 = ""
        sign = f"sign(code(data, '{code}'))"
    elif split == "abs":
        p = "<>"
        p2 = ""
        sign = "1.0"
    else:
        print("bad split factor")
        sys.exit()

    cur.execute(f"""
    with tab as (
        select
            log(abs(code(data, '{code}'))) * {sign} as p1,
            inn
        from {name}_{year} f
        where code(data, '{code}') {p} 0 and {gen_exceptions(code, bad_values)}
    )
    update {name}_{year}_fix as fs
    set data = jsonb_set(
        coalesce(fs.data, '{{}}'::jsonb),
        '{{{str(code) + p2}}}',
        to_jsonb((p1)::float8),
        true
    )
    from tab as t
    where t.inn = fs.inn;
    """)
    connection.commit()

def gen_fix_table_split (year : int, codes : list, fix_dict : dict[int, str], name):
    print(f" Gen fix table y{year} ".center(60, '='))
    for i, code in enumerate(codes):
        bad_values = get_bad_values(code, year, name)
        bad_values = list(set(bad_values + [0]))

        if fix_dict[code] == "p":
            update_table(code, "only_plus", bad_values, year, name)
        elif fix_dict[code] == "m":
            update_table(code, "only_minus", bad_values, year, name)
        elif fix_dict[code] == "pm":
            plus_count, minus_count = check_split(code, year, name)
            if plus_count > 1000:
                update_table(code, "plus", bad_values, year, name)
            if minus_count > 1000:
                update_table(code, "minus", bad_values, year, name)
        else:
            print("BAD dictionary")

        print(f"\r{i} / {len(codes)}", end="")
    print("")

def gen_fix_table (year : int, codes : list, fix_dict : dict[int, str], name):
    print(f" Gen fix table y{year} ".center(60, '='))
    for i, code in enumerate(codes):
        bad_values = get_bad_values(code, year, name)
        bad_values = list(set(bad_values + [0]))

        if fix_dict[code] == "p" or fix_dict[code] == "m":
            update_table(code, "abs", bad_values, year, name)
        elif fix_dict[code] == "pm":
            update_table(code, "plus_minus", bad_values, year, name)
        else:
            print("BAD dictionary")

        print(f"\r{i} / {len(codes)}", end="")
    print("")
    # cur.close()
    # connection.close()