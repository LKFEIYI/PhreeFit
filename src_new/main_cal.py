# cython: language_level=3
import os
from pathlib import Path
import sys
import threading

import numpy as np
import phreeqpy.iphreeqc.phreeqc_dll as phc_mod
from scipy.optimize import dual_annealing, differential_evolution, minimize


OPTIMIZATION_CONVERGENCE_TOLERANCE = 1e-7
FINAL_CONVERGENCE_TOLERANCE = 1e-8

_DISABLE_SELECTED_OUTPUT = '''
PRINT
    -selected_output false
END
'''

_ENABLE_SELECTED_OUTPUT = '''
PRINT
    -selected_output true
END
'''

_iphreeqc_local = threading.local()


def _configured_iphreeqc_library():
    """Return the explicit or project-bundled IPhreeqc library when available."""
    configured = os.environ.get("PHREEFIT_IPHREEQC_LIBRARY")
    if configured:
        return configured

    if sys.platform == "darwin":
        library_name = "libiphreeqc-3.8.6.dylib"
    elif sys.platform == "win32":
        library_name = "IPhreeqc-3.8.6.dll"
    else:
        return None

    candidates = []
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        candidates.append(Path(frozen_root) / "iphreeqc" / library_name)
    candidates.append(
        Path(__file__).resolve().parents[1] / "packaging" / "lib" / library_name
    )
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None


def _new_iphreeqc():
    """Create an instance using the configured or packaged 3.8.6 library."""
    library = _configured_iphreeqc_library()
    return phc_mod.IPhreeqc(library) if library else phc_mod.IPhreeqc()


def _get_cached_iphreeqc(database):
    """Return one database-loaded IPhreeqc instance per process and thread."""
    pid = os.getpid()
    cached = getattr(_iphreeqc_local, "instance", None)
    cached_pid = getattr(_iphreeqc_local, "pid", None)
    cached_database = getattr(_iphreeqc_local, "database", None)

    if cached is not None and cached_pid == pid and cached_database == database:
        return cached

    # Never destroy a pointer inherited through fork in the child process.
    if cached is not None and cached_pid == pid:
        cached.destroy_iphreeqc()

    instance = _new_iphreeqc()
    try:
        instance.load_database_string(database)
    except Exception:
        instance.destroy_iphreeqc()
        raise
    _iphreeqc_local.instance = instance
    _iphreeqc_local.pid = pid
    _iphreeqc_local.database = database
    return instance


def close_cached_iphreeqc():
    """Release the IPhreeqc instance owned by the current process/thread."""
    instance = getattr(_iphreeqc_local, "instance", None)
    if instance is not None and getattr(_iphreeqc_local, "pid", None) == os.getpid():
        instance.destroy_iphreeqc()
    for attribute in ("instance", "pid", "database"):
        if hasattr(_iphreeqc_local, attribute):
            delattr(_iphreeqc_local, attribute)


def _run_cached(database, script, convergence_tolerance):
    """Run a script while preventing selected-output rows from leaking between runs."""
    instance = _get_cached_iphreeqc(database)
    run_script = '''
KNOBS
    -convergence_tolerance {0:.0e}
END
'''.format(convergence_tolerance) + _DISABLE_SELECTED_OUTPUT + script
    try:
        instance.run_string(run_script)
        return instance.get_selected_output_array()
    except Exception:
        # A failed PHREEQC run can leave partial definitions in the instance.
        close_cached_iphreeqc()
        raise


class OptimizationCancelled(Exception):
    """Raised when the user requests that an optimization stop safely."""


