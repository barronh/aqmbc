from aqmbc._core import driver
import argparse
import json

prsr = argparse.ArgumentParser()
prsr.add_argument('cfgpath')
args = prsr.parse_args()
with open(args.cfgpath, 'r') as cfgf:
    cfg = json.load(cfgf)
driver(cfg)
