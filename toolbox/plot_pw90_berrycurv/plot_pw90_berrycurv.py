#!/usr/bin/python3
# Author: liyang@cmt.tsinghua
# Date: 2020.09.11
# Descripution: This script is designed for plot the post-w90 berry curvature.
#

import json
import os
import sys
import argparse
import math
import numpy as np
print("[do] Loading the matplotlib.pyplot...")
import matplotlib.pyplot as plt
plt.switch_backend('agg') # For GUI less server


def check_python_version():
  """Check the python version"""
  curr_python_version = sys.version
  if curr_python_version[0] != '3':
    print('[error] Please use the python3 run this script...')
    sys.exit()
  return 0


def get_command_line_input():
  """Read in the command line parameters"""
  parser = argparse.ArgumentParser("Basic VASP band plot parameters")
  parser.add_argument('-k', '--kcoors', dest='kcoors_file', 
                      default='wannier90-kslice-coord.dat', type=str,
                      help='Point to the kpoints coordinates file.')
  parser.add_argument('-c', '--curvs', dest='curvs_file', 
                      default='wannier90-kslice-curv.dat', type=str,
                      help='Point to the Berry curvature file.')
  parser.add_argument('-f', '--format', dest='plot_format', 
                      default='pdf', type=str, choices=['png', 'eps', 'pdf'],
                      help='Plot format.')
  parser.add_argument('-d', '--min', dest='cb_min', 
                      default=-100.0, type=float,
                      help='The minimal value of the curvature plot.')
  parser.add_argument('-u', '--max', dest='cb_max', 
                      default=100.0, type=float,
                      help='The maximal value of the curvature plot.')
  parser.add_argument('-i', '--dpi', dest='plot_dpi', 
                      default=400, type=int,
                      help='Plot resolution (dpi).')
  parser.add_argument('-o', '--output', dest='plot_filename', 
                      default='berrycurv', type=str,
                      help='Output file name.')
  args = parser.parse_args()
  plot_args = {"kcoors_file"     : args.kcoors_file,
               "curvs_file"      : args.curvs_file,
               "cb_min"          : args.cb_min,
               "cb_max"          : args.cb_max,
               "plot_format"     : args.plot_format,
               "plot_dpi"        : args.plot_dpi,
               "plot_filename"   : args.plot_filename}
  return plot_args


def read_kcoors_info(plot_args):
  kcoors_file = plot_args['kcoors_file']
  kcoors = []
  str_kcoors = []
  with open(kcoors_file) as frp:
    lines = frp.readlines()
  for line in lines:
    line = line.replace('\n', '')
    line = line.split()
    if line == []:
      continue
    str_kcoors.append(line)
    kcoors.append([float(line[0]), float(line[1])])
  start_ky = str_kcoors[0][1]
  k_num = len(kcoors)
  kx_num = 0
  for kcoor in str_kcoors:
    if start_ky == kcoor[1]:
      kx_num += 1
    else:
      break
  ky_num = k_num // kx_num
  if ky_num * kx_num != k_num:
    print("[error] kx ky k number not match...")
    sys.exit(1)
  return kcoors, kx_num, ky_num


def read_curv_info(plot_args, kcoors, kx_num, ky_num):
  curvs_file = plot_args["curvs_file"]
  curvs_x = []
  curvs_y = []
  curvs_z = []
  curvs_x_block = [[0.0 for i in range(kx_num)] for j in range(ky_num)]
  curvs_y_block = [[0.0 for i in range(kx_num)] for j in range(ky_num)]
  curvs_z_block = [[0.0 for i in range(kx_num)] for j in range(ky_num)]
  with open(curvs_file) as frp:
    lines = frp.readlines()
  for line in lines:
    line = line.replace('\n', '')
    line = line.split()
    if line == []:
      continue
    curvs_x.append(float(line[0]))
    curvs_y.append(float(line[1]))
    curvs_z.append(float(line[2]))
  if (len(curvs_x) != len(kcoors)) or \
     (len(curvs_y) != len(kcoors)) or \
     (len(curvs_z) != len(kcoors)):
    print("[error] kcoors number not equal to curvs number...")
    sys.exit(1)
  for k_index in range(len(kcoors)):
    kx_index = k_index % ky_num
    ky_index = k_index // ky_num
    curvs_x_block[ky_index][kx_index] = curvs_x[k_index]
    curvs_y_block[ky_index][kx_index] = curvs_y[k_index]
    curvs_z_block[ky_index][kx_index] = curvs_z[k_index]
  curvs = [curvs_x, curvs_y, curvs_z]
  curvs_block = [curvs_x_block, curvs_y_block, curvs_z_block]
  return curvs, curvs_block


