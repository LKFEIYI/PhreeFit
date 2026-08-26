
import numpy as np
from scipy.optimize import differential_evolution as de_opt
from src import main_cal
import phreeqpy.iphreeqc.phreeqc_dll as phc_mod
import time
import pandas as pd

from scipy import optimize
database_path="/Users/lyt/PycharmProjects/PhreeFit/test/cdm/simple_davies_for_titration.dat"
with open(database_path,"r",encoding="UTF-8") as file:
    database=file.read()


# data=pd.read_csv("/Users/lyt/Desktop/phreefit/gyy/small_hh.csv")
data=np.loadtxt("/Users/lyt/Desktop/phreefit/gyy/small_hh.csv",delimiter=",",skiprows=1)

simple_species1=main_cal.SurfaceSpecies2()
simple_species2=main_cal.SurfaceSpecies2()
simple_species3=main_cal.SurfaceSpecies2()

simple_species1.add_surface("Surf_a","Surf_aH1.333",(0,0.01),48.56,0.08,1,1,0.001,1,1)
simple_species1.add_reactions("Surf_aH-0.333 + H+ + NO3- = Surf_aH2NO3-0.333",(-15,15),-1,True,0,-5,-1)
simple_species1.add_reactions("Surf_aH-0.333 + Na+ = Surf_aHNa+0.667",(-5,5),1,True,1,-5,-1)
simple_species1.add_reactions("Surf_aH-0.333 + H+ = Surf_aH2+0.667",(-14,14),0,True,1,-5,-1)
simple_species1.add_reactions("Surf_aH1.333 = Surf_aH-0.333 + 0.333H+",25,0,True,-0.333,-5,-1)


simple_species2.add_surface("Surf_b","Surf_bH1.667",(0,0.01),48.56,0.08,(0,5),(0,5),0.001,1,1)
simple_species2.add_reactions("Surf_bH-0.667 + H+ + NO3- = Surf_bH2NO3-0.667",(-15,15),-1,True,0,-5,-1)
simple_species2.add_reactions("Surf_bH-0.667 + Na+ = Surf_bHNa+0.333",(-5,5),1,True,1,-5,-1)
simple_species2.add_reactions("Surf_bH-0.667 + H+ = Surf_bH2+0.333",(-14,14),0,True,1,-5,-1)
simple_species2.add_reactions("Surf_bH1.667 = Surf_bH-0.667 + 0.667H+",25,0,True,-0.667,-5,-1)

simple_species3.add_surface("Inter_a","Inter_aH1.667",(0,0.01),48.56,0.08,(0,5),(0,5),0.001,1,1)
simple_species3.add_reactions("Inter_aH-0.667 + H+ + NO3- = Inter_aH2NO3-0.667",(-15,15),-1,True,0,-5,-1)
simple_species3.add_reactions("Inter_aH-0.667 + Na+ = Inter_aHNa+0.333",(-5,5),1,True,1,-5,-1)
simple_species3.add_reactions("Inter_aH-0.667 + H+ = Inter_aH2+0.333",(-14,14),0,True,1,-5,-1)
simple_species3.add_reactions("Inter_aH1.667 = Inter_aH-0.667 + 0.667H+",25,0,True,-0.667,-5,-1)

titration=main_cal.Adsorption("CDMUSIC")
titration.species_definition(database,"")
titration.initial_solution([0.01],initial_pH=7,cation="Na",anion="N(5)",metal={})

titration.add_surface(simple_species1)
titration.add_surface(simple_species2)
titration.add_surface(simple_species3)


titration.selected_output({})
titration.set_type_acid(type_base="NaOH",type_acid="HNO3")

titration.mix_solution(type_solution="dissolution",base_mass=0.1,acid_mass=0.1)
titration.mix_action(initial_volume=40,mix_volume=data[:,1])
# titration.eq_ph(ph_list=data[:,0],eq_phase="",ph_sep=None,auto_p=True)

titration.get_bounds()

