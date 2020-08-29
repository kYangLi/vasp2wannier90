# Author: liyang@cmt.tsinghua
# Date: 2020.8.2
#

import os
import sys
import getopt
import re
import matplotlib.pyplot as plt
plt.switch_backend('agg') # For GUI less server
import json

def grep(tstr, file):
  with open(file) as frp:
    lines = frp.readlines()
  targets = []
  for line in lines:
    if tstr in line:
      line = line.replace('\n','')
      targets.append(line)
  return targets

def main(argv):
  # +----------------------+
  # | Command Line Options |
  # +----------------------+
  min_plot_energy = -6
  max_plot_energy = 6
  plot_format = 'png'
  plot_dpi = 400
  plot_filename = 'band'
  try:
    opts, args = getopt.getopt(argv, "hd:u:f:r:n:",
                               ["min=", "max=", "format=", 
                               "dpi=","name="])
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
    elif opt in ("-n", "--name"):
      plot_filename = arg

  # +-------------------+
  # | Band Data Read In |
  # +-------------------+
  ## Check the existance of the Band Data
  if not os.path.isfile('BAND.dat'):
    print("[error] BAND.dat not found..")
    sys.exit(1)
  if not os.path.isfile('KLABELS'):
    print("[error] KLABELS not found...")
    sys.exit(1)
  ## Spin Number
  spin_res = grep('Spin-Down', 'BAND.dat')
  if spin_res == []:
    spin_num = 1
  else:
    spin_num = 2
  ## K Path Coor. & K Path Symbol
  hsk_symbol_list = []
  hsk_corrdinate_list = []
  with open('KLABELS') as frp:
    lines = frp.readlines()
  for line in lines:
    valid_line = re.compile('[0-9]+.[0-9]+').findall(line)
    if valid_line == []:
      continue
    line = line.replace('\n','')
    line = line.replace('GAMMA',u"\u0393") 
    line = line.replace('Gamma',u"\u0393")
    line = line.replace('gamma',u"\u0393")
    line = line.replace('G',u"\u0393")
    line = line.replace('g',u"\u0393")
    hsk_line = line.split()
    hsk_symbol_list.append(hsk_line[0])
    hsk_corrdinate_list.append(float(hsk_line[1]))
  ## Band Quantity & Band Data
  with open("BAND.dat") as frp:
    lines = frp.readlines()
  # Band quantity
  for line in lines:
    if '# Band-Index' in line:
      line = line.replace('\n', '')
      band_quantity = int(line.split()[2])
  # Kpoints quantity
  curr_line_index = 0
  kpoints_quantity = 0
  kpoints_index_list = []
  for line in lines:
    curr_line_index += 1
    if '# Band-Index' in line:
      kpoints_index_list.append(curr_line_index)
      if len(kpoints_index_list) >= 2:
        break
    res = re.compile('[0-9]+.[0-9]+').findall(line)
    if ('#' not in line) and (res != []):
        kpoints_quantity += 1
  k_start_line = kpoints_index_list[0] + 1
  k_end_line = k_start_line + kpoints_quantity - 1
  # Kline coors.
  kline_coors = [0 for i in range(kpoints_quantity)]
  for index in range(k_start_line, k_end_line + 1):
    line = lines[index-1]
    k_index = index - k_start_line
    kline_coors[k_index] = float(line.split()[0])
  # Band data
  if spin_num == 1:
    band_energys = \
      [[0 for i in range(kpoints_quantity)] for j in range(band_quantity)]
  elif spin_num == 2:
    spin_up_band_energys = \
      [[0 for i in range(kpoints_quantity)] for j in range(band_quantity)]
    spin_dn_band_energys = \
      [[0 for i in range(kpoints_quantity)] for j in range(band_quantity)]
  energy_index = 0
  for line in lines:
    if ('#' in line) or (line.replace('\n','').replace(' ','') == ''):
      continue
    line = line.replace('\n','')
    band_data_line = line.split()
    band_index = energy_index // kpoints_quantity
    kpoint_index = energy_index % kpoints_quantity
    if band_index % 2 == 1:
      kpoint_index = kpoints_quantity - kpoint_index - 1
    if spin_num == 1:
      energy = float(band_data_line[1])
      band_energys[band_index][kpoint_index] = energy
    elif spin_num == 2:
      spin_up_energy = float(band_data_line[1])
      spin_dn_energy = float(band_data_line[2])
      spin_up_band_energys[band_index][kpoint_index] = spin_up_energy
      spin_dn_band_energys[band_index][kpoint_index] = spin_dn_energy
    energy_index += 1

  # +-----------+
  # | Band Json |
  # +-----------+
  data = {}
  data["spin_num"] = spin_num
  data["plot_energy_window"] = [min_plot_energy, max_plot_energy]
  data["hsk_symbol_list"] = hsk_symbol_list
  data["hsk_corrdinate_list"] = hsk_corrdinate_list
  data["kline_coors"] = kline_coors
  if spin_num == 1:
    data["energys"] = band_energys
  if spin_num == 2:
    data["energys"] = {
      "up" : spin_up_band_energys,
      "dn" : spin_dn_band_energys
    }
  json_file = plot_filename + '.json'
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
    for band in band_energys:
        x = kline_coors
        y = band
        band_plot.plot(x, y, 'r-', linewidth=1.2)
  elif spin_num == 2:
    for band in spin_up_band_energys:
      x = kline_coors
      y = band
      band_plot.plot(x, y, 'r-', linewidth=1.4)
    for band in spin_dn_band_energys:
      x = kline_coors
      y = band
      band_plot.plot(x, y, '-', color='blue', linewidth=1.0)
  # Save the figure
  plot_band_file_name = plot_filename + '.' + plot_format
  plt.savefig(plot_band_file_name, format=plot_format, dpi=plot_dpi)
  
if __name__ == "__main__":
  main(sys.argv[1:])
