#!/bin/bash

outdir="./ATOLL/out"
if [ ! -d "${outdir}" ]; then
    mkdir ${outdir}
fi

# - raw -> lev0
echo "--- raw -> 0 ---"
python3 ../src/converter/QuadAcsmConverter.py ./ATOLL/in/*.txt ${outdir} -n

# - lev0 -> lev0b
echo "--- 0 -> 0b ---"
python3 ../src/converter/EbasQuadAcsmConverter0to0b.py ${outdir}/*.lev0.nas ${outdir}

# - lev0b -> lev1b
echo "--- 0b -> 1b ---"
python3 ../src/converter/EbasQuadAcsmConverter0bto1b.py ${outdir}/*.lev0b.nas ${outdir}

# - lev1b -> lev2b
echo "--- 1b -> 2b ---"
python3 ../src/converter/EbasQuadAcsmConverter1bto2b.py ${outdir}/*.lev1b.nas ${outdir}
