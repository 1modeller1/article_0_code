import math
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
# from patsy.state import scale
from scipy.cluster.hierarchy import average
from scipy.stats import norm, skewnorm, johnsonsu
from scipy.optimize import minimize
import statsmodels.api as sm
import signal

# codes = pd.read_csv("counts.csv")
# codes = codes[codes["count"] > 10_000]

db_config = {}
with open("../db_config.txt", "r") as file:
    for line in file:
        line = line.strip()
        if not line: continue
        key, value= line.split('=', 1)
        db_config[key] = value

connection = psycopg2.connect(**db_config)
cur = connection.cursor()

code = 1150
data = "data_clean"
table = "fin_2020_clean"
# table = "fin_2020_no_blows_split_clean"

koefs = pd.read_csv("../koefs/fin_split_c1600p_MNK_factors_y2020.csv")
koefs = koefs.set_index("code")
koef_a_p, koef_a_m = 0, 0
# koef_a_p = koefs.loc[str(code) + 'p', "a"]
# koef_a_m = koefs.loc[str(code) + 'm', "a"]

# getter = f"""coalesce(
#     ({data} ->> '{str(code) + 'p'}')::float8 - {koef_a_p},
#     ({data} ->> '{str(code) + 'm'}')::float8 - {koef_a_m}
# )
# """

# koef_a = koefs.loc[code, "a"]
koef_a = 0
getter = f"({data} ->> '{code}')::float8 - {koef_a}"

cur.execute(f"""
with tab as (
    select
        {getter} as value
    from {table} fd
    where {getter} <> 0
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
# avg = [copysign(10**abs(i), i) for i in avg]
# ------------------------------

cur.execute(f"""
with tab as (
	select
	{getter} as p
	from {table} f
	where {getter} <> 0
	order by p
)
select
	p,
	p - lag(p) over (order by p) as dp
from tab
order by p;
""")

x, dx = [list(i) for i in zip(*cur.fetchall())]
x, dx = x[1:], dx[1:]
# x = [copysign(10**abs(i), i) for i in x if i]

dx = [math.log10(1 / a) if a != 0 else 0 for a in dx]
# nn = range(len(dx))

# ------------------------------


# ------------------------------

fig, ax = plt.subplots(nrows=2)
for i in range(2):
    ax[i].minorticks_on()
    ax[i].grid(which="minor", color="#404040", linewidth=0.5, alpha=0.4)
    ax[i].grid(which="major", color="#404040", linewidth=0.8)

    # ax[i].set_xscale('symlog', linthresh=1)
    # ax[i].xaxis.set_major_locator(SymmetricalLogLocator(base=1000, linthresh=1))
    # ax[i].xaxis.set_minor_locator(SymmetricalLogLocator(base=1000, linthresh=1, subs=[10, 100]))

# ax.set_yscale('symlog', linthresh=1)
# ax.yaxis.set_major_locator(SymmetricalLogLocator(base=1000, linthresh=1))
# ax.yaxis.set_minor_locator(SymmetricalLogLocator(base=1000, linthresh=1, subs=[10, 100]))

fig.set_size_inches(10, 8)
# ax.set_title(r"code: $\bf{%s}$      count: $\bf{%s}$" % (code, sum(count)))

# n0 = range(len(count))
# count.sort()
# n1 = range(len(dx))
# dx.sort()

ax[0].scatter(avg, count, s=3)
# ax[0].scatter(n0, count, s=3)
ax[0].set_xlabel(f"avg(c{code})")
ax[0].set_ylabel("count")

ax[1].scatter(x, dx, s=3)
# ax[1].scatter(n1, dx, s=3)
ax[1].set_xlabel(f"c{code}")
ax[1].set_ylabel("log(1/dx)")

# ax[0].set_xticks(np.linspace(0, len(count) - 1, 11))
# ax[0].set_xticklabels([str(i) + '%' for i in range(0, 101, 10)])
# ax[1].set_xticks(np.linspace(0, len(dx) - 1, 11))
# ax[1].set_xticklabels([str(i) + '%' for i in range(0, 101, 10)])



fig.suptitle(r"Распределение остатков по счету $\bf{c%s}$ (c%s - b * c1600)" % (code, code))
# fig.suptitle(r"Распределение остатков по счету $\bf{c%s}$ (c%s - b * c1600 - a)    $\bf{[split]}$" % (code, code))
plt.tight_layout()
# plt.savefig("two_graphs_log_1150.png", dpi=150)
plt.show()