def ph_sc(k1,k2,k3,k4,k5,s1,s2,c1,c2,s3,c3,c4):
    ph_script='''SOLUTION 1
             temp      25
             pH        7
             pe        4
             redox     pe
             units     mol/l
             density   1
             Na        0.01
             N(5)        0.01    charge
             -water    1 # kg
         
        SAVE solution 1
        END
            
        PHASES
            Fix_H+
                H + = H +
                log_k     0
        END
                
        SOLUTION 11
            temp      25
            pH        7
            pe        4
            redox     pe
            units     mol/kgw
            density   1
            -water    1 # kg
        END     
        USE solution 11
        REACTION 1
            HNO3
            0.1 moles in 1 steps
        SAVE solution 12
        END        
                 
        USE solution 11
        REACTION 1
            NaOH
            0.1 moles in 1 steps
        SAVE solution 13
        END        
                
        SURFACE_MASTER_SPECIES
            Surf_a	Surf_aH1.333
            Surf_b	Surf_bH1.667
            Inter_a	Inter_aH1.667
        SURFACE_SPECIES
            Surf_aH1.333 = Surf_aH1.333
                log_k 0
            -cd_music  0 0 0
            Surf_aH-0.333 + H+ + NO3- = Surf_aH2NO3-0.333
                log_k 	{0}
            -cd_music  1 -1 0
            Surf_aH-0.333 + Na+ = Surf_aHNa+0.667
                log_k 	{1}
            -cd_music  0 1 0
            Surf_aH-0.333 + H+ = Surf_aH2+0.667
                log_k 	{2}
            -cd_music  1 0 0
            Surf_aH1.333 = Surf_aH-0.333 + 0.333H+
                log_k 25
            -cd_music  -0.333 0 0
            Surf_bH1.667 = Surf_bH1.667
                log_k 0
            -cd_music  0 0 0
            Surf_bH-0.667 + H+ + NO3- = Surf_bH2NO3-0.667
                log_k 	{0}
            -cd_music  1 -1 0
            Surf_bH-0.667 + Na+ = Surf_bHNa+0.333
                log_k 	{1}
            -cd_music  0 1 0
            Surf_bH-0.667 + H+ = Surf_bH2+0.333
                log_k 	{3}
            -cd_music  1 0 0
            Surf_bH1.667 = Surf_bH-0.667 + 0.667H+
                log_k 25
            -cd_music  -0.667 0 0
            Inter_aH1.667 = Inter_aH1.667
                log_k 0
            -cd_music  0 0 0
            Inter_aH-0.667 + H+ + NO3- = Inter_aH2NO3-0.667
                log_k 	{0}
            -cd_music  1 -1 0
            Inter_aH-0.667 + Na+ = Inter_aHNa+0.333
                log_k 	{1}
            -cd_music  0 1 0
            Inter_aH-0.667 + H+ = Inter_aH2+0.333
                log_k 	{4}
            -cd_music  1 0 0
            Inter_aH1.667 = Inter_aH-0.667 + 0.667H+
                log_k 25
            -cd_music  -0.667 0 0
        END
        SURFACE 1
            Surf_aH1.333	{5}	48.56	0.08
                    -capacitances 1 1
            Surf_bH1.667	{6}	48.56	0.08
                    -capacitances {7} {8}
            Inter_aH1.667	{9}	48.56	0.08
                    -capacitances {10} {11}
        -cd_music
        END
        SELECTED_OUTPUT 1
            -reset                false
            -simulation           true
            -pH                   true
            -water                true           
        
            USE surface 1
            MIX 1
                1    0.04
                12    0.000497
                13    0.0
            END
            USE surface 1
            MIX 2
                1    0.04
                12    0.000497
                13    7.793999999999999e-05
            END
            USE surface 1
            MIX 3
                1    0.04
                12    0.000497
                13    0.00024317
            END
            USE surface 1
            MIX 4
                1    0.04
                12    0.000497
                13    0.00035807
            END
            USE surface 1
            MIX 5
                1    0.04
                12    0.000497
                13    0.00044233
            END
            USE surface 1
            MIX 6
                1    0.04
                12    0.000497
                13    0.00050661
            END
            USE surface 1
            MIX 7
                1    0.04
                12    0.000497
                13    0.0005579199999999999
            END
            USE surface 1
            MIX 8
                1    0.04
                12    0.000497
                13    0.0005996700000000001
            END
            USE surface 1
            MIX 9
                1    0.04
                12    0.000497
                13    0.00063554
            END
            USE surface 1
            MIX 10
                1    0.04
                12    0.000497
                13    0.00066654
            END
            USE surface 1
            MIX 11
                1    0.04
                12    0.000497
                13    0.00069432
            END
            USE surface 1
            MIX 12
                1    0.04
                12    0.000497
                13    0.00071958
            END
            USE surface 1
            MIX 13
                1    0.04
                12    0.000497
                13    0.00074305
            END
            USE surface 1
            MIX 14
                1    0.04
                12    0.000497
                13    0.0007653299999999999
            END
            USE surface 1
            MIX 15
                1    0.04
                12    0.000497
                13    0.00078662
            END
            USE surface 1
            MIX 16
                1    0.04
                12    0.000497
                13    0.0008067800000000001
            END
            USE surface 1
            MIX 17
                1    0.04
                12    0.000497
                13    0.00082566
            END
            USE surface 1
            MIX 18
                1    0.04
                12    0.000497
                13    0.0008442300000000001
            END
            USE surface 1
            MIX 19
                1    0.04
                12    0.000497
                13    0.00086171
            END
            USE surface 1
            MIX 20
                1    0.04
                12    0.000497
                13    0.0008792
            END
            USE surface 1
            MIX 21
                1    0.04
                12    0.000497
                13    0.0008989200000000001
            END
            USE surface 1
            MIX 22
                1    0.04
                12    0.000497
                13    0.00092212
            END
            USE surface 1
            MIX 23
                1    0.04
                12    0.000497
                13    0.00094613
            END
            USE surface 1
            MIX 24
                1    0.04
                12    0.000497
                13    0.00097485
            END
            USE surface 1
            MIX 25
                1    0.04
                12    0.000497
                13    0.00100405
            END
            USE surface 1
            MIX 26
                1    0.04
                12    0.000497
                13    0.0010357300000000001
            END
            USE surface 1
            MIX 27
                1    0.04
                12    0.000497
                13    0.0010711
            END
            USE surface 1
            MIX 28
                1    0.04
                12    0.000497
                13    0.00111407
            END
            USE surface 1
            MIX 29
                1    0.04
                12    0.000497
                13    0.00116132
            END
            USE surface 1
            MIX 30
                1    0.04
                12    0.000497
                13    0.0012188099999999999
            END
            USE surface 1
            MIX 31
                1    0.04
                12    0.000497
                13    0.00128783
            END'''.format(k1,k2,k3,k4,k5,s1,s2,c1,c2,s3,c3,c4)
    return ph_script
