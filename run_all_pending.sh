#!/bin/bash
python3 run_univ_eval_gemini_cli.py 广西壮族自治区 --retry > logs/guangxi_eval.log 2>&1 &
python3 run_univ_eval_gemini_cli.py 河北省 --retry > logs/hebei_eval.log 2>&1 &
python3 run_univ_eval_gemini_cli.py 吉林省 --retry > logs/jilin_eval.log 2>&1 &
python3 run_univ_eval_gemini_cli.py 黑龙江省 --retry > logs/heilongjiang_eval.log 2>&1 &
python3 run_univ_eval_gemini_cli.py 内蒙古自治区 --retry > logs/neimenggu_eval.log 2>&1 &
