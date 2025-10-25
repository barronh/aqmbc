from aqmbc.utils import driver
import argparse

prsr = argparse.ArgumentParser()
prsr.add_argument('cfgpath')
args = prsr.parse_args()
driver(args.cfgpath)
