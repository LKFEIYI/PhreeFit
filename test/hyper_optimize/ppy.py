import phreeqpy.iphreeqc.phreeqc_dll as phc_mod


prc = phc_mod.IPhreeqc()
prc.load_database('/Users/lyt/Library/CloudStorage/OneDrive-共享的库-onedrive/sciapp/simulation/minteq.v4.dat')

script_string='''
PHASES
    Fix_H+
        H+ = H+
        log_k 0.0  
END

SOLUTION 1
    temp      25
    H(1)      1e-7  charge      
    pe        4
    redox     pe
    units     mmol/kgw
    density   1
    B         0.8  mol/kgw
    Br        0.484
    C(4)      5
    Ca        25
    Cl        0.545 mol/kgw
    Co(2)     0.001 umol/kgw
    Fe(3)     100 umol/kgw
    K         9.49
    Mg        10
    Mn(2)     100 umol/kgw
    Mo        0.005 umol/kgw
    N(-3)     1
    N(5)      1
    Na        0.467 mol/kgw
    Ni        0.3 umol/kgw
    P         0.4 umol/kgw
    S(6)      1
    Si        0.67
    Zn        0.01 umol/kgw
    I         4.57 umol/kgw
    -water    1

EQUILIBRIUM_PHASES 1
    CoFe2O4   0 0
    Fe(OH)2.7Cl.3 0 0
    Ferrihydrite 0 0
    Fix_H+    -7 NaOH      10
    Goethite  0 0
    Hematite  0 0
    K-Jarosite 0 0
    Lepidocrocite 0 0
    Maghemite 0 0
    Magnesioferrite 0 0
    Magnetite 0 0
    Na-Jarosite 0 0
    Aragonite 0 0
    Calcite   0 0
    Chalcedony 0 0
    Quartz    0 0
    Cristobalite 0 0
    Fe3(OH)8  0 0
    Hydroxylapatite 0 0
    Dolomite(ordered) 0 0
'''

prc.run_string(script_string)