class SurfaceSpecies2:
    def __init__(self):
        self.surface_name = None
        self.surface_mp = None
        self.surface_area = None
        self.surface_mass = None
        self.surface_sites = None
        self.surface_C1 = None
        self.surface_C2 = None
        self.surface_reactions = {}
        self.sfinitial = None

    def add_surface(self, surfacename: str, surface_ms: str, sites, area, mass, c1, c2, sites_initial, c1_initial=1,
                    c2_initial=1):
        self.surface_name = surfacename
        self.surface_mp = surface_ms
        self.surface_sites = sites
        self.surface_area = area
        self.surface_mass = mass
        self.surface_C1 = c1  # ccm value for CCM
        self.surface_C2 = c2
        self.sfinitial = (sites_initial, c1_initial, c2_initial)

    def add_reactions(self, reactions: str, k, z1, z0d: bool, ztotal, k_initial=0, z1_initial=1):
        self.surface_reactions[reactions] = [k, z1, z0d, ztotal, k_initial, z1_initial]

    def reset_cap(self, c1, c2):  # reset ccm to reduce parameter input
        self.surface_C1 = c1
        self.surface_C2 = c2

    #
    def get_all_species(self):
        if len(self.surface_reactions) == 0:
            return []
        else:
            species_list = []
            for keys in self.surface_reactions.keys():
                seperated_species = keys.split()
                for specise in seperated_species:
                    if specise.startswith(self.surface_name):
                        species_list.append(specise)
            # Preserve reaction order so result columns and plot legends are stable.
            return list(dict.fromkeys(species_list))


