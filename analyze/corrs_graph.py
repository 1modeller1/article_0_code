import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def get_x_y (df):
    df = df.drop(columns=["code", "Unnamed: 0"])
    y = [a for key in df for a in df[key] if pd.notna(a)]
    y = [abs(a) for a in y]
    y.sort()
    x = np.linspace(0,100,len(y))
    return x, y

fig, ax = plt.subplots()
ax.minorticks_on()
ax.grid(which="minor", color="#404040", linewidth=0.5, alpha=0.4)
ax.grid(which="major", color="#404040", linewidth=0.8)

# ax.set_xscale('symlog', linthresh=1)
# ax.set_yscale('symlog', linthresh=1)

# ax.xaxis.set_major_locator(SymmetricalLogLocator(base=1000, linthresh=1))
# ax.xaxis.set_minor_locator(SymmetricalLogLocator(base=1000, linthresh=1, subs=[10, 100]))

# ax.yaxis.set_major_locator(SymmetricalLogLocator(base=1000, linthresh=1))
# ax.yaxis.set_minor_locator(SymmetricalLogLocator(base=1000, linthresh=1, subs=[10, 100]))
fig.set_size_inches(10, 8)
ax.set_xlabel("Сортировка по возрастанию")
ax.set_ylabel("Величина |корреляции|")

def graph_0 ():
    df0 = pd.read_csv("../corrs/corrs_y2020_first.csv")
    x0, y0 = get_x_y(df0)
    df1 = pd.read_csv("../corrs/corrs_y2020_clean.csv")
    x1, y1 = get_x_y(df1)
    df2 = pd.read_csv("../corrs/fin_2_corrs_y2020_clean.csv")
    x2, y2 = get_x_y(df2)
    df3 = pd.read_csv("../corrs/corrs_no_blows_clean.csv")
    x3, y3 = get_x_y(df3)

    ax.scatter(x0, y0, s=2)
    ax.scatter(x1, y1, s=2)
    ax.scatter(x2, y2, s=2)
    ax.scatter(x3, y3, s=2)

    ax.legend([
        "no blows, clean, split",
        "no blows, clean, split, fixed +-",
        "no blows, clean, fixed +-",
        "no blows, clean"
               ], markerscale=4)

def graph_1 ():
    df0 = pd.read_csv("../corrs/corrs_y2020_clean.csv")
    x0, y0 = get_x_y(df0)
    ax.scatter(x0, y0, s=2, zorder=20, color = "black")

    okveds = ["01", "02", "03", "05", "06", "07", "08"]
    for okved in okveds:
        df1 = pd.read_csv(f"../corrs/fin_{okved}_corrs_y2020_clean.csv")
        x1, y1 = get_x_y(df1)
        ax.scatter(x1, y1, s=2)


    ax.legend([
        "all okved2",
        *[f"okved2 = {a}" for a in okveds]
    ],
        markerscale=4)

def graph_2 ():
    df0 = pd.read_csv("../corrs/fin_corrs_y2020_fix.csv")
    df1 = pd.read_csv("../corrs/fin_corrs_y2020_clean.csv")
    df2 = pd.read_csv("../corrs/fin_p2019_corrs_y2020_clean.csv")

    l = [df0, df1, df2]
    for i in l:
        x, y = get_x_y(i)
        ax.scatter(x, y, s=2)

    ax.legend([
        "Корреляции при log(значение)",
        "При log(значение) - b * log(активы)",
        "При log(значение) - b * log(активы прошлого года)"
    ], markerscale=4)

graph_2()

plt.xticks(np.arange(0, 101, 10), [str(i) + '%' for i in range(0, 101, 10)])

# plt.savefig("Сравнение корреляций в разных секторах.png", dpi=150)
plt.show()