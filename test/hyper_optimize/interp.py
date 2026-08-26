import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

df_stats = pd.read_csv('/Users/lyt/Desktop/phreefit/po4/de_statistical_summary.csv')

# 筛选最佳策略（按 fun_mean 排序）
best_strategy = df_stats.sort_values('fun_mean').iloc[0]
print("最佳参数组合：")
print(best_strategy[['strategy', 'init', 'recombination', 'fun_mean', 'fun_std']])

# 可视化对比
import matplotlib.pyplot as plt

plt.errorbar(
    df_stats.index,
    df_stats['fun_mean'],
    yerr=df_stats['fun_std'],
    fmt='o'
)
plt.xlabel('Parameter Combination Index')
plt.ylabel('Objective Function Value (Mean ± SD)')
plt.title('Performance Across Parameter Combinations')
plt.show()

from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting



df = pd.read_csv('/Users/lyt/Desktop/phreefit/po4/de_raw_results_50_runs.csv')

# 过滤失败的任务（fun值为无穷大或nfev为-1）
df_valid = df[(df['fun'] < np.inf) & (df['nfev'] > 0)]

# 按参数组合分组，计算均值
grouped = df_valid.groupby(['strategy', 'init', 'recombination'])
df_mean = grouped.agg({
    'fun': ['mean', 'std'],
    'nfev': ['mean', 'std'],
    'time': ['mean', 'std']
}).reset_index()

# 重命名列
df_mean.columns = [
    'strategy', 'init', 'recombination',
    'fun_mean', 'fun_std',
    'nfev_mean', 'nfev_std',
    'time_mean', 'time_std'
]

# 定义优化目标：最小化 fun_mean 和 nfev_mean
F = df_mean[['fun_mean', 'time_mean']].values

nds = NonDominatedSorting(method="fast_non_dominated_sort")
fronts = nds.do(F, return_rank=False)

# 获取第一层帕累托前沿（最优解）
pareto_front = df_mean.iloc[fronts[0]]

# 标记原始数据中的帕累托最优组合
df_mean['is_pareto'] = False
df_mean.loc[fronts[0], 'is_pareto'] = True


plt.figure(figsize=(10, 6))

# 绘制所有参数组合
plt.scatter(
    df_mean['time_mean'],
    df_mean['fun_mean'],
    c='gray',
    alpha=0.5,
    label='Non-Pareto'
)

# 高亮帕累托前沿
plt.scatter(
    pareto_front['time_mean'],
    pareto_front['fun_mean'],
    c='red',
    edgecolors='black',
    label='Pareto Front'
)

# 标注参数组合
for idx, row in pareto_front.iterrows():
    label = f"{row['strategy']}-{row['init']}-CR{row['recombination']}"
    plt.annotate(
        label,
        (row['time_mean'], row['fun_mean']),
        textcoords="offset points",
        xytext=(5, 5),
        ha='left',
        fontsize=8
    )

plt.xlabel('Number of Function Evaluations (time_mean)')
plt.ylabel('Objective Function Value (fun_mean)')
plt.title('Pareto Front: fun_mean vs. time_mean')
plt.legend()
plt.grid(True)
plt.show()


# 按 fun_mean 排序
best_by_fun = pareto_front.sort_values('fun_mean').head(3)
print("帕累托解中精度最高的3个组合：")
print(best_by_fun[['strategy', 'init', 'recombination', 'fun_mean', 'time_mean']])

# 按 nfev_mean 排序
best_by_nfev = pareto_front.sort_values('time_mean').head(3)
print("\n帕累托解中计算效率最高的3个组合：")
print(best_by_nfev[['strategy', 'init', 'recombination', 'fun_mean', 'time_mean']])

pareto_front_sorted = pareto_front.sort_values('fun_mean')
pareto_front_sorted['robustness_score'] = pareto_front_sorted['fun_std'] / pareto_front_sorted['fun_mean']

print("\n帕累托解的鲁棒性排名（标准差/均值比越小越稳定）：")
print(pareto_front_sorted[['strategy', 'init', 'recombination', 'robustness_score', 'fun_mean']])


from matplotlib.backends.backend_pdf import PdfPages

with PdfPages('/Users/lyt/Desktop/phreefit/po4/pareto_analysis_report_ccm.pdf') as pdf:
    # 二维帕累托图
    plt.figure(figsize=(10, 6))
    plt.scatter(
        df_mean['time_mean'],
        df_mean['fun_mean'],
        c='gray',
        alpha=0.5,
        label='Non-Pareto'
    )

    # 高亮帕累托前沿
    plt.scatter(
        pareto_front['time_mean'],
        pareto_front['fun_mean'],
        c='red',
        edgecolors='black',
        label='Pareto Front'
    )

    # 标注参数组合
    for idx, row in pareto_front.iterrows():
        label = f"{row['strategy']}-{row['init']}-CR{row['recombination']}"
        plt.annotate(
            label,
            (row['time_mean'], row['fun_mean']),
            textcoords="offset points",
            xytext=(5, 5),
            ha='left',
            fontsize=8
        )

    plt.xlabel('Number of Function Evaluations (time_mean)')
    plt.ylabel('Objective Function Value (fun_mean)')
    plt.title('Pareto Front: fun_mean vs. nfev_mean')
    plt.legend()
    plt.grid(True)
    # plt.show()
    pdf.savefig()
    plt.close()

    # 鲁棒性表格
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis('off')
    table = ax.table(
        cellText=pareto_front_sorted.values,
        colLabels=pareto_front_sorted.columns,
        cellLoc='center',
        loc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)
    pdf.savefig()
    plt.close()