class Adsorption:
    def __init__(self, type_of_problem: str):
        self.first_mix = ""
        self.titration_solution = ""
        self.definition = ""
        self.initial_condition = ""
        self.p_type = type_of_problem
        self.surface = []
        self.sms = ""
        self.initial_guess = []
        self.bounds = []
        self.total = ""
        self.ph_test = ""
        self.eq = ''
        self.acid_base = []
        self.unknown_surface = False
        self.surf_eq_solution = ""
        self.all_surfacespecies = []

    def species_definition(self, database: str, otherspecies=""):
        #with open(database_path, "r", encoding="UTF-8") as file:
        self.database = database
        self.definition = otherspecies

    def set_type_acid(self, type_acid="HNO3", type_base="NaOH"):
        self.acid_base.clear()
        self.acid_base.append(type_acid)
        self.acid_base.append(type_base)

    def initial_solution(self, na, metal: dict, initial_pH=7.0, cation="Na", anion="Cl"):
        n = 1
        self.cs_lst = na
        self.initial_condition = ""
        # ensure charge balance
        for na_con in na:
            if initial_pH <= 7:
                c_anion = str(na_con) + "    charge"
                c_cation = na_con
            else:
                c_cation = str(na_con) + "    charge"
                c_anion = na_con
            initial_con = '''
        SOLUTION {5}
             temp      25
             pH        {0}
             pe        4
             redox     pe
             units     mol/l
             density   1
             {1}        {3}
             {2}        {4}
             -water    1 # kg
         '''.format(initial_pH, cation, anion, c_cation, c_anion, n)

            if metal:
                for i in metal.keys():
                    initial_con += '''
        REACTION 1
            {0} 1
            {1} moles in 1 steps'''.format(i, metal[i])
            initial_con += '''
        SAVE solution {0}
        END
            '''.format(n)
            n += 1
            self.initial_condition += initial_con
        self.initial_condition += '''
        PHASES
            Fix_H+
                H + = H +
                log_k     0
        END
        '''

    def equilibrate_solution(self, ionic_strength=0.01, initial_pH=7.0, cation="Na", anion="Cl"):
        #this solution is for equilibrium with surface, especially for
        #some mud-like samples, e.g., bacteria, sediments
        self.unknown_surface = True
        if initial_pH <= 7:
            c_anion = str(ionic_strength) + "    charge"
            c_cation = ionic_strength
        else:
            c_cation = str(ionic_strength) + "    charge"
            c_anion = ionic_strength
        self.surf_eq_solution = '''
        SOLUTION 10
             temp      25
             pH        {0}
             pe        4
             redox     pe
             units     mol/l
             density   1
             {1}        {3}
             {2}        {4}
             -water    1000 # kg
        END
         '''.format(initial_pH, cation, anion, c_cation, c_anion)

    def mix_solution(self, acid_mass=0.0, base_mass=0.0, acid_pH=7, base_pH=7, type_solution="fix_pH"):
        self.titration_solution = '''        
        SOLUTION 11
            temp      25
            pH        7
            pe        4
            redox     pe
            units     mol/kgw
            density   1
            -water    1 # kg
        END'''

        if type_solution == "fix_pH":
            self.titration_solution += '''
        USE solution 11              
        EQUILIBRIUM_PHASES 1
            Fix_H+ {0} {1} 20
        SAVE solution 12
        END
            '''.format(-acid_pH, self.acid_base[0])
            self.titration_solution += '''     
        USE solution 11
        EQUILIBRIUM_PHASES 1
            Fix_H+ {0} {1} 20
        SAVE solution 13
        END       
                    '''.format(-base_pH, self.acid_base[1])
        elif type_solution == "dissolution":
            self.titration_solution += '''     
        USE solution 11
        REACTION 1
            {0}
            {1} moles in 1 steps
        SAVE solution 12
        END        
            '''.format(self.acid_base[0], acid_mass)
            self.titration_solution += '''     
        USE solution 11
        REACTION 1
            {0}
            {1} moles in 1 steps
        SAVE solution 13
        END        
                '''.format(self.acid_base[1], base_mass)
        else:
            raise Exception("Solution type should be fix_pH or dissolution")

    def selected_output(self, output: dict):
        self.output = '''
        SELECTED_OUTPUT 1
            -reset                false
            -simulation           true
            -pH                   true
            -water                true           
        '''
        for i in output.keys():
            self.output += "    -" + i + "                " + output[i] + "\n"

    def mix_action(self, initial_volume, mix_volume):
        self.first_mix = ""
        n = 1
        if len(self.cs_lst) == 1:
            acid_volume = 0
            base_volume = 0
            for v in mix_volume:
                if v < 0:
                    base_volume = v
                else:
                    acid_volume = v
                self.first_mix += '''
            USE surface 1
            MIX {0}
                1    {1}
                12    {2}
                13    {3}
            END'''.format(n, initial_volume / 1000, acid_volume / 1000, abs(base_volume / 1000))
                n += 1
        else:
            for i in range(0, len(self.cs_lst)):
                acid_volume = 0
                base_volume = 0
                vols = mix_volume.get_group(self.cs_lst[i])["volume"].to_list()
                for v in vols:
                    if v < 0:
                        base_volume = v
                    else:
                        acid_volume = v
                    self.first_mix += '''
                                USE surface 1
                                MIX {0}
                                    {4}    {1}
                                    12    {2}
                                    13    {3}
                                END'''.format(n, initial_volume / 1000, acid_volume / 1000, abs(base_volume / 1000),
                                              i + 1)
                    n += 1

    def eq_ph(self, ph_list, eq_phase, ph_sep, auto_p=False):
        if auto_p == True:
            ph_sep = self.initial_ph(eq_phase=eq_phase)
        self.eq = ''''''
        if len(self.cs_lst) == 1:
            for i in ph_list:
                # print(i)
                if i > ph_sep:
                    aorb = self.acid_base[1]  #base
                else:
                    aorb = self.acid_base[0]
                self.eq += '''
                 EQUILIBRIUM_PHASES 1
                     Fix_H+ {0} {2} 20
                     {1}
                 USE surface 1
                 USE solution 1
                 END
                 '''.format(-i, eq_phase, aorb)
        else:
            for j in range(0, len(self.cs_lst)):
                ph = ph_list.get_group(self.cs_lst[j])["pH"].to_list()
                for i in ph:
                    # print(i)
                    if i > ph_sep[j]:
                        aorb = self.acid_base[1]
                    else:
                        aorb = self.acid_base[0]
                    self.eq += '''
                    EQUILIBRIUM_PHASES 1
                        Fix_H+ {0} {3} 20
                        {2}
                    USE surface 1
                    USE solution {1}
                    END
                    '''.format(-i, j + 1, eq_phase, aorb)

    def add_surface(self, sp: SurfaceSpecies2):
        self.surface.append(sp)

    def get_bounds(self):
        self.bounds.clear()
        self.initial_guess.clear()
        self.all_surfacespecies.clear()
        for sp in self.surface:
            self.all_surfacespecies += sp.get_all_species()
            if isinstance(sp.surface_sites, tuple) == True:
                self.bounds.append(sp.surface_sites)
                self.initial_guess.append(sp.sfinitial[0])
            for react in sp.surface_reactions.keys():
                k = sp.surface_reactions[react][0]
                init_k = sp.surface_reactions[react][4]
                if isinstance(k, tuple) == True:
                    self.bounds.append(k)
                    self.initial_guess.append(init_k)
                if self.p_type == 'CDMUSIC':
                    if sp.surface_reactions[react][2] == True:
                        if isinstance(sp.surface_reactions[react][1], tuple) == True:
                            self.bounds.append(sp.surface_reactions[react][1])
                            self.initial_guess.append(sp.surface_reactions[react][5])
                    else:
                        if isinstance(sp.surface_reactions[react][1], tuple) == True:
                            self.bounds.append(sp.surface_reactions[react][1])
                            self.initial_guess.append(sp.surface_reactions[react][5])
            if self.p_type == "CCM":
                if isinstance(sp.surface_C1, tuple) == True:
                    self.initial_guess.append(sp.sfinitial[1])
                    self.bounds.append(sp.surface_C1)
            elif self.p_type == 'CDMUSIC':
                if isinstance(sp.surface_C1, tuple) == True:
                    self.bounds.append(sp.surface_C1)
                    self.initial_guess.append(sp.sfinitial[1])
                if isinstance(sp.surface_C2, tuple) == True:
                    self.bounds.append(sp.surface_C2)
                    self.initial_guess.append(sp.sfinitial[2])

    def set_para(self, unknowns):
        self.sms = ""
        surface_keywords = "\n" + "        " + "SURFACE_MASTER_SPECIES"
        surface_amounts = "\n" + "        " + "SURFACE 1"
        if self.unknown_surface == True:
            surface_amounts += "\n" + "            " + "-equilibrate with solution 10"
        surface_reaction = "\n" + "        " + "SURFACE_SPECIES"
        n = 0
        for sp in self.surface:
            surface_keywords += "\n" + "            " + sp.surface_name + "\t" + sp.surface_mp
            if isinstance(sp.surface_sites, tuple) == False:
                surface_amounts += "\n" + "            " + sp.surface_mp + "\t" + str(sp.surface_sites) + "\t" + str(
                    sp.surface_area) + "\t" + str(sp.surface_mass)
            else:
                surface_amounts += "\n" + "            " + sp.surface_mp + "\t" + str(unknowns[n]) + "\t" + str(
                    sp.surface_area) + "\t" + str(sp.surface_mass)
                n += 1
            surface_reaction += "\n" + "            " + sp.surface_mp + " = " + sp.surface_mp
            surface_reaction += "\n" + "                " + "log_k 0"
            if self.p_type == "CDMUSIC":
                surface_reaction += "\n" + "            " + '-cd_music  0 0 0'
            for react in sp.surface_reactions.keys():
                surface_reaction += "\n" + "            " + react
                k = sp.surface_reactions[react][0]
                if isinstance(k, tuple) == False:
                    surface_reaction += "\n" + "                " + "log_k " + str(k)
                else:
                    surface_reaction += "\n" + "                " + "log_k " + "\t" + str(unknowns[n])
                    n += 1
                if self.p_type == 'CDMUSIC':
                    if sp.surface_reactions[react][2] == True:
                        if isinstance(sp.surface_reactions[react][1], tuple) == False:
                            surface_reaction += "\n" + "            " + '-cd_music  ' + str(
                                sp.surface_reactions[react][3] - sp.surface_reactions[react][1]) + " " + str(
                                sp.surface_reactions[react][1]) + ' 0'
                        else:
                            surface_reaction += "\n" + "            " + '-cd_music  ' + str(
                                sp.surface_reactions[react][3] - unknowns[n]) + " " + str(unknowns[n]) + ' 0'
                            n += 1
                    else:
                        if isinstance(sp.surface_reactions[react][1], tuple) == False:
                            surface_reaction += "\n" + "            " + '-cd_music  ' + '0 ' + str(
                                sp.surface_reactions[react][1]) + " " + str(
                                sp.surface_reactions[react][3] - sp.surface_reactions[react][1])
                        else:
                            surface_reaction += "\n" + "            " + '-cd_music  ' + '0 ' + str(
                                unknowns[n]) + " " + str(sp.surface_reactions[react][3] - unknowns[n])
                            n += 1

            if self.p_type == "CCM":
                if isinstance(sp.surface_C1, tuple) == False:
                    surface_amounts += "\n" + "        -ccm " + str(sp.surface_C1)
                else:
                    surface_amounts += "\n" + "        -ccm " + str(unknowns[n])
                    n += 1
            elif self.p_type == 'CDMUSIC':
                if isinstance(sp.surface_C1, tuple) == False:
                    surface_amounts += "\n" + '                    -capacitances ' + str(sp.surface_C1)
                else:
                    surface_amounts += "\n" + '                    -capacitances ' + str(unknowns[n])
                    n += 1
                if isinstance(sp.surface_C2, tuple) == False:
                    surface_amounts += " " + str(sp.surface_C2)
                else:
                    surface_amounts += " " + str(unknowns[n])
                    n += 1
        surface_reaction += "\n" + "        " + "END"
        if self.p_type == "NEM":
            surface_amounts += "\n" + "        -no_edl" + "\n" + "        " + "END"
        elif self.p_type == "GDDL":
            surface_amounts += "\n" + "        -ddl" + "\n" + "        " + "END"
        elif self.p_type == 'CDMUSIC':
            surface_amounts += "\n" + "        -cd_music" + "\n" + "        " + "END"
        else:
            surface_amounts += "\n" + "        " + "END"
        self.sms += surface_keywords + surface_reaction + surface_amounts

    def create_script(self, mix=False):

        if mix:
            self.total = self.initial_condition + self.surf_eq_solution + self.titration_solution + self.sms + self.output + _ENABLE_SELECTED_OUTPUT + self.first_mix
        else:
            self.total = self.initial_condition + self.sms + self.output + _ENABLE_SELECTED_OUTPUT + self.eq

    def create_eval_script(self, mix=False, species_output=False):
        if species_output:
            additional_output="    -molalities     " + " ".join(self.all_surfacespecies,)

        else:
            additional_output=""
        if mix:
            self.total = self.initial_condition + self.surf_eq_solution + self.titration_solution + self.sms + self.output + additional_output + _ENABLE_SELECTED_OUTPUT + self.first_mix
        else:
            self.total = self.initial_condition + self.sms + self.output + additional_output + _ENABLE_SELECTED_OUTPUT + self.eq


    def initial_ph(self, eq_phase):
        temp_eq = ""
        if eq_phase != "":
            temp_eq = '''
                 EQUILIBRIUM_PHASES 1
                     {0}
            '''.format(eq_phase)
        if len(self.cs_lst) == 1:
            temp_eq += '''
                 USE surface 1
                 USE solution 1
                 END
                 '''
        else:
            temp_eq += ""
            for j in range(0, len(self.cs_lst)):
                temp_eq += '''
                 USE surface 1
                 USE solution {0}
                 END
                 '''.format(j + 1)

        self.ph_test = self.initial_condition + self.sms + self.output + _ENABLE_SELECTED_OUTPUT + temp_eq
        return get_pH(_run_cached(
            self.database, self.ph_test, OPTIMIZATION_CONVERGENCE_TOLERANCE
        ))


