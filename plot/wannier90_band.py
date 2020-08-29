# Author: liyang@cmt.tsinghua
# Date: 2020.8.2
#

import json
import os
import sys
import getopt
import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
plt.switch_backend('agg') # For GUI less server


def grep(tstr, file):
  with open(file) as frp:
    lines = frp.readlines()
  targets = []
  for line in lines:
    if tstr in line:
      line = line.replace('\n','')
      targets.append(line)
  return targets

def get_band_diff(vasp_band, w90_band, min_plot_energy, max_plot_energy):
  vasp_energy_list = []
  w90_energy_list = []
  for band_index in range(len(w90_band)):
    for k_index in range(len(w90_band[0])):
      energy = w90_band[band_index][k_index]
      w90_energy_list.append(energy)
  w90_energy_list.sort()
  for band_index in range(len(vasp_band)):
    for k_index in range(len(vasp_band[0])):
      energy = vasp_band[band_index][k_index]
      if (energy > min_plot_energy) and (energy < max_plot_energy) and \
         (energy > w90_energy_list[0]) and (energy < w90_energy_list[-1]):
        vasp_energy_list.append(energy)
  vasp_energy_list.sort()
  try_time = len(w90_energy_list) - len(vasp_energy_list) + 1
  min_band_diff = 99999999999.00
  for try_index in range(try_time):
    curr_band_diff = 0.0
    for vasp_index in range(len(vasp_energy_list)):
      curr_band_diff += \
        (vasp_energy_list[vasp_index] - \
         w90_energy_list[vasp_index + try_index]) ** 2
    curr_band_diff = curr_band_diff ** 0.5
  if curr_band_diff < min_band_diff:
    min_band_diff = curr_band_diff
  return min_band_diff

def read_wannier90_band(w90_band_dat_file, fermi_energy):
  w90_kline_coors = []
  w90_band_energys = []
  with open(w90_band_dat_file) as frp:
    w90_band_dat = frp.readlines()
  # Get the kline
  for line in w90_band_dat:
    line = line.replace('\n', '')
    if line.replace(' ', '') == '':
      break
    w90_kline_coors.append(float(line.split()[0]))
  # Get the bands
  curr_band_index = 0
  w90_band_energys.append([])
  for line in w90_band_dat:
    line = line.replace('\n', '')
    if line.replace(' ', '') == '':
      curr_band_index += 1
      w90_band_energys.append([])
      continue
    energy = float(line.split()[1]) - fermi_energy
    w90_band_energys[curr_band_index].append(energy)
  w90_band_energys = list(filter(None, w90_band_energys))
  return w90_kline_coors, w90_band_energys


def intetpl_vasp_band(vasp_band_energys, vasp_kline_coors, w90_kline_coors):
  new_vasp_band_energys = []
  for vasp_band in vasp_band_energys:
    linear_interpld = interpolate.interp1d(vasp_kline_coors, vasp_band)
    new_vasp_band = linear_interpld(w90_kline_coors)
    new_vasp_band_energys.append(new_vasp_band)
  return new_vasp_band_energys


