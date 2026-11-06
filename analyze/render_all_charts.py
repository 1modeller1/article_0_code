import os
import re
import sys
from time import sleep
import psycopg2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, SymmetricalLogLocator
from math import e, exp, copysign
import numpy as np
from scipy.stats import norm
import statsmodels.api as sm

db_config = {}
with open("../db_config.txt", "r") as file:
    for line in file:
        line = line.strip()
        if not line: continue
        key, value= line.split('=', 1)
        db_config[key] = value

connection = psycopg2.connect(**db_config)
cur = connection.cursor()

def get_data_split (code, koef_a = None):
    cur.execute(f"""
    with tab as (
        select
            coalesce( {data} ->> '{str(code) + 'p'}', {data} ->> '{str(code) + 'm'}')::float8 as value
        from {table} fd
        where coalesce( {data} ->> '{str(code) + 'p'}', {data} ->> '{str(code) + 'm'}')::float8 <> 0
    )
    select
        floor( value * 200 ) as income_group,
        avg( value ) as income_avg,
        count(*) as count
    from tab 
    group by income_group
    order by income_group ;
    """)

    groups, avg, count = [list(a) for a in zip(*cur.fetchall())]

    avg = [copysign(10**abs(a), a) for a in avg]
    return groups, avg, count

def get_data (code, koef_a = None):
    if koef_a:
        minus_a = f" - {koef_a}"
    else:
        minus_a = ""

    cur.execute(f"""
    with tab as (
        select
            ({data} ->> '{code}')::float8 as value
        from {table} fd
        where ({data} ->> '{code}')::float8 <> 0
    )
    select
        floor( value * 200 ) as income_group,
        avg( value ) {minus_a} as income_avg,
        count(*) as count
    from tab 
    group by income_group
    order by income_group ;
    """)

    groups, avg, count = [list(a) for a in zip(*cur.fetchall())]
    avg = [copysign(10**abs(a), a) for a in avg]
    return groups, avg, count

def render_chart (code, name, koef_a):
    groups, avgs, counts = get_data(code, koef_a)

    fig, ax = plt.subplots()
    # ax.plot(list(df["income_avg"]), list(df["count"]), lw=2)
    # ax.bar(list(df["income_avg"]), list(df["count"]), color='lightblue', edgecolor='blue')
    # ax.hist(resid, bins=20, edgecolor='black', alpha=0.7)
    ax.scatter(avgs, counts, s=3)
    # ax.plot(model_x, y_predict, lw=2)
    # ax.plot(list(df["income_avg"]), norm, lw=2, ls='--')

    # -------------------------------------------------

    ax.set_title(r"year: $\bf{%s}$   code: $\bf{%s}$   count: %s" % (2020, code, f"{sum(counts):,}"))
    fig.suptitle(name)
    ax.set_ylabel("Число компаний")
    ax.set_xlabel(f"log(c{code} - k*c1600)")

    ax.minorticks_on()
    ax.grid(which="minor", color="#404040", linewidth=0.5, alpha=0.4)
    ax.grid(which="major", color="#404040", linewidth=0.8)

    ax.set_xscale('symlog', linthresh=1)
    ax.xaxis.set_major_locator(SymmetricalLogLocator(base=1000, linthresh=1))
    ax.xaxis.set_minor_locator(SymmetricalLogLocator(base=1000, linthresh=1, subs=[10,100]))

    fig.set_size_inches(10,8)

    # ax.legend([f"count: {count}"], loc="lower right")
    # plt.show()
    plt.savefig(f"{OUT_FOLDER}/y{2020}-c{code}.png", dpi=200)
    plt.close()


OUT_FOLDER = "plots_minus_a"

table = "fin_2020_clean"
data = "data_clean"

if __name__ == "__main__":
    codes = pd.read_csv("../counts.csv")
    codes = codes[codes["count"] > 10_000]
    codes = codes["code"].tolist()

    koefs = pd.read_csv("../koefs/fin_c1600_MNK_factors_y2020.csv")
    koefs = koefs.set_index("code")
    # print(koefs.loc[2300, "a"])

    names = pd.read_csv("../codes.csv")
    names = dict(zip(names["code"], names["name"]))

    if not os.path.isdir(OUT_FOLDER):
        os.mkdir(OUT_FOLDER)

    for i, code in enumerate(codes):
        if code == 1600:
            continue
        koef_a = koefs.loc[code, "a"]
        name = names[int(code)]
        render_chart(code, name, koef_a)
        print(f"\r{i} / {len(codes)}", end="")