def get_pH(ppp):
    re_ph = []
    #ph = ppp.get_selected_output_array()
    for i in range(1, len(ppp)):
        re_ph.append(ppp[i][1])
    return np.array(re_ph)


def get_metal(ppp):
    re_total_metal = []
    #metal = ppp.get_selected_output_array()
    for i in range(1, len(ppp)):
        re_total_metal.append(ppp[i][3])
    return np.array(re_total_metal)


def run_phreeqc(titration: Adsorption):
    return get_pH(_run_cached(
        titration.database, titration.total, OPTIMIZATION_CONVERGENCE_TOLERANCE
    ))


def advanced_fun(p, exp_data, titration: Adsorption, mix=False):
    titration.set_para(p)
    titration.create_script(mix)
    error = run_phreeqc_ad(titration) - exp_data
    return np.linalg.norm(error)


def advanced_fun_auto(p, exp_data, ph_list, eq_phase, titration: Adsorption, mix=False):
    titration.set_para(p)
    titration.eq_ph(ph_list=ph_list, eq_phase=eq_phase, ph_sep=None, auto_p=True)
    titration.create_script(mix)
    error = run_phreeqc_ad(titration) - exp_data
    return np.linalg.norm(error)


def proto_fun(p, exp_data, titration: Adsorption, mix=False):
    titration.set_para(p)
    # print(p)
    titration.create_script(mix)
    error = run_phreeqc(titration) - exp_data
    return np.linalg.norm(error)


