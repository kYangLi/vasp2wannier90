# Author: liyang@cmt.tsinghua
# Date: 2020.8.2
#

import json
import os
import sys
import argparse
from scipy import interpolate
import matplotlib.pyplot as plt
plt.switch_backend('agg') # For GUI less server


def get_command_line_input():
  """Read in the command line parameters"""
  parser = argparse.ArgumentParser("Basic wannier90 band plot parameters")
  parser.add_argument('-d', '--ymin', dest='min_plot_energy',
                      default=-3, type=float,
                      help='Minimal plot energy windows.')
  parser.add_argument('-u', '--ymax', dest='max_plot_energy',
                      default=3, type=float,
                      help='Maximal plot energy windows.')
  parser.add_argument('-f', '--format', dest='plot_format',
                      default='pdf', type=str, choices=['png', 'eps', 'pdf'],
                      help='Plot format.')
  parser.add_argument('-i', '--dpi', dest='plot_dpi',
                      default=400, type=int,
                      help='Plot resolution (dpi).')
  parser.add_argument('-s', '--point-size', dest='plot_point_size',
                      default=1.0, type=float,
                      help='Point size of the wannier band plot.')
  parser.add_argument('-t', '--tag', dest='plot_tag',
                      default='w90.replot', type=str,
                      help='Output file tag name.')
  parser.add_argument('-b', '--benchmark', dest='plot_benchmark',
                      default='vasp_band.json', type=str,
                      help='The benchmark vasp band json file.')
  parser.add_argument('-x', '--no-plot', dest='no_plot', action='store_const',
                      const=True, default=False,
                      help='Do not plot the band.')
  args = parser.parse_args()
  plot_args = {"min_plot_energy" : args.min_plot_energy,
               "max_plot_energy" : args.max_plot_energy,
               "plot_format"     : args.plot_format,
               "plot_dpi"        : args.plot_dpi,
               "plot_point_size" : args.plot_point_size,
               "plot_tag"        : args.plot_tag,
               "plot_benchmark"  : args.plot_benchmark,
               "no_plot"         : args.no_plot}
  return plot_args


def read_wannier90_band(w90_band_dat_file):
  """Read in the wanneri bands"""
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
    energy = float(line.split()[1])
    w90_band_energys[curr_band_index].append(energy)
  w90_band_energys = list(filter(None, w90_band_energys))
  return w90_kline_coors, w90_band_energys


def intetpl_vasp_band(vasp_band_energys, vasp_kline_coors, w90_kline_coors):
  """intetpl_vasp_band"""
  inp_vasp_band_energys = []
  for vasp_band in vasp_band_energys:
    linear_interpld = interpolate.interp1d(vasp_kline_coors, vasp_band)
    inp_vasp_band = linear_interpld(w90_kline_coors)
    inp_vasp_band_energys.append(list(inp_vasp_band))
  return inp_vasp_band_energys


def get_band_diff(vasp_band, w90_band, min_plot_energy, max_plot_energy):
  """get_band_diff"""
  w90_band_num = len(w90_band)
  vasp_band_num = len(vasp_band)
  kp_num = len(w90_band[0])
  w90_band_aver = [sum(band)/len(band) for band in w90_band]
  vasp_band_aver = [sum(band)/len(band) for band in vasp_band]
  min_match_diff = 9999999999999999.0
  for i_sf in range(vasp_band_num-w90_band_num+1):
    match_diff = 0
    for i_w90 in range(w90_band_num):
      match_diff += (w90_band_aver[i_w90]-vasp_band_aver[i_w90+i_sf])**2
    if match_diff < min_match_diff:
      min_match_diff = match_diff
      match_sf = i_sf
  # Cut the vasp band
  vasp_band_com = vasp_band[match_sf:match_sf+w90_band_num]
  # Calculate the band difference
  band_diff = 0
  for band_i in range(w90_band_num):
    for kp_i in range(kp_num):
      w90_energy = w90_band[band_i][kp_i]
      vasp_energy = vasp_band_com[band_i][kp_i]
      if max_plot_energy > vasp_energy > min_plot_energy:
        band_diff += (w90_energy-vasp_energy)**2
  band_diff = (band_diff / (w90_band_num*kp_num)) ** 0.5
  return band_diff, match_sf


