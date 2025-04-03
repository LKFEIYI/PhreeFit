import numpy as np
from scipy.optimize import differential_evolution as de_opt
from src import main_cal
from sklearn.model_selection import ParameterGrid
import time
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
database_path="simple_davies_for_titration.dat"
with open(database_path,"r",encoding="UTF-8") as file:
    database=file.read()


data=np.loadtxt("actec.csv",delimiter=",",skiprows=1)

simple_species=main_cal.SurfaceSpecies2()
simple_species.add_surface("Surf","SurfOH",(0,0.01),1,1,1,1,0.001,1,1)
simple_species.add_reactions("SurfOH = SurfO- + H+",(-11,-2),1,True,1,-5,-1)
titration=main_cal.Adsorption("NEM")
titration.species_definition(database,"")
titration.initial_solution([0.1],initial_pH=3.065,cation="Na",anion="Cl",metal={})
titration.add_surface(simple_species)
titration.selected_output({})
titration.set_type_acid(type_base="NaOH",type_acid="HNO3")
titration.mix_solution(type_solution="dissolution",base_mass=0.993)
titration.mix_action(initial_volume=10.5768,mix_volume=data[:,1])
titration.get_bounds()

stras = ['best1bin', 'best1exp', 'rand1bin', 'rand1exp', 'rand2bin', 'rand2exp', 'randtobest1bin', 'randtobest1exp',
         'currenttobest1bin', 'currenttobest1exp', 'best2exp', 'best2bin']
inits = ['latinhypercube', 'sobol', 'halton', 'random']
recoms = [0.7, 0.8, 0.9]
param_grid = {
    'strategy': stras,
    'init': inits,
    'recombination': recoms
}


def run_de_experiment(params):
    try:
        start_time = time.time()
        result =de_opt(main_cal.proto_fun,bounds=np.array(titration.bounds),args=(data[:,0],titration,True),**params)
        elapsed_time = time.time() - start_time

        return {
            'strategy': params['strategy'],
            'init': params['init'],
            'recombination': params['recombination'],
            'nfev': result.nfev,
            'nit': result.nit,
            'fun': result.fun,
            'time': elapsed_time,
            'error': None
        }
    except Exception as e:
        return {
            'strategy': params['strategy'],
            'init': params['init'],
            'recombination': params['recombination'],
            'nfev': -1,
            'nit': -1,
            'fun': np.inf,
            'time': -1,
            'error': str(e)
        }
# opt_res=main_cal.optimize_problem(0,"Differential evolution",np.array(titration.initial_guess),np.array(titration.bounds),extra_para=(data[:,0],titration,True))
if __name__ == '__main__':  # 必须添加，确保Windows/macOS多进程安全
    num_workers = 8  # 根据CPU核心数调整（建议等于物理核心数）
    results = []
    from tqdm import tqdm
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # 提交所有任务
        futures = [executor.submit(run_de_experiment, param) for param in all_params]

        # 使用tqdm显示进度
        for future in tqdm(as_completed(futures), total=len(all_params), desc="Grid Search Progress"):
            results.append(future.result())

    # 保存结果
    df_results = pd.DataFrame(results)
    df_results.to_csv('de_grid_search_multiprocess_results.csv', index=False)
    print("Results saved to de_grid_search_multiprocess_results.csv")
