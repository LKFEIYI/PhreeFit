# usr/bin/python3
import numpy as np
import phreeqpy.iphreeqc.phreeqc_dll as phc_mod
import time
import pandas as pd
from scipy import optimize as opt
# from sko.SA import SA
# from sko.GA import GA
#import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import axes3d
# from matplotlib import cm

database_path="/home/l4d2/iphreeqc-3.7.3-15968/database/simple.dat"
with open(database_path,"r",encoding="UTF-8") as file:
    database=file.read()
ip_path="/usr/local/lib/libiphreeqc-3.7.3.so"
def make_initial_con(Na_con):
    initial_condition = '''
    SOLUTION 1
    temp      25
    pH        7
    pe        4
    redox     pe
    units     mol/l
    density   1
    Cl        {0}
    Na        {0}
    -water    1 # kg

    END
    '''.format(Na_con)

    return initial_condition


def make_mix_acid(ph: float):
    acid_solution = '''
    SOLUTION 2
    temp      25
    pH        7
    pe        4
    redox     pe
    units     mol/kgw
    density   1
    -water    1 # kg

    REACTION 1
        NaOH
        {0} moles in 1 steps

    SAVE solution 3
    END

    '''.format(ph)
    return acid_solution


def select_output():
    so = '''
    SELECTED_OUTPUT 1
    -reset                false
    -simulation           true
    -pH                   true
    -water                true
    '''
    return so


def surface_sp(k1,k2,k3,k4):
    surface_master_species = '''
    SURFACE_MASTER_SPECIES 
        Surfa    SurfaOH
        Surfb    SurfbOH
        Surfc    SurfcOH
        Surfd    SurfdOH
    SURFACE_SPECIES 
        SurfaOH = SurfaOH 
                log_k   0 
        SurfbOH = SurfbOH 
                log_k   0 
        SurfcOH = SurfcOH 
                log_k   0 
        SurfdOH = SurfdOH 
                log_k   0         
        SurfaOH = SurfaO- + H+
                log_k   {0}
        SurfbOH = SurfbO- + H+
                log_k   {1}
        SurfcOH = SurfcO- + H+
                log_k   {2}
        SurfdOH = SurfdO- + H+
                log_k   {3}
    End
    '''.format(k1,k2,k3,k4)
    return surface_master_species


def surface_param(s1,s2,s3,s4):
    surface = '''
    SURFACE 1
        SurfaOH     {0}
        SurfbOH     {1}
        SurfcOH     {2}
        SurfdOH     {3}
        -no_edl
    END
    '''.format(s1,s2,s3,s4)
    return surface


def mix_action(initial_volumn, mix_volumn):
    first_mix = '''
    USE surface 1
    MIX 1
        1    {0}
        3    0
    END
    '''.format(initial_volumn)
    n=1
    for i in mix_volumn[1:]:
        n += 1
        first_mix += '''
        USE surface 1
        MIX {0}
            1    {1}
            3    {2}
        END

        '''.format(n, initial_volumn, i/1000)
    return first_mix


def get_pH(ppp):
    re_ph = []
    ph = ppp.get_selected_output_array()
    for i in range(1, len(ph)):
        re_ph.append(ph[i][1])
    return np.array(re_ph)



def traget_fun(exp_data,mixvv):
    def vi(p):
        prc2 = phc_mod.IPhreeqc(ip_path)
        prc2.load_database_string(database)
        prc2.run_string(make_initial_con(0.1))
        prc2.run_string(make_mix_acid(0.993))
        prc2.run_string(surface_sp(p[0],p[1],p[2],p[3]))
        prc2.run_string(surface_param(p[4],p[5],p[6],p[7]))
        prc2.run_string(select_output())
        prc2.run_string(mix_action(0.006509, mixvv))
        error = get_pH(prc2) - exp_data
        prc2.destroy_iphreeqc()
        return np.linalg.norm(error)

    return vi


def test_data(k1,k2,k3,k4, s1,s2,s3,s4,mixvv):
    prc = phc_mod.IPhreeqc(ip_path)
    prc.load_database_string(database)
    prc.run_string(make_initial_con(0.1))
    prc.run_string(make_mix_acid(0.993))
    prc.run_string(surface_sp(k1,k2,k3,k4))
    prc.run_string(surface_param(s1,s2,s3,s4))
    prc.run_string(select_output())
    prc.run_string(mix_action(0.006509, mixvv))
    ph_var = get_pH(prc)
    prc.destroy_iphreeqc()
    return ph_var

def lsq_fun(p,exp_data,mixvv):
    p = p.valuesdict()
    prc2 = phc_mod.IPhreeqc(ip_path)
    prc2.load_database_string(database)
    prc2.run_string(make_initial_con(0.1))
    prc2.run_string(make_mix_acid(0.993))
    prc2.run_string(surface_sp(p["k1"],p["k2"],p["k3"],p["k4"]))
    prc2.run_string(surface_param(p["site1"],p["site2"],p["site3"],p["site4"]))
    prc2.run_string(select_output())
    prc2.run_string(mix_action(0.006509, mixvv))
    error = get_pH(prc2) - exp_data
    prc2.destroy_iphreeqc()
    return np.linalg.norm(error)