def read_all_band(plot_args):
  """read all band data"""
  ## Read in the vasp band data
  with open(plot_args["plot_benchmark"]) as jfrp:
    vasp_band = json.load(jfrp)
  ## Spin number
  spin_num = vasp_band["spin_num"]
  ## Check the existance of the Band Data
  if (spin_num == 2 and os.path.isfile('wannier90.up_band.f0.dat') and \
      os.path.isfile('wannier90.dn_band.f0.dat')) or \
     (spin_num == 1 and os.path.isfile('wannier90_band.f0.dat')):
    pass
  else:
    print("[error] spin number and band data not match...")
    sys.exit(1)
  ## K Path Coor. & K Path Symbol
  hsk_symbol_list = vasp_band['hsk_symbol_list']
  hsk_corrdinate_list = vasp_band['hsk_corrdinate_list']
  ## Read in bands and klines for vasp and wannier90
  vasp_kline_coors = vasp_band['kline_coors']
  if spin_num == 1:
    vasp_band_energys = vasp_band['energys']
    w90_kline_coors, w90_band_energys = \
      read_wannier90_band('wannier90_band.f0.dat')
    vasp_band_energys = [vasp_band_energys, None]
    w90_band_energys = [w90_band_energys, None]
  else:
    vasp_up_band_energys = vasp_band['energys']['up']
    vasp_dn_band_energys = vasp_band['energys']['dn']
    w90_kline_coors, w90_up_band_energys = \
      read_wannier90_band('wannier90.up_band.f0.dat')
    _, w90_dn_band_energys = \
      read_wannier90_band('wannier90.dn_band.f0.dat')
    vasp_band_energys = [vasp_up_band_energys, vasp_dn_band_energys]
    w90_band_energys = [w90_up_band_energys, w90_dn_band_energys]
  band_data = {"min_plot_energy"     : plot_args["min_plot_energy"],
               "max_plot_energy"     : plot_args["max_plot_energy"],
               "spin_num"            : spin_num,
               "hsk_symbol_list"     : hsk_symbol_list,
               "hsk_corrdinate_list" : hsk_corrdinate_list,
               "vasp_kline_coors"    : vasp_kline_coors,
               "w90_kline_coors"     : w90_kline_coors,
               "vasp_band_energys"   : vasp_band_energys,
               "w90_band_energys"    : w90_band_energys,
               "vasp_kp_num"         : len(vasp_kline_coors),
               "w90_kp_num"          : len(w90_kline_coors),
               "vasp_band_num"       : len(vasp_band_energys[0]),
               "w90_band_num"        : len(w90_band_energys[0])}
  return band_data


def band_compare(band_data):
  """compare bands"""
  min_plot_energy = band_data["min_plot_energy"]
  max_plot_energy = band_data["max_plot_energy"]
  vasp_kline_coors = band_data["vasp_kline_coors"]
  w90_kline_coors = band_data["w90_kline_coors"]
  vasp_band_energys = band_data["vasp_band_energys"]
  w90_band_energys = band_data["w90_band_energys"]
  band_diff_dict = {'cbd': 999999999999999.00}
  with open('current_band_diff.json', 'w') as jfwp:
    json.dump(band_diff_dict, jfwp)
  # Get band diff
  if band_data["spin_num"] == 1:
    inp_vasp_band_energys = intetpl_vasp_band(vasp_band_energys[0],
                                              vasp_kline_coors,
                                              w90_kline_coors)
    band_diff, match_sf = \
      get_band_diff(inp_vasp_band_energys, w90_band_energys[0],
                    min_plot_energy, max_plot_energy)
    inp_vasp_band_energys = [inp_vasp_band_energys, None]
  else:
    inp_vasp_up_band_energys = \
      intetpl_vasp_band(vasp_band_energys[0], vasp_kline_coors, w90_kline_coors)
    inp_vasp_dn_band_energys = \
      intetpl_vasp_band(vasp_band_energys[1], vasp_kline_coors, w90_kline_coors)
    up_band_diff, match_sf = \
      get_band_diff(inp_vasp_up_band_energys, w90_band_energys[0],
                    min_plot_energy, max_plot_energy)
    dn_band_diff, _ = \
      get_band_diff(inp_vasp_dn_band_energys, w90_band_energys[1],
                    min_plot_energy, max_plot_energy)
    band_diff = ((up_band_diff**2 + dn_band_diff**2) * 0.5) ** 0.5
    inp_vasp_band_energys = [inp_vasp_up_band_energys, inp_vasp_dn_band_energys]
  band_data["inp_vasp_band_energys"] = inp_vasp_band_energys
  band_data["band_diff"] = band_diff
  band_data["match_index"] = match_sf
  band_diff_dict = {'cbd': band_diff}
  with open('current_band_diff.json', 'w') as jfwp:
    json.dump(band_diff_dict, jfwp)
  return band_data


