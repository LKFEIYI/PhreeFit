import numpy as np
from scipy.optimize import differential_evolution as de_opt
from src import main_cal
from sklearn.model_selection import ParameterGrid
import time
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from scipy import optimize
database_path="simple_cr_davies.dat"
with open(database_path,"r",encoding="UTF-8") as file:
    database=file.read()


data=np.loadtxt("geo.csv",delimiter=",",skiprows=1)

simple_species1=main_cal.SurfaceSpecies2()

simple_species1.add_surface("Surf","SurfOH",3.587e-4,60,1.8,1,1,0.001,1,1)
simple_species1.add_reactions("SurfOH  + H+ = SurfOH2+",6.93,1,True,1,-5,-1)
simple_species1.add_reactions("SurfOH  = SurfO- + H+",-9.65,1,True,1,-5,-1)
simple_species1.add_reactions("SurfOH + CrO4-2 + H+ = SurfCrO4- + H2O",(0,30),1,True,1,-5,-1)
simple_species1.add_reactions("SurfOH + CrO4-2 + 2H+ = SurfHCrO4 + H2O",(0,30),1,True,1,-5,-1)
simple_species1.add_reactions("SurfOH + CrO4-2 = SurfOHCrO4-2 ",(0,30),1,True,1,-5,-1)


titration=main_cal.Adsorption("GDDL")
titration.species_definition(database,"")
titration.initial_solution([0.1],initial_pH=7,cation="Na",anion="Cl",metal={"H2CrO4":2e-4})

titration.add_surface(simple_species1)


titration.selected_output({"totals":"Cr"})
titration.set_type_acid(type_base="NaOH",type_acid="HCl")
# titration.eq_ph(ph_list=data[:,0],eq_phase="",ph_sep=None,auto_p=True)

titration.get_bounds()

stras = ['best1bin', 'best1exp', 'rand1bin', 'rand1exp', 'rand2bin', 'rand2exp', 'randtobest1bin', 'randtobest1exp',
         'currenttobest1bin', 'currenttobest1exp', 'best2exp', 'best2bin']
inits = ['latinhypercube', 'sobol', 'halton', 'random']
recoms = [0.7, 0.8, 0.9]
param_grid = {
    'strategy': stras,
    'init': inits,
    'recombination': recoms,
    'run_id': list(range(1))
}

all_params = list(ParameterGrid(param_grid))

# result = de_opt(main_cal.advanced_fun_auto, bounds=np.array(titration.bounds), args=(data[:, 1], data[:,0],"",titration))

# def run_single_experiment(param):
#     try:
#         # 为每次运行生成唯一随机种子
#         # np.random.seed((param['run_id'] + 1) * 42)  # 种子 = (run_id+1)*固定基数
#
#
#         # 运行DE算法
#         start_time = time.time()
#
#         # 运行DE算法
#         result_pre = de_opt(main_cal.advanced_fun_auto, bounds=np.array(titration.bounds), args=(data[:, 1], data[:,0],"",titration),
#                             strategy=param['strategy'],
#                             init=param['init'],
#                             recombination=param['recombination'],polish=False)
#         result_polish=optimize.minimize(main_cal.advanced_fun_auto, bounds=np.array(titration.bounds), x0=result_pre.x,args=(data[:, 1], data[:,0],"",titration),method="Nelder-Mead",options={"adaptive":True})
#         if result_polish.fun < result_pre.fun:
#             result=result_polish
#         else:
#             result=result_pre
#         elapsed_time = time.time() - start_time
#         print(str(param["run_id"])+":"+"success")
#         return {
#             'strategy': param['strategy'],
#             'init': param['init'],
#             'recombination': param['recombination'],
#             'run_id': param['run_id'],
#             'nfev': result.nfev,
#             'nit': result.nit,
#             'fun': result.fun,
#             'time': elapsed_time,
#             'error': None
#         }
#     except Exception as e:
#         print(str(param["run_id"]) + ":" + "fail")
#         return {
#             'strategy': param['strategy'],
#             'init': param['init'],
#             'recombination': param['recombination'],
#             'run_id': param['run_id'],
#             'nfev': -1,
#             'nit': -1,
#             'fun': np.inf,
#             'time': -1,
#             'error': str(e)
#         }
#
#
# # 多进程执行（主程序）
# if __name__ == '__main__':
#     num_workers = 2  # 根据CPU核心数调整
#     results = []
#
#     with ProcessPoolExecutor(max_workers=num_workers) as executor:
#         # 提交所有任务
#         futures = [executor.submit(run_single_experiment, param) for param in all_params]
#
#         # 使用tqdm显示进度
#         for future in tqdm(as_completed(futures), total=len(all_params), desc="Grid Search"):
#             results.append(future.result())
#
#     # 保存原始数据（包含所有50次运行）
#     df_raw = pd.DataFrame(results)
#     df_raw.to_csv('de_raw_results_50_runs.csv', index=False)
#
#     # 计算统计摘要（按参数组合分组）
#     df_stats = df_raw.groupby(['strategy', 'init', 'recombination']).agg({
#         'fun': ['mean', 'std', 'min', 'max'],
#         'nfev': ['mean', 'std'],
#         'time': ['mean', 'std']
#     }).reset_index()
#
#     # 重命名列名
#     df_stats.columns = [
#         'strategy', 'init', 'recombination',
#         'fun_mean', 'fun_std', 'fun_min', 'fun_max',
#         'nfev_mean', 'nfev_std',
#         'time_mean', 'time_std'
#     ]
#
#     df_stats.to_csv('de_statistical_summary.csv', index=False)
#     print("原始数据已保存至 de_raw_results_50_runs.csv")
#     print("统计摘要已保存至 de_statistical_summary.csv")