def advanced_evaluation(exp_data, results, titration: Adsorption, mix=False, auto_p=False,
                        eq=None, ph_list=None, error=None, stop_requested=None):
    p = results.x
    titration.set_para(p)

    if auto_p is True:
        titration.eq_ph(ph_list=ph_list, eq_phase=eq, auto_p=True, ph_sep=None)
    titration.create_eval_script(mix,True)
    #print(titration.total)
    all_output = run_phreeqc_eval(titration)
    if mix is False:
        model_res = get_metal(all_output)
    else:
        model_res = get_pH(all_output)
    #print(model_res)
    raw_r2 = r2(exp_data, model_res)
    adj_r2 = 1 - (1 - raw_r2) * (len(exp_data) - 1) / (len(exp_data) - 1 - len(p))
    rms = results.fun / len(exp_data) ** 0.5
    BIC = len(exp_data) * np.log(results.fun ** 2 / len(exp_data)) + np.log(len(exp_data)) * len(p)
    if error is None:
        if mix is False:
            error_list=exp_data*0.05
        else:
            # error_list=np.full(len(exp_data), 0.005)
            error_list=exp_data*0.02303
    else:
        error_list=error
    reduced_chi=reduced_x2(exp_data, model_res,error_list,len(exp_data)-len(p))
    try:
        # Local import keeps the optimization/calculation module independent of
        # sensitivity-analysis implementation details during module loading.
        from .sensitivity import estimate_parameter_uncertainty
        mix_mode = 0 if mix else (2 if auto_p else 1)
        parameter_uncertainty = estimate_parameter_uncertainty(
            problem=titration,
            optimal_parameters=p,
            experimental_data=exp_data,
            baseline_response=model_res,
            bounds=titration.bounds,
            error_list=error_list,
            mix_mode=mix_mode,
            ph_list=ph_list,
            eq_phase=eq,
            stop_requested=stop_requested,
        )
    except OptimizationCancelled:
        raise
    except Exception:
        parameter_uncertainty = np.full(len(p), np.nan, dtype=float)
    titration.set_para(p)
    return (raw_r2, adj_r2, BIC, rms, results.nfev, model_res, titration.sms,
            all_output, reduced_chi, parameter_uncertainty)


