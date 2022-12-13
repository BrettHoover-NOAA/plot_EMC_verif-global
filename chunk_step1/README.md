**Purpose**  
  
This set of scripts is designed to take an EMC_verify-global step1 job (statistics generation for grid2grid, grid2obs, etc)  
and generate multiple config.vrfy files for the task, each of which works in a separate work-directory space and each of  
which covers only a segment (a "chunk") of the total time between the beginning and ending date. This is done so that each  
chunk can be run in parallel by submitting each job separately, and avoid walltime limits for generating all statistics with  
a single job and greatly speed up job time.  
  
**Contents**  
  
*chunk_job.sh*: Takes date settings, number of chunks, and config.vfry template to generate separate config.vrfy for each chunk.  
*split_datelist.py*: Generates beginning/ending dates for each chunk by splitting total time period into as-equal-as-possible pieces.  
  
**Execution**  
  
The config.vrfy.tmpl template-file is set as per a normal config.vrfy file for running the step1 jobs, but contains three wildcards:  
. >>OUTDIR<<: subdirectory of OUTPUTROOT defining work-directory space for a chunk  
. >>START_DATE<<: beginning date (YYYYMMDD) of total time-period for job  
. >>END_DATE<<: ending date of total time-period for job  
  
The ">> <<" format is used to distinguish these as wildcards.  
  
The chunk_job.sh script has settings for the following variables:  
date_beg: input to replace >>START_DATE<< wildcard in template file  
date_end: input to replace >>END_DATE<< wildcard in template file  
n_chunks: number of chunks (some integer value)  
tmpl_name: name of template file  
config_name: name of each config.vrfy file generated for each chunk, will end in ".chunk#" for each chunk (1,2,3,...)  
  
For example:  
date_beg=20220101  
date_end=20220131  
n_chunks=6  
tmpl_name=config.vrfy.step1.tmpl  
config_name=config.vrfy.step1  
  
These settings will use the supplied template in config.vrfy.step1.tmpl to generate 6 config files named  
config.vrfy.step1.chunk[1,...6], each writing to verify_global_standalone.chunk.[1,...,6], and each covering the dates:  
  
chunk1: 20220101–20220105 (5 days)  
chunk2: 20220106–20220110 (5 days)  
chunk3: 20220111–20220115 (5 days)  
chunk4: 20220116–20220120 (5 days)  
chunk5: 20220121–20220125 (5 days)  
chunk6: 20220126–20220131 (6 days)  
  
Each of these jobs can be individually submitted to generate statistics for whichever step1 jobs were specified in the  
template file via:  
  
./run_verif_global.sh config.vrfy.step1.chunk1  
./run_verif_global.sh config.vrfy.step1.chunk2  
./run_verif_global.sh config.vrfy.step1.chunk3  
./run_verif_global.sh config.vrfy.step1.chunk4  
./run_verif_global.sh config.vrfy.step1.chunk5  
./run_verif_global.sh config.vrfy.step1.chunk6
