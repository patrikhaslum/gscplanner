#!/bin/bash

SRCDIR=../../../src
DATADIR=../../../src/psr/sgt/PsrSgtServer/data
TESTNWS="nesta_case4_gs nesta_case6_c nesta_case6_ww nesta_case9_wscc nesta_case14_ieee nesta_case24_ieee_rts nesta_case29_edin nesta_case30_as nesta_case30_fsr"

for nwname in ${TESTNWS}; do
    for pfile in `ls ${DATADIR}/tests/${nwname}`; do
	pname=`basename $pfile .yaml`
	echo "${DATADIR}/nesta_mod/${nwname}.m ${DATADIR}/tests/${nwname}/${pfile}"
	python ${SRCDIR}/nw_parse_tool.py --pddl ${DATADIR}/nesta_mod/${nwname}.m ${DATADIR}/tests/${nwname}/${pfile} > ${nwname}_${pname}.pddl
    done
done