def record_band_json_txt(plot_args, band_data):
  plot_tag = plot_args["plot_tag"]
  json_file = 'band_' + plot_tag + '.json'
  with open(json_file, 'w') as jfwp:
    json.dump(band_data, jfwp)
  # Text file
  txt_file = 'band_' + plot_tag + '.txt'
  txt_data = ['# HSK Symbol       : %s\n' %band_data["hsk_symbol_list"],
              '# HSK Coords       : %s\n' %band_data["hsk_corrdinate_list"],
              '# Spin Number      : %d\n' %band_data["spin_num"],
              '# Plot Window      : [%f, %f]\n' %(band_data["min_plot_energy"],
                                                  band_data["max_plot_energy"]),
              '# Band Diff.       : %f\n' %band_data["band_diff"],
              '# VASP Match Index : %d\n' %(band_data["match_index"]+1),
              '# VASP Kpoints Num : %d\n' %band_data["vasp_kp_num"],
              '# VASP Bands Num   : %d\n' %band_data["vasp_band_num"],
              '# W90 Kpoints Num  : %d\n' %band_data["w90_kp_num"],
              '# W90 Bands Num    : %d\n' %band_data["w90_band_num"],
              '\n']
  for band_index in range(band_data["w90_band_num"]):
    txt_data.append('\n')
    txt_data.append('#Band-%d\n' %(band_index+1))
    if band_data["spin_num"] == 2:
      txt_data.append('#K-coors        VASP-spin-up(eV)  VASP-spin-dn(eV)  W90-spin-up(eV)  W90-spin-dn(eV)\n')
    else:
      txt_data.append('#K-coors        VASP(eV)          Wannier90(eV)\n')
    for kp_index in range(band_data["w90_kp_num"]):
      vbi = band_index + band_data["match_index"]
      if band_data["spin_num"] == 2:
        kp = band_data['w90_kline_coors'][kp_index]
        vasp_up_energy = \
          band_data['inp_vasp_band_energys'][0][vbi][kp_index]
        w90_up_energy = band_data['w90_band_energys'][0][band_index][kp_index]
        vasp_dn_energy = \
          band_data['inp_vasp_band_energys'][1][vbi][kp_index]
        w90_dn_energy = band_data['w90_band_energys'][1][band_index][kp_index]
        txt_data.append(' %.6f      %3.10f    %3.10f    %3.10f    %3.10f\n'
                        %(kp, vasp_up_energy, vasp_dn_energy,
                          w90_up_energy, w90_dn_energy))
      else:
        kp = band_data['w90_kline_coors'][kp_index]
        vasp_energy = \
          band_data['inp_vasp_band_energys'][0][vbi][kp_index]
        w90_energy = band_data['w90_band_energys'][0][band_index][kp_index]
        txt_data.append(' %.6f      %3.10f    %3.10f\n' %(kp, vasp_energy,
                                                          w90_energy))
  with open(txt_file, 'w') as fwp:
    fwp.writelines(txt_data)
  return 0


def plot_compare_band(plot_args, band_data):
  min_plot_energy = plot_args["min_plot_energy"]
  max_plot_energy = plot_args["max_plot_energy"]
  points_size = plot_args["plot_point_size"]
  plot_format = plot_args["plot_format"]
  plot_dpi = plot_args["plot_dpi"]
  plot_tag = plot_args["plot_tag"]
  hsk_corrdinate_list = band_data["hsk_corrdinate_list"]
  hsk_symbol_list = band_data["hsk_symbol_list"]
  spin_num = band_data["spin_num"]
  vasp_kline_coors = band_data['vasp_kline_coors']
  w90_kline_coors = band_data['w90_kline_coors']
  vasp_band_energys = band_data["vasp_band_energys"]
  w90_band_energys = band_data['w90_band_energys']
  ## Design the Figure
  # Set the Fonts
  plt.rcParams.update({'font.size': 12,
                       'font.family': 'STIXGeneral',
                       'mathtext.fontset': 'stix'})
  # Set the spacing between the axis and labels
  plt.rcParams['xtick.major.pad'] = '5'
  plt.rcParams['ytick.major.pad'] = '5'
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
    for band in w90_band_energys[0]:
      x = w90_kline_coors
      y = band
      band_plot.plot(x, y, '.', color='red', markersize=6*points_size)
    for band in vasp_band_energys[0]:
      x = vasp_kline_coors
      y = band
      band_plot.plot(x, y, '-', color='black', linewidth=0.9)
  elif spin_num == 2:
    for band in w90_band_energys[0]:
      x = w90_kline_coors
      y = band
      band_plot.plot(x, y, '.', color='red', markersize=6*points_size)
    for band in w90_band_energys[1]:
      x = w90_kline_coors
      y = band
      band_plot.plot(x, y, '.', color='blue', markersize=6*points_size)
    for band in vasp_band_energys[0]:
      x = vasp_kline_coors
      y = band
      band_plot.plot(x, y, '-', color='#959cab', linewidth=0.9)
    for band in vasp_band_energys[1]:
      x = vasp_kline_coors
      y = band
      band_plot.plot(x, y, '-', color='black', linewidth=0.9)
  # Save the figure
  plot_band_file_name = 'band_' + plot_tag + '.' + plot_format
  plt.savefig(plot_band_file_name, format=plot_format, dpi=plot_dpi)


def main():
  """main function"""
  plot_args = get_command_line_input()
  print("[do] Reading band data...")
  band_data = read_all_band(plot_args)
  print("[do] Comparing band data...")
  band_data = band_compare(band_data)
  print("[do] Recording band data...")
  record_band_json_txt(plot_args, band_data)
  if not plot_args["no_plot"]:
    print("[do] Plotting band data...")
    plot_compare_band(plot_args, band_data)
  print("[done]")

if __name__ == "__main__":
  main()
