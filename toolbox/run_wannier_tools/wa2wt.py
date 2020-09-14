'''wanniertools run'''
import json
import os
import sys


def grep(tstr, file):
  with open(file) as frp:
    lines = frp.readlines()
  targets = []
  for line in lines:
    if tstr in line:
      line = line.replace('\n','')
      targets.append(line)
  return targets


def read_filename():
  v2w_ap_file = 'v2w.allpara.json'
  if not os.path.isfile(v2w_ap_file):
    print("[error] No %s was found..." %v2w_ap_file)
    sys.exit(1)
  with open(v2w_ap_file) as jfrp:
    v2w_allpara = json.load(jfrp)
  return v2w_allpara['filename']


def read_spin_num(filename):
  wnr_folder = filename['band_folder']
  outcar_path = os.path.join(wnr_folder, 'OUTCAR')
  if not os.path.isfile(outcar_path):
    print("[error] No SSC OUTCAR was found..")
    sys.exit(1)
  spin_num = grep('ISPIN', '%s'%(outcar_path))
  spin_num = int(spin_num[-1].split()[2])
  return spin_num


def main():
  filename = read_filename()
  spin_num = read_spin_num(filename)
  if spin_num == 1:
    pass
  else:
    pass
  return 0


if __name__ == "__main__":
  main()