def plot_band(plot_args, curvs_block, dirc):
  """Plot the band"""
  plot_filename = plot_args['plot_filename']
  plot_dpi = plot_args['plot_dpi']
  plot_format = plot_args['plot_format']
  cb_min = plot_args["cb_min"]
  cb_max = plot_args["cb_max"]
  ky_num = len(curvs_block)
  plot_curvs_block = [[] for i in range(ky_num)]
  for i in range(ky_num):
    plot_curvs_block[i] = curvs_block[ky_num-1-i]
  # plot_curvs_block = np.array(plot_curvs_block)
  # plot_curvs_block = np.hstack((plot_curvs_block,plot_curvs_block))
  # plot_curvs_block = np.vstack((plot_curvs_block,plot_curvs_block))
  ## Design the Figure
  # Set the Fonts
  plt.rcParams.update({'font.size': 14,
                       'font.family': 'STIXGeneral',
                       'mathtext.fontset': 'stix'})
  # Set the spacing between the axis and labels
  plt.rcParams['xtick.major.pad']='6'
  plt.rcParams['ytick.major.pad']='6'
  # Set the ticks 'inside' the axis
  plt.rcParams['xtick.direction'] = 'in'
  plt.rcParams['ytick.direction'] = 'in'
  # Create the figure and axis object
  fig = plt.figure()
  band_plot = fig.add_subplot(1, 1, 1)
  # Set the label of x and y axis
  plt.xlabel(r'$k_x\;\;\to$')
  plt.xticks([])
  plt.ylabel(r'$k_y\;\;\to$')
  plt.yticks([])
  ## Plot the curvature - x
  hm = band_plot.imshow(plot_curvs_block, cmap=plt.cm.get_cmap('YlGnBu'), 
                        vmin=cb_min, vmax=cb_max)
  plt.colorbar(hm)
  # Save the figure
  plot_bc_file = plot_filename + '-' + dirc + '.' + plot_format
  plt.savefig(plot_bc_file, format=plot_format, dpi=plot_dpi)
  return 0


def main():
  """Main function"""
  check_python_version()
  plot_args = get_command_line_input()
  plot_filename = plot_args["plot_filename"]
  plot_format = plot_args["plot_format"]
  kcoors_file = plot_args["kcoors_file"]
  curvs_file = plot_args["curvs_file"]
  plot_curv_x_file = plot_filename + '-x.' + plot_format
  plot_curv_y_file = plot_filename + '-y.' + plot_format
  plot_curv_z_file = plot_filename + '-z.' + plot_format
  print("[do] Reading the k coordinates info...              <== (%s)"
        %(kcoors_file))
  kcoors, kx_num, ky_num = read_kcoors_info(plot_args)
  print("[do] Reading the total band...                      <== (%s)"
        %(curvs_file))
  _, curvs_block = read_curv_info(plot_args, kcoors, kx_num, ky_num)
  print("[do] Plotting the Berry curvature in x direction... ==> (%s)"
        %(plot_curv_x_file))
  plot_band(plot_args, curvs_block[0], 'x')
  print("[do] Plotting the Berry curvature in y direction... ==> (%s)"
        %(plot_curv_y_file))
  plot_band(plot_args, curvs_block[1], 'y')
  print("[do] Plotting the Berry curvature in z direction... ==> (%s)"
        %(plot_curv_z_file))
  plot_band(plot_args, curvs_block[2], 'z')
  return 0


if __name__ == "__main__":
  main()