def main(argv):
  # +----------------------+
  # | Command Line Options |
  # +----------------------+
  min_plot_energy = -6
  max_plot_energy = 6
  plot_format = 'png'
  plot_dpi = 400
  plot_tag = 'w90'
  plot_benchmark = 'vasp.json'
  fermi_energy = 0.0
  try:
    opts, args = getopt.getopt(argv, "hd:u:f:r:t:b:e:",
                               ["min=", "max=", "format=",
                                "dpi=", "tag=", "benchmark=", "fermi="])
  except getopt.GetoptError:
    print('band_plot.py -n <filename> -d <E_min> -u <E_max> -f <PlotFormat>')
    sys.exit(2)
  del args
  for opt, arg in opts:
    if opt == '-h':
      print('band_plot.py -n <filename> -d <E_min> -u <E_max> -f <PlotFormat>')
      sys.exit()
    elif opt in ("-d", "--min"):
      min_plot_energy = float(arg)
    elif opt in ("-u", "--max"):
      max_plot_energy = float(arg)
    elif opt in ("-f", "--format"):
      plot_format = arg
    elif opt in ("-r", "--dpi"):
      plot_dpi = int(arg.split(".")[0])
    elif opt in ("-t", "--tag"):
      plot_tag = arg
    elif opt in ("-b", "--benchmark"):
      plot_benchmark = arg
    elif opt in ("-e", "--fermi"):
      fermi_energy = float(arg)

  # +-------------------+
  # | Band Data Read In |
  # +-------------------+
  ## Read in the vasp band data
  with open(plot_benchmark) as jfrp:
    vasp_band = json.load(jfrp)
  ## Spin number
  spin_num = vasp_band["spin_num"]
  ## Check the existance of the Band Data
  if (spin_num == 2 and os.path.isfile('wannier90.up_band.dat') and \
      os.path.isfile('wannier90.dn_band.dat')) or \
     (spin_num == 1 and os.path.isfile('wannier90_band.dat')):
    pass
  else:
    print("[error] spin number and band data not match...")
    sys.exit(1)
  ## Energy window
  min_plot_energy = vasp_band['plot_energy_window'][0]
  max_plot_energy = vasp_band['plot_energy_window'][1]
  ## K Path Coor. & K Path Symbol
  hsk_symbol_list = vasp_band['hsk_symbol_list']
  hsk_corrdinate_list = vasp_band['hsk_corrdinate_list']
  ## VASP kline
  vasp_kline_coors = vasp_band['kline_coors']
  ## VASP band
  if spin_num == 1:
    vasp_band_energys = vasp_band['energys']
  else:
    vasp_up_band_energys = vasp_band['energys']['up']
    vasp_dn_band_energys = vasp_band['energys']['dn']
  ## Wannier90 band
  if spin_num == 1:
    w90_kline_coors, w90_band_energys = \
      read_wannier90_band('wannier90_band.dat', fermi_energy)
  else:
    w90_kline_coors, w90_up_band_energys = \
      read_wannier90_band('wannier90.up_band.dat', fermi_energy)
    _, w90_dn_band_energys = \
      read_wannier90_band('wannier90.dn_band.dat', fermi_energy)

  # +--------------+
  # | Band Compare |
  # +--------------+
  band_diff_dict = {'cbd': 999999999999999.00}
  with open('current_band_diff.json', 'w') as jfwp:
    json.dump(band_diff_dict, jfwp)
  # Get band diff
  if spin_num == 1:
    new_vasp_band_energys = \
      intetpl_vasp_band(vasp_band_energys, vasp_kline_coors, w90_kline_coors)
    band_diff = get_band_diff(new_vasp_band_energys, w90_band_energys,
                              min_plot_energy, max_plot_energy)
  else:
    new_vasp_up_band_energys = \
      intetpl_vasp_band(vasp_up_band_energys, vasp_kline_coors, w90_kline_coors)
    new_vasp_dn_band_energys = \
      intetpl_vasp_band(vasp_dn_band_energys, vasp_kline_coors, w90_kline_coors)
    up_band_diff = get_band_diff(new_vasp_up_band_energys, w90_up_band_energys,
                                 min_plot_energy, max_plot_energy)
    dn_band_diff = get_band_diff(new_vasp_dn_band_energys, w90_dn_band_energys,
                                 min_plot_energy, max_plot_energy)
    band_diff = (up_band_diff + dn_band_diff) * 0.5
  band_diff_dict = {'cbd': band_diff}
  with open('current_band_diff.json', 'w') as jfwp:
    json.dump(band_diff_dict, jfwp)

  # +-----------+
  # | Band Json |
  # +-----------+
  data = {}
  data["spin_num"] = spin_num
  data["plot_energy_window"] = [min_plot_energy, max_plot_energy]
  data["hsk_symbol_list"] = hsk_symbol_list
  data["hsk_corrdinate_list"] = hsk_corrdinate_list
  data["kline_coors"] = w90_kline_coors
  if spin_num == 1:
    data["energys"] = w90_band_energys
  if spin_num == 2:
    data["energys"] = {
      "up" : w90_up_band_energys,
      "dn" : w90_dn_band_energys
    }
  json_file ='band_' + plot_tag + '.json'
  with open(json_file, 'w') as jfwp:
    json.dump(data, jfwp)

  # +-----------+
  # | Band Plot |
  # +-----------+
  ## Design the Figure
  # Set the Fonts
  plt.rcParams.update({'font.size': 12,
                      'font.family': 'STIXGeneral',
                      'mathtext.fontset': 'stix'})
  # Set the spacing between the axis and labels
  plt.rcParams['xtick.major.pad']='5'
  plt.rcParams['ytick.major.pad']='5'
  # Set the ticks 'inside' the axis
  plt.rcParams['xtick.direction'] = 'in'
  plt.rcParams['ytick.direction'] = 'in'
  # Create the figure and axis object
  fig = plt.figure()
  band_plot = fig.add_subplot(1, 1, 1)
  # Set the range of plot
  x_min = 0.0
  x_max = hsk_corrdinate_list[-1]
  y_min = min_plot_energy
  y_max = max_plot_energy
  plt.xlim(x_min, x_max)
  plt.ylim(y_min, y_max)
  # Set the label of x and y axis
  plt.xlabel('')
  plt.ylabel('Energy (eV)')
  # Set the Ticks of x and y axis
  plt.xticks(hsk_corrdinate_list)
  band_plot.set_xticklabels(hsk_symbol_list)
  # Plot the solid lines for High symmetic k-points
  for hsk_corrdinate in hsk_corrdinate_list:
    plt.vlines(hsk_corrdinate, y_min, y_max, 
               colors="black", linewidth=0.7, zorder=3)
  # Plot the fermi energy surface with a dashed line
  plt.hlines(0.0, x_min, x_max, colors="black",
             linestyles="dashed", linewidth=0.7, zorder=3)
  # Grid 
  plt.grid(linestyle='--', axis="y", linewidth=0.5)
  # Plot the Band Structure
  if spin_num == 1:
    for band in w90_band_energys:
      x = w90_kline_coors
      y = band
      band_plot.plot(x, y, '.', color='red', linewidth=1.2)
    for band in vasp_band_energys:
      x = vasp_kline_coors
      y = band
      band_plot.plot(x, y, '-', color='black', linewidth=1.0)
  elif spin_num == 2:
    for band in w90_up_band_energys:
      x = w90_kline_coors
      y = band
      band_plot.plot(x, y, '.', color='red', linewidth=1.2)
    for band in w90_dn_band_energys:
      x = w90_kline_coors
      y = band
      band_plot.plot(x, y, '.', color='blue', linewidth=1.2)
    for band in vasp_up_band_energys:
      x = vasp_kline_coors
      y = band
      band_plot.plot(x, y, '-', color='#959cab', linewidth=1.0)
    for band in vasp_dn_band_energys:
      x = vasp_kline_coors
      y = band
      band_plot.plot(x, y, '-', color='black', linewidth=1.0)
  # Save the figure
  plot_band_file_name = 'band_' + plot_tag + '.' + plot_format
  plt.savefig(plot_band_file_name, format=plot_format, dpi=plot_dpi)
  
if __name__ == "__main__":
  main(sys.argv[1:])