def run_phreeqc_ad(titration: Adsorption):
    return get_metal(_run_cached(
        titration.database, titration.total, OPTIMIZATION_CONVERGENCE_TOLERANCE
    ))

def run_phreeqc_eval(titration: Adsorption):
    # Final reporting should be independent of the last optimizer state. This
    # one-time reload is negligible compared with the many cached evaluations.
    close_cached_iphreeqc()
    return _run_cached(
        titration.database, titration.total, FINAL_CONVERGENCE_TOLERANCE
    )

def reduced_x2(exp_data, model_data, error, f):
    ssd = 0
    for i in range(0, len(exp_data)):
        ssd += ((model_data[i] - exp_data[i])/ error[i])**2
    return ssd / f


def r2(exp_data, model_data):
    sst = 0
    sse = 0
    average = np.mean(exp_data)
    for i in range(0, len(exp_data)):
        sst += (exp_data[i] - average) ** 2
        sse += (model_data[i] - exp_data[i]) ** 2
    return 1 - sse / sst


def optimize_problem(mix_or_eq, method, x0, bounds, maxiter=1000, core=1, t=5230, extra_para=None,
                     stop_requested=None):
    # args for proto_fun is exp_data,titration:Adsorption,mix=ture
    # args for advanced_fun is exp_data, titration:Adsorption,mix=False
    # args for advanced_fun_auto is exp_data,ph_list,eq_phase, titration:Adsorption,mix=False
    # print(maxiter)
    if mix_or_eq == 0:
        residual_func = proto_fun
    elif mix_or_eq == 1:
        residual_func = advanced_fun
    else:
        residual_func = advanced_fun_auto

    def check_cancelled(*args, **kwargs):
        if stop_requested is not None and stop_requested():
            raise OptimizationCancelled("Terminated by user")

    check_cancelled()
    if method == "Differential evolution":
        param_de = {
            'strategy': "best1bin",
            'init': "halton",
            'recombination': 0.8
        }
        if  extra_para[-2].p_type == "CDMUSIC":
            param_de = {
                'strategy': "best1exp",
                'init': "halton",
                'recombination': 0.9,
                'popsize': 8,
            }
        elif extra_para[-2].p_type == "CCM":
            param_de = {
                'strategy': "best1exp",
                'init': "halton",
                'recombination': 0.9,
            }
        if core > 1:
            de_results = differential_evolution(residual_func, bounds=bounds, x0=x0, maxiter=maxiter, updating="deferred",
                                              workers=core, args=extra_para, polish=False,
                                              callback=check_cancelled, **param_de)
        else:
            de_results = differential_evolution(residual_func, bounds=bounds, x0=x0, maxiter=maxiter,
                                                args=extra_para, polish=False, callback=check_cancelled, **param_de)
        check_cancelled()
        polished_results = minimize(residual_func, options={"adaptive": True}, bounds=bounds, x0=de_results.x,
                                    method="Nelder-Mead", args=extra_para, callback=check_cancelled)
        if polished_results.success and polished_results.fun < de_results.fun:
            results=polished_results
            results.nfev += de_results.nfev
        else:
            results=de_results
    elif method == "Dual annealing":
        results = dual_annealing(residual_func, bounds=bounds, x0=x0, maxiter=maxiter, initial_temp=t,
                                 args=extra_para, callback=check_cancelled)
    elif method == "Nelder Mead":
        results = minimize(residual_func, options={"adaptive": True}, bounds=bounds, x0=x0,
                           method="Nelder-Mead", args=extra_para, callback=check_cancelled)
    elif method == "Powell":
        results = minimize(residual_func, bounds=bounds, x0=x0, method="Powell", args=extra_para,
                           callback=check_cancelled)
    else:
        pass
    return results
