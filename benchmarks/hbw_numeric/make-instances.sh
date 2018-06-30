#!/bin/bash

hbwdir=../hydraulic-blocks-world

mkdir -p problems/3c/v10
mkdir -p problems/3c/v9
mkdir -p problems/3c/v8
mkdir -p problems/3c/v7
mkdir -p problems/3c/v6
mkdir -p problems/3c/v5
mkdir -p problems/3c/v4
#mkdir -p problems/3c/v3

(
    cd problems/3c/v10
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 10 3
    done
)

(
    cd problems/3c/v9
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 9 3
    done
)

(
    cd problems/3c/v8
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 8 3
    done
)

(
    cd problems/3c/v7
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 7 3
    done
)

(
    cd problems/3c/v6
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 6 3
    done
)

(
    cd problems/3c/v5
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 5 3
    done
)

(
    cd problems/3c/v4
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 4 3
    done
)

# (
#     cd problems/3c/v3
#     for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
# 	python ${here}/convert_hbw_to_pddl.py $file 3 3
#     done
# )

mkdir -p problems/4c/v10
mkdir -p problems/4c/v9
mkdir -p problems/4c/v8
mkdir -p problems/4c/v7
mkdir -p problems/4c/v6
mkdir -p problems/4c/v5
mkdir -p problems/4c/v4
#mkdir -p problems/4c/v3

(
    cd problems/4c/v10
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 10 4
    done
)

(
    cd problems/4c/v9
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 9 4
    done
)

(
    cd problems/4c/v8
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 8 4
    done
)

(
    cd problems/4c/v7
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 7 4
    done
)

(
    cd problems/4c/v6
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 6 4
    done
)

(
    cd problems/4c/v5
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 5 4
    done
)

(
    cd problems/4c/v4
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 4 4
    done
)

# (
#     cd problems/4c/v3
#     for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
# 	python ${here}/convert_hbw_to_pddl.py $file 3 4
#     done
# )

mkdir -p problems/5c/v10
mkdir -p problems/5c/v9
mkdir -p problems/5c/v8
mkdir -p problems/5c/v7
mkdir -p problems/5c/v6
mkdir -p problems/5c/v5
mkdir -p problems/5c/v4

(
    cd problems/5c/v10
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 10 5
    done
)

(
    cd problems/5c/v9
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 9 5
    done
)

(
    cd problems/5c/v8
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 8 5
    done
)

(
    cd problems/5c/v7
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 7 5
    done
)

(
    cd problems/5c/v6
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 6 5
    done
)

(
    cd problems/5c/v5
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 5 5
    done
)

(
    cd problems/5c/v4
    for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
	python ${here}/convert_hbw_to_pddl.py $file 4 5
    done
)

# (
#     cd problems/5c/v3
#     for file in ${hbwdir}/p{4,5,6,7}_*.hbw; do
# 	python ${here}/convert_hbw_to_pddl.py $file 3 4
#     done
# )