def get_pH(ppp):
    re_ph = []
    ph = ppp.get_selected_output_array()
    for i in range(1, len(ph)):
        re_ph.append(ph[i][1])
    return np.array(re_ph)

def traget_fun(p,exp_data):
    try:
        prc2 = phc_mod.IPhreeqc()
        prc2.load_database_string(database)
        prc2.run_string(ph_sc(*p))
        error = get_pH(prc2) - exp_data
        prc2.destroy_iphreeqc()
    # print(p)
        return np.linalg.norm(error)
    except:
        return 999

param = {
    'strategy': "best1exp",
    'init': "halton",
    'recombination': 0.9
}

# 运行DE算法
# start_time = time.time()
bounds=[(0,10),(-5,5),(-10,10),(-10,10),(-10,10),(0,0.01),(0,0.01),(0,3),(0,3),(0,0.01),(0,3),(0,3)]
# 运行DE算法
if __name__=='__main__':
    # test_res1=de_opt(traget_fun,bounds=bounds,args=([data[:,0]]),workers=6,**param)
    # test_res = optimize.minimize(traget_fun, bounds=bounds, args=(data[:,0]),x0=np.array([5,0,5,5,5,0.0001,0.0001,1,1,0.001,1,1]),method="Nelder-Mead",options={"adaptive":True,"maxiter":5000})
    st=[2.81952001e+00,
    4.44256742e+00,
    - 1.30072006e+00,
    3.32420739e+00,
    1.07497447e+01,
    9.93483579e-03,
    9.09017675e-03,
    2.19011109e+00,
    3.64112519e-06,
    1.77309499e-03,
    5.84655911e+00,
    7.53540867e+00]
    print(ph_sc(*st))
# result_pre = de_opt(main_cal.proto_fun, workers=6,bounds=bounds,args=(data[:, 0], titration, True),**param)
# result_polish=optimize.minimize(main_cal.proto_fun, x0=result_pre.x,bounds=np.array(titration.bounds),args=(data[:, 0], titration, True),method="Nelder-Mead",options={"adaptive":True})
# if result_polish.fun < result_pre.fun:
#     result=result_polish
# else:
#     result=result_pre
# elapsed_time = time.time() - start_time
#
# evaluations=main_cal.advanced_evaluation(exp_data=data[:,0],results=result,titration=titration,mix=True)
# print(result.x,result.fun)
#     from SALib.sample import saltelli
#     from SALib.analyze import sobol
#
#     # 定义问题
#     problem = {
#         'num_vars': len(bounds),
#         'names': ['k1', 'k2', 'k3','k4','k5','s1', 's2', 'c1', 'c2', 's', 'c3','c4'],
#         'bounds': bounds
#     }
#
#     # 生成样本并运行模型
#     param_values = saltelli.sample(problem, 1024)
#     Y = np.zeros([param_values.shape[0]])
#     for i, X in enumerate(param_values):
#         Y[i] = traget_fun(*X,data[:,0])  # 黑箱函数
#
#     # Sobol 分析
#     Si = sobol.analyze(problem, Y)
#     print("一阶敏感性指数:", Si['S1'])
#     print("全局敏感性指数:", Si['ST'])