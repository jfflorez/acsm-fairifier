#!/bin/bash

outdir="./SIRTA/out"
if [ ! -d "${outdir}" ]; then
    mkdir ${outdir}
fi

# --- NRT --- #
rm -f ${outdir}/*
# - raw -> lev0
echo "--- raw -> 0 ---"
python3 ../src/converter/QuadAcsmConverter.py ./SIRTA/in/SIRTA_ACSM-140113_????????????.txt ${outdir} -n

# - lev0 -> lev0b
echo "--- 0 -> 0b ---"
python3 ../src/converter/EbasQuadAcsmConverter0to0b.py ${outdir}/*.lev0.nas ${outdir}

# - lev0b -> lev1b
echo "--- 0b -> 1b ---"
python3 ../src/converter/EbasQuadAcsmConverter0bto1b.py ${outdir}/*.lev0b.nas ${outdir}

# - lev1b -> lev2b
echo "--- 1b -> 2b ---"
python3 ../src/converter/EbasQuadAcsmConverter1bto2b.py ${outdir}/*.lev1b.nas ${outdir}


<<<<<<< HEAD
# --- REGULAR --- #
rm -f ${outdir}/*
# - raw -> lev0
echo "--- raw -> 0 ---"
python3 ../src/converter/QuadAcsmConverter.py ./SIRTA/in/SIRTA_ACSM-140113_????.txt ${outdir} -e ./SIRTA/in/*FLAGS*.txt

# - lev0 -> lev0b
echo "--- 0 -> 0a ---"
python3 ../src/converter/EbasQuadAcsmConverter0to0b.py ${outdir}/*.lev0.nas ${outdir}  -i

# - lev0b -> lev1b
echo "--- 0a -> 1 ---"
python3 ../src/converter/EbasQuadAcsmConverter0bto1b.py ${outdir}/*.lev0a.nas ${outdir} -i

# - lev1 -> lev2
echo "--- 1 -> 2 ---"
python3 ../src/converter/EbasQuadAcsmConverter1bto2b.py ${outdir}/*.lev1.nas ${outdir} -i