def traget_fun_ccm(exp_data,mixvv):
    def vi(p):
        # p = p.valuesdict()
        prc2 = phc_mod.IPhreeqc(ip_path)
        prc2.load_database_string(database)
        prc2.run_string(make_initial_con(0.1))
        prc2.run_string(make_mix_acid(0.993))
        prc2.run_string(surface_sp_3site2(p[0],p[1],p[2]))
        prc2.run_string(surface_param_ccm2(p[3],p[4],p[5],p[6]))
        prc2.run_string(select_output())
        prc2.run_string(mix_action(0.006509, mixvv))
        error = get_pH(prc2) - exp_data
        prc2.destroy_iphreeqc()
        return np.linalg.norm(error)
    return vi
def lsq_fun_ccm(p,exp_data,mixvv):
    p=p.valuesdict()
    # print(p)
    prc2 = phc_mod.IPhreeqc(ip_path)
    prc2.load_database_string(database)
    prc2.run_string(make_initial_con(0.1))
    prc2.run_string(make_mix_acid(0.993))
    prc2.run_string(surface_sp_3site2(p["k1"],p["k2"],p["k3"]))
    prc2.run_string(surface_param_ccm2(p["site1"],p["site2"],p["site3"],p["ccm"]))
    prc2.run_string(select_output())
    prc2.run_string(mix_action(0.006509, mixvv))
    error = get_pH(prc2) - exp_data
    prc2.destroy_iphreeqc()
    return np.linalg.norm(error)


def test_data_ccm(k1,k2,k3, s1,s2,s3,s4,mixvv):
    start_t1 = time.perf_counter()
    prc = phc_mod.IPhreeqc()
    prc.load_database_string(database)
    prc.run_string(make_initial_con(0.1))
    prc.run_string(make_mix_acid(0.993))

    prc.run_string(surface_sp_3site(k1,k2,k3))
    prc.run_string(surface_param_ccm(s1,s2,s3,s4))

    prc.run_string(select_output())
    start_t = time.perf_counter()
    prc.run_string(mix_action(0.006509, mixvv))
    end_t = time.perf_counter()
    print("ccm mix耗时: {:.6f}秒".format(end_t - start_t))
    ph_var = get_pH(prc)
    prc.destroy_iphreeqc()
    end_t1 = time.perf_counter()
    print("ccm 总耗时: {:.6f}秒".format(end_t1 - start_t1))
    return ph_var

def test_data_ddl(k1,k2,k3, s1,s2,s3,mixvv):
    start_t1 = time.perf_counter()
    prc = phc_mod.IPhreeqc()
    prc.load_database_string(database)
    prc.run_string(make_initial_con(0.1))
    prc.run_string(make_mix_acid(0.993))

    prc.run_string(surface_sp_3site(k1,k2,k3))
    prc.run_string(surface_param_ddl(s1,s2,s3))

    prc.run_string(select_output())
    start_t = time.perf_counter()
    prc.run_string(mix_action(0.006509, mixvv))
    end_t = time.perf_counter()
    print("dll mix耗时: {:.6f}秒".format(end_t - start_t))
    ph_var = get_pH(prc)
    prc.destroy_iphreeqc()
    end_t1 = time.perf_counter()
    print("dll 总耗时: {:.6f}秒".format(end_t1 - start_t1))
    return ph_var

def surface_sp_3site2(k1,k2,k3):
    surface_master_species = '''
    SURFACE_MASTER_SPECIES 
        Surf_a    Surf_aOH
        Surf_b    Surf_bOH
        Surf_c    Surf_cOH
    SURFACE_SPECIES 
        Surf_aOH = Surf_aOH 
                log_k   0 
        Surf_bOH = Surf_bOH 
                log_k   0 
        Surf_cOH = Surf_cOH 
                log_k   0         
        Surf_aOH = Surf_aO- + H+
                log_k   {0}
        Surf_bOH = Surf_bO- + H+
                log_k   {1}
        Surf_cOH = Surf_cO- + H+
                log_k   {2}
    End
    '''.format(k1,k2,k3)
    return surface_master_species
def surface_param_ccm2(s1,s2,s3,s4):
    surface = '''
    SURFACE 1
        Surf_aOH     {0}  140 0.9705
        Surf_bOH     {1}
        Surf_cOH     {2}
        -ccm        {3}
    END
    '''.format(s1,s2,s3,s4)
    return surface
