"""Background optimization worker used by the main window."""

import threading
import time

import numpy as np
from PySide6.QtCore import QThread, Signal

from . import main_cal as mc


class WorkThreadAdvanced(QThread):
    signals = Signal(dict)

    def __init__(self):
        super(WorkThreadAdvanced, self).__init__()
        self._stop_event = threading.Event()

    def request_stop(self):
        self._stop_event.set()
        self.requestInterruption()

    def stop_requested(self):
        return self._stop_event.is_set() or self.isInterruptionRequested()

    def set_pa(self, p1, p2, max_t, T, mix, ph_list=None, eq=None, method="Differential evolution", process_num=1,task=None,error_list=None):
        self.p1 = p1
        self.p2 = p2
        self.max_t = max_t
        self.T = T
        self.mix_or_eq = mix  # 0:mix 1: eq 2: auto_eq
        self.msg = {}
        # self.sep_ph =sep_ph #ph separate point
        self.eq = eq  # extra equilibrium phase in text
        self.ph_list = ph_list  # ph list for equilibrium
        self.method = method
        self.processes = process_num
        self.task_name=task
        self.error_list = error_list

    def run(self):
        # args for proto_fun is exp_data,titration:Adsorption,mix=ture
        # args for advanced_fun is exp_data, titration:Adsorption,mix=False
        # args for advanced_fun_auto is exp_data,ph_list,eq_phase, titration:Adsorption,mix=False
        problem_type = False
        auto_ph = False
        try:
            if self.mix_or_eq == 0:
                mix = True
                problem_type = True

                fix_para = (self.p2, self.p1, mix)
            elif self.mix_or_eq == 1:  # no auto calculate, use given pH value
                mix = False

                fix_para = (self.p2, self.p1, mix)
            elif self.mix_or_eq == 2:  # automatically calculate pH for each parameters
                mix = False
                auto_ph = True
                fix_para = (self.p2, self.ph_list, self.eq, self.p1, mix)
            st_eva_t = time.time()
            results = mc.optimize_problem(self.mix_or_eq, method=self.method, x0=np.array(self.p1.initial_guess),
                                          bounds=self.p1.bounds, maxiter=self.max_t, core=self.processes, t=self.T,
                                          extra_para=fix_para, stop_requested=self.stop_requested)
            ed_eva_t = time.time()
            res_str = ""

            if self.stop_requested():
                raise mc.OptimizationCancelled("Terminated by user")
            eva = mc.advanced_evaluation(exp_data=self.p2, titration=self.p1, results=results, mix=mix, eq=self.eq,
                                         ph_list=self.ph_list, auto_p=auto_ph, error=self.error_list)
            res_str += "Optimized parameters: "
            for x in results.x:
                res_str += str(x) + "  "
            res_str += "\n" + "R2" + "\t" + "adj. R2" + "\t" + "BIC"  + "\t" + "RMSE" + "\t" + "V(Y)"+ "\t" + "Evaluations" + "\n"
            for y in eva[0:3]:
                res_str += "{:.5f}".format(y) + "\t"
            res_str += "{:.3e}".format(eva[3]) + "\t" + "{:.3e}".format(eva[8]) + "\t" + str(eva[4])
            # write_results(self.p2, eva[4],self.output_folder)
            self.msg["Task"]="Task: "+self.task_name
            self.msg["successful"] = True
            self.msg["eva"] = res_str + "\n"
            self.msg["model"] = eva[5].tolist()
            self.msg["surface"] = eva[6]
            self.msg["type"] = problem_type
            self.msg["time"] = "Time: {:.2f} s".format(ed_eva_t - st_eva_t)
            self.msg["speciation"]=eva[7]
            self.msg["surface_species"] = list(self.p1.all_surfacespecies)
            self.msg["surface_species_groups"] = [
                {
                    "surface_name": surface.surface_name,
                    "species": surface.get_all_species(),
                }
                for surface in self.p1.surface
            ]
            self.msg["iterations"] = eva[4]
            self.signals.emit(self.msg)
        except mc.OptimizationCancelled as e:
            self.msg["Task"] = "Task: " + self.task_name
            self.msg["successful"] = False
            self.msg["cancelled"] = True
            self.msg["error"] = str(e)
            self.signals.emit(self.msg)
        except Exception as e:
            self.msg["Task"] = self.task_name
            self.msg["successful"] = False
            self.msg["error"] = str(e)
            self.signals.emit(self.msg)
