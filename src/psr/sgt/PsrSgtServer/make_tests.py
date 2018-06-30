import oct2py
import os
import os.path
import shutil
import subprocess

case_paths = [
    "data/nesta_mod/nesta_case4_gs.m",
    "data/nesta_mod/nesta_case5_pjm.m",
    "data/nesta_mod/nesta_case6_c.m",
    "data/nesta_mod/nesta_case6_ww.m",
    "data/nesta_mod/nesta_case9_wscc.m",
    "data/nesta_mod/nesta_case14_ieee.m",
    "data/nesta_mod/nesta_case24_ieee_rts.m",
    "data/nesta_mod/nesta_case29_edin.m",
    "data/nesta_mod/nesta_case30_as.m",
    "data/nesta_mod/nesta_case30_fsr.m"
]

octave = oct2py.Oct2Py();

for p in case_paths:
    cmds = [
        'idxs = int8(loadcase([pwd, "/", "' + p + '"]).bus(:, 1));',
        'ndig = int8(length(num2str(int8(max(idxs)))));'
    ]
    for cmd in cmds:
        octave.eval(cmd)

    ndig = octave.pull("ndig")
    idxs = [str(x[0]).zfill(ndig) for x in octave.pull("idxs")]

    d, c = os.path.split(p)
    c = c.split('.')[0]

    shutil.rmtree("data/tests/" + c, ignore_errors=True)
    os.mkdir("data/tests/" + c)
    for idx in idxs:
        print("------------------------------------------------------------------")
        fault = "bus_" + idx
        cmd = [
            "setup_problem",
            "--faults", fault,
            "--outfile", "data/tests/" + c + "/faults_" + fault + ".yaml",
            "--method", "socp",
            p
        ]
        print(' '.join(cmd))
        print("------------------------------------------------------------------")
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(proc.stdout.decode('utf8'))
        print("------------------------------------------------------------------")
