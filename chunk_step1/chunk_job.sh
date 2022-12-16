#! /bin/sh

# Load required modules
module purge
module load python/3.7.5

# Define use settings
date_beg=20200807
date_end=20200930
n_chunks=8
tmpl_name=config.vrfy_grid2obs.tmpl
config_name=config.vrfy_grid2obs

# Run split_datelist.py to generate start/end dates for each of n_chunks
# NOTE: Python3 is REQUIRED for this script
python3 split_datelist.py << EOF > split_dates.txt
${date_beg}
${date_end}
${n_chunks}
EOF

# For each chunk n:
#  1. Copy ${tmpl_name} to config.tmp
#  1. Extract start/end dates
#  2. Replace template key-words (>>OUTDIR<<, >>START_DATE<<, >>END_DATE<<)
#  3. Move to ${config_name}.chunk${n}
let n=0
while [ ${n} -lt ${n_chunks} ]
do
  let n++
  cp ${tmpl_name} config.tmp
  date1=`awk NR==${n} split_dates.txt | awk '{print $1}'`
  date2=`awk NR==${n} split_dates.txt | awk '{print $2}'`
  sed "s/>>OUTDIR<</verify_global_standalone.chunk.${n}/g" config.tmp > tmp.file
  mv tmp.file config.tmp
  sed "s/>>START_DATE<</${date1}/g" config.tmp > tmp.file
  mv tmp.file config.tmp
  sed "s/>>END_DATE<</${date2}/g" config.tmp > tmp.file
  mv tmp.file config.tmp
  mv config.tmp ${config_name}.chunk${n}
done