if __name__=="__main__":

    data=pd.read_csv("工作簿1.csv")
    ph_res=data['x'].values
    mix_data=data['y'].values
    # re=pd.DataFrame(columns=["k1","k2","k3","k4","s1","s2","s3","s4","time","R^2"])

    from sko.SA import SAFast
    from sko.SA import SACauchy
    from sko.SA import SABoltzmann
    from sko.GA import GA
    from sko.PSO import PSO
    from sko.DE import DE
    import lmfit
    res_df=pd.DataFrame(columns=["repeat","method","site1","k1","site2","k2","site3","k3","ccm","time","residual","nfev"])
    methods = ["basinhopping", "differential_evolution", "shgo", "dual_annealing"]
    para = lmfit.Parameters()
    para.add("k1", value=0, min=-10, max=0)
    para.add("site1", value=0.001, min=0, max=0.01)
    para.add("k2", value=0, min=-10, max=0)
    para.add("site2", value=0.001, min=0, max=0.01)
    para.add("k3", value=0, min=-10, max=0)
    para.add("site3", value=0.001, min=0, max=0.01)
    # para.add("k4", value=0, min=-10, max=0)
    # para.add("site4", value=0.001, min=0, max=0.01)
    para.add("ccm", value=1, min=0, max=3)
    x0 = [0,0,0 ,0.001, 0.001, 0.001,1]
    lb = [-10,-10,-10, 0.00001, 0.00001, 0.00001, 0]
    ub = [0,0,0, 0.01, 0.01, 0.01,3]
    minner = lmfit.Minimizer(lsq_fun_ccm, para, fcn_args=[ph_res, mix_data])
    for i in range(0, 50, 1):
        print(i)
        for method in methods:
            print(method)
            temp_lst = []
            start_t = time.time()
            results2 = minner.minimize(method)
            end_t = time.time()
            xxx = results2.params.valuesdict()
            temp_lst.append(i)
            temp_lst.append(method)
            temp_lst.append(xxx["site1"])
            temp_lst.append(xxx["k1"])
            temp_lst.append(xxx["site2"])
            temp_lst.append(xxx["k2"])
            temp_lst.append(xxx["site3"])
            temp_lst.append(xxx["k3"])
            # temp_lst.append(xxx["site4"])
            # temp_lst.append(xxx["k4"])
            temp_lst.append(xxx["ccm"])
            temp_lst.append(end_t - start_t)
            temp_lst.append(results2.residual)
            temp_lst.append(results2.nfev)
            res_df.loc[len(res_df)] = temp_lst

        start_t = time.time()
        sa = SAFast(func=traget_fun_ccm(ph_res, mix_data), x0=x0, lb=lb, ub=ub)
        sa.run()
        end_t = time.time()
        temp_lst = [i, "SAFast", sa.best_x[3], sa.best_x[0],sa.best_x[4], sa.best_x[1],sa.best_x[5], sa.best_x[2],sa.best_x[6], end_t - start_t, sa.best_y,0]
        res_df.loc[len(res_df)] = temp_lst

        start_t = time.time()
        sa = SACauchy(func=traget_fun_ccm(ph_res, mix_data), x0=x0, lb=lb, ub=ub)
        sa.run()
        end_t = time.time()
        temp_lst = [i, "SACauchy",sa.best_x[3], sa.best_x[0],sa.best_x[4], sa.best_x[1],sa.best_x[5], sa.best_x[2],sa.best_x[6], end_t - start_t, sa.best_y,0]
        res_df.loc[len(res_df)] = temp_lst

        start_t = time.time()
        sa = SABoltzmann(func=traget_fun_ccm(ph_res, mix_data), x0=x0, lb=lb, ub=ub)
        sa.run()
        end_t = time.time()
        temp_lst = [i, "SABoltzmann", sa.best_x[3], sa.best_x[0],sa.best_x[4], sa.best_x[1],sa.best_x[5], sa.best_x[2],sa.best_x[6], end_t - start_t, sa.best_y,0]
        res_df.loc[len(res_df)] = temp_lst

        start_t = time.time()
        pso = PSO(func=traget_fun_ccm(ph_res, mix_data), n_dim=7, lb=lb, ub=ub)
        pso.run()
        end_t = time.time()
        temp_lst = [i, "pso",pso.best_x[3], pso.best_x[0],pso.best_x[4], pso.best_x[1],pso.best_x[5], pso.best_x[2],pso.best_x[6], end_t - start_t, pso.best_y,0]
        res_df.loc[len(res_df)] = temp_lst

        start_t = time.time()
        ga = GA(func=traget_fun_ccm(ph_res, mix_data), n_dim=7, lb=lb, ub=ub)
        ga.run()
        end_t = time.time()
        temp_lst = [i, "ga", ga.best_x[3], ga.best_x[0],ga.best_x[4], ga.best_x[1],ga.best_x[5], ga.best_x[2],ga.best_x[6], end_t - start_t, ga.best_y,0]
        res_df.loc[len(res_df)] = temp_lst

        start_t = time.time()
        de = DE(func=traget_fun_ccm(ph_res, mix_data), n_dim=7, lb=lb, ub=ub)
        de.run()
        end_t = time.time()
        temp_lst = [i, "de",de.best_x[3],de.best_x[0],de.best_x[4], de.best_x[1],de.best_x[5], de.best_x[2],de.best_x[6], end_t - start_t, de.best_y,0]
        res_df.loc[len(res_df)] = temp_lst

        res_df.to_csv("bacteria_test_algorithm_ccm.csv")
