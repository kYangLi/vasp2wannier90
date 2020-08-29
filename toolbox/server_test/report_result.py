import os 
import sys
import json
print("[do] Importing matplotlib, please wait...")
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

def env_check():
  if os.path.isdir('report'):
    _ = os.system("rm -rf report")
  os.mkdir('report')
  os.chdir('report')
  os.mkdir('latex')
  os.mkdir('figure')
  os.chdir('..')
  return 0

def get_res_data_file_location(obj_dir):
  all_paras_json = os.path.join(obj_dir, "vr.allpara.json")
  with open(all_paras_json) as jfrp:
    all_paras = json.load(jfrp)
  filename = all_paras["filename"]
  calc_para_list = all_paras["calc_para"]
  nodes_quantity = calc_para_list["nodes_quantity"]
  cores_per_node = calc_para_list["cores_per_node"]
  total_cores = nodes_quantity * cores_per_node
  result_folder = filename["result_folder"]
  result_json = filename["result_json"]
  band_res_folder = filename["band_res_folder"]
  dos_res_folder = filename["dos_res_folder"]
  band_fig = filename["band_fig"]
  dos_fig = filename["dos_fig"]
  obj_res_dir = os.path.join(obj_dir, result_folder)
  obj_res_json = os.path.join(obj_res_dir, result_json)
  obj_band_dir = os.path.join(obj_res_dir, band_res_folder)
  obj_band_json = os.path.join(obj_band_dir, band_fig+'.json')
  obj_band_gap = os.path.join(obj_band_dir, 'BAND_GAP')
  obj_dos_json = os.path.join(obj_res_dir, dos_res_folder, dos_fig+'.json')
  return nodes_quantity, total_cores, obj_res_json, \
         obj_band_json, obj_band_gap, obj_dos_json

def get_bandgap_info(file):
  bandgap_info = {}
  # Get homo index
  homo_index = grep('HOMO Band', file)
  if not homo_index:
    homo_index = grep('HOMO & LUMO Bands:', file)
    homo_index = int(homo_index[0].split()[-2])
  else: 
    homo_index = int(homo_index[0].split()[-1])
  bandgap_info["homo_index"] = homo_index
  # Get band gap
  band_gap = grep('Band Gap', file)
  band_gap = float(band_gap[0].split()[-1])
  bandgap_info["band_gap"] = band_gap
  # Get VBM
  vbm = grep('Eigenvalue of VBM', file)
  vbm = float(vbm[0].split()[-1])
  bandgap_info["vbm"] = vbm
  return bandgap_info

def get_calc_objs_infos():
  # Define the collect dict
  calc_objs_infos = {}
  # Collect the infos
  calc_obj_list = os.listdir('calc')
  all_lib_pri_objs = os.listdir('lib/private')
  all_lib_pub_objs = os.listdir('lib/public')
  for obj in calc_obj_list:
    if not os.path.isdir(os.path.join('calc', obj)):
      continue
    print("[subdo] Collecting result of %s ..." %obj)
    # Check the lib dir.
    if (obj in all_lib_pri_objs) and (obj in all_lib_pub_objs):
      print("[error] Same object name in pri. and pub. list...")
      sys.exit()
    if obj in all_lib_pri_objs:
      lib_sub_dir = 'private'
    elif obj in all_lib_pub_objs:
      lib_sub_dir = 'public'
    else:
      print("[error] Calc obj do not match to any one in lib...")
      sys.exit(1)
    ## Get the result file data
    # lib
    obj_dir = os.path.join('lib', lib_sub_dir, obj)
    lib_nodes_quantity, lib_total_cores, lib_obj_res_json, \
      lib_obj_band_json, lib_obj_band_gap, lib_obj_dos_json \
      = get_res_data_file_location(obj_dir)
    # calc
    obj_dir = os.path.join('calc', obj)
    calc_nodes_quantity, calc_total_cores, calc_obj_res_json, \
      calc_obj_band_json, calc_obj_band_gap, calc_obj_dos_json \
      = get_res_data_file_location(obj_dir)
    # File check 
    if (not os.path.isfile(lib_obj_res_json)) or \
       (not os.path.isfile(lib_obj_band_json)) or \
       (not os.path.isfile(lib_obj_dos_json)) or \
       (not os.path.isfile(lib_obj_band_gap)):
      print("[warning] %s lib not complete... skip..." %obj)
      continue
    if (not os.path.isfile(calc_obj_res_json)) or \
       (not os.path.isfile(calc_obj_band_json)) or \
       (not os.path.isfile(calc_obj_dos_json)) or \
       (not os.path.isfile(calc_obj_band_gap)):
      print("[warning] %s calc not finished... skip..." %obj)
      continue
    # Get band gap file data 
    lib_bandgap_info = get_bandgap_info(lib_obj_band_gap)
    calc_bandgap_info = get_bandgap_info(calc_obj_band_gap)
    # Write the compare json data
    with open(lib_obj_res_json) as jfrp:
      lib_res = json.load(jfrp)
    with open(calc_obj_res_json) as jfrp:
      calc_res = json.load(jfrp)
    calc_objs_infos[obj] = {
      "lib"  : lib_res,
      "calc" : calc_res
    }
    calc_objs_infos[obj]["lib"]["cpus"] = {
      "nodes" : lib_nodes_quantity, 
      "cores" : lib_total_cores
    }
    calc_objs_infos[obj]["calc"]["cpus"] = {
      "nodes" : calc_nodes_quantity, 
      "cores" : calc_total_cores
    }
    calc_objs_infos[obj]["lib"]["bandgap"] = lib_bandgap_info
    calc_objs_infos[obj]["calc"]["bandgap"] = calc_bandgap_info
    calc_objs_infos[obj]["lib"]["bandplot"] = lib_obj_band_json
    calc_objs_infos[obj]["lib"]["dosplot"] = lib_obj_dos_json
    calc_objs_infos[obj]["calc"]["bandplot"] = calc_obj_band_json
    calc_objs_infos[obj]["calc"]["dosplot"] = calc_obj_dos_json
  if calc_objs_infos == {}:
    print("[error] No calc result avaliable...")
    sys.exit(1)
  return calc_objs_infos, calc_obj_list

def compare_lib_calc(calc_objs_infos, calc_obj_list):
  for obj in calc_obj_list:
    calc_objs_infos[obj]["compare"] = {}
    # CPU diff.
    lib_nodes = calc_objs_infos[obj]["lib"]["cpus"]["nodes"]
    lib_cores = calc_objs_infos[obj]["lib"]["cpus"]["cores"]
    calc_nodes = calc_objs_infos[obj]["calc"]["cpus"]["nodes"]
    calc_cores = calc_objs_infos[obj]["calc"]["cpus"]["cores"]
    calc_objs_infos[obj]["compare"]["cpus"] = {
      "nodes_diff" : lib_nodes - calc_nodes,
      "cores_diff" : lib_cores - calc_cores
    }
    # Relax, SSC, Band, DOS diff.
    calc_objs_infos[obj]["compare"]["time_diff"] = {}
    calc_objs_infos[obj]["compare"]["lsc_diff"] = {}
    calc_objs_infos[obj]["compare"]["fermi_diff"] = {}
    calc_objs_infos[obj]["compare"]["energy_diff"] = {}
    calc_objs_infos[obj]["compare"]["force_diff"] = {}
    calc_objs_infos[obj]["compare"]["mag_diff"] = {}
    for task_tag in ["relax", "ssc", "band", "dos"]:
      lib_time = calc_objs_infos[obj]["lib"]["time"][task_tag]
      lib_lcs = calc_objs_infos[obj]["lib"]["lattice_para"][task_tag]
      lib_fermi = calc_objs_infos[obj]["lib"]["fermi"][task_tag]
      lib_energy = calc_objs_infos[obj]["lib"]["energy"][task_tag]
      lib_force = calc_objs_infos[obj]["lib"]["force_per_atom"][task_tag]
      lib_mag = calc_objs_infos[obj]["lib"]["total_mag"][task_tag]
      calc_time = calc_objs_infos[obj]["calc"]["time"][task_tag]
      calc_lcs = calc_objs_infos[obj]["calc"]["lattice_para"][task_tag]
      calc_fermi = calc_objs_infos[obj]["calc"]["fermi"][task_tag]
      calc_energy = calc_objs_infos[obj]["calc"]["energy"][task_tag]
      calc_force = calc_objs_infos[obj]["calc"]["force_per_atom"][task_tag]
      calc_mag = calc_objs_infos[obj]["calc"]["total_mag"][task_tag]
      time_diff = lib_time - calc_time
      lsc_diff = [lib_lcs[i]-calc_lcs[i] for i in range(len(lib_lcs))]
      fermi_diff = lib_fermi - calc_fermi
      energy_diff = lib_energy - calc_energy
      force_diff = [lib_force[i]-calc_force[i] for i in range(len(lib_force))]
      mag_diff = lib_mag - calc_mag
      calc_objs_infos[obj]["compare"]["time_diff"][task_tag] = time_diff
      calc_objs_infos[obj]["compare"]["lsc_diff"][task_tag] = lsc_diff
      calc_objs_infos[obj]["compare"]["fermi_diff"][task_tag] = fermi_diff
      calc_objs_infos[obj]["compare"]["energy_diff"][task_tag] = energy_diff
      calc_objs_infos[obj]["compare"]["force_diff"][task_tag] = force_diff
      calc_objs_infos[obj]["compare"]["mag_diff"][task_tag] = mag_diff
    lib_total_time = calc_objs_infos[obj]["lib"]["time"]["total"]
    calc_total_time = calc_objs_infos[obj]["calc"]["time"]["total"]
    total_time_diff = lib_total_time - calc_total_time
    calc_objs_infos[obj]["compare"]["time_diff"]["total"] = total_time_diff
    # Band Gap 
    lib_bandgap_info = calc_objs_infos[obj]["lib"]["bandgap"]
    calc_bandgap_info = calc_objs_infos[obj]["calc"]["bandgap"]
    lib_homo = lib_bandgap_info["homo_index"]
    lib_gap = lib_bandgap_info["band_gap"]
    lib_vbm = lib_bandgap_info["vbm"]
    calc_homo = calc_bandgap_info["homo_index"]
    calc_gap = calc_bandgap_info["band_gap"]
    calc_vbm = calc_bandgap_info["vbm"]
    calc_objs_infos[obj]["compare"]["bandgap"] = {
      "homo_diff" : lib_homo - calc_homo,
      "gap_diff"  : lib_gap - calc_gap,
      "vbm_diff"  : lib_vbm - calc_vbm
    }
  return calc_objs_infos

def band_plot(lib_band, calc_band, obj):
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
  x_max = lib_band["hsk_corrdinate_list"][-1]
  y_min = lib_band["plot_energy_window"][0]
  y_max = lib_band["plot_energy_window"][1]
  plt.xlim(x_min, x_max)
  plt.ylim(y_min, y_max)
  # Set the label of x and y axis
  plt.xlabel('')
  plt.ylabel('Energy (eV)')
  # Set the Ticks of x and y axis
  plt.xticks(lib_band["hsk_corrdinate_list"])
  band_plot.set_xticklabels(lib_band["hsk_symbol_list"])
  # Plot the solid lines for High symmetic k-points
  for hsk_corrdinate in lib_band["hsk_corrdinate_list"]:
    plt.vlines(hsk_corrdinate, y_min, y_max, 
               colors="black", linewidth=0.7, zorder=3)
  # Plot the fermi energy surface with a dashed line
  plt.hlines(0.0, x_min, x_max, colors="black",
             linestyles="dashed", linewidth=0.7, zorder=3)
  # Grid 
  plt.grid(linestyle='--', axis="y", linewidth=0.5)
  # Plot the Band Structure
  x = lib_band["kline_coors"]
  if lib_band["spin_num"] == 1:
    for band_index in range(len(lib_band["energys"])):
      yl = lib_band["energys"][band_index]
      yc = calc_band["energys"][band_index]
      band_plot.plot(x, yl, '-', color='red', linewidth=1.2)
      band_plot.plot(x, yc, '--', color='black', linewidth=1.2)
  elif lib_band["spin_num"] == 2:
    for band_index in range(len(lib_band["energys"]["up"])):
      yl = lib_band["energys"]["up"][band_index]
      yc = calc_band["energys"]["up"][band_index]
      band_plot.plot(x, yl, '-', color='red', linewidth=1.2)
      band_plot.plot(x, yc, '--', color='black', linewidth=1.2)
    for band_index in range(len(lib_band["energys"]["dn"])):
      yl = lib_band["energys"]["dn"][band_index]
      yc = calc_band["energys"]["dn"][band_index]
      band_plot.plot(x, yl, '-', color='blue', linewidth=1.0)
      band_plot.plot(x, yc, '--', color='black',  linewidth=1.0)
  # Save the figure
  plot_format = 'png'
  plot_dpi = 300
  band_plot_file = '%s.band.%s' %(obj, plot_format)
  plt.savefig(band_plot_file, format=plot_format, dpi=plot_dpi)
  return 'report/figure/%s' %(band_plot_file)


def calc_band_diff(lib_band, calc_band):
  band_diff = 0
  if lib_band["spin_num"] == 1:
    total_energy_number = len(lib_band["energys"]) * len(lib_band["energys"][0])
    for band_index in range(len(lib_band["energys"])):
      yl = lib_band["energys"][band_index]
      yc = calc_band["energys"][band_index]
      for index in range(len(yl)):
        band_diff += (yl[index]-yc[index])**2
  elif lib_band["spin_num"] == 2:
    total_energy_number = len(lib_band["energys"]["up"]) * \
                          len(lib_band["energys"]["up"][0])
    for band_index in range(len(lib_band["energys"]["up"])):
      yl = lib_band["energys"]["up"][band_index]
      yc = calc_band["energys"]["up"][band_index]
      for index in range(len(yl)):
        band_diff += (yl[index]-yc[index])**2
    for band_index in range(len(lib_band["energys"]["dn"])):
      yl = lib_band["energys"]["dn"][band_index]
      yc = calc_band["energys"]["dn"][band_index]
      for index in range(len(yl)):
        band_diff += (yl[index]-yc[index])**2
    band_diff = band_diff / 2
  band_diff = band_diff / total_energy_number
  band_diff = band_diff ** 0.5
  return band_diff


def plot_compare_band(calc_objs_infos, calc_obj_list):
  os.chdir("report/figure")
  for obj in calc_obj_list:
    print("[subdo] Plotting %s"%obj)
    lib_band_json = calc_objs_infos[obj]["lib"]["bandplot"]
    calc_band_json = calc_objs_infos[obj]["calc"]["bandplot"]
    lib_band_json = os.path.join('..', '..', lib_band_json)
    calc_band_json = os.path.join('..', '..', calc_band_json)
    with open(lib_band_json) as jfrp:
      lib_band = json.load(jfrp)
    with open(calc_band_json) as jfrp:
      calc_band = json.load(jfrp)
    # Plot band
    band_plot_file = band_plot(lib_band, calc_band, obj)
    calc_objs_infos[obj]["compare"]["bandplot"] = band_plot_file
    # Compare band in number
    band_diff = calc_band_diff(lib_band, calc_band)
    calc_objs_infos[obj]["compare"]["band_diff"] = band_diff
  os.chdir("../..")
  return calc_objs_infos


def dos_plot(lib_dos, calc_dos, obj):
  # Set the Fonts
  plt.rcParams.update({'font.size': 14,
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
  dos_plot = fig.add_subplot(1, 1, 1)
  # Set the range of plot
  x_min = lib_dos["plot_energy_window"][0]
  x_max = lib_dos["plot_energy_window"][1]
  plt.xlim(x_min, x_max)
  # Set the label of x and y axis
  plt.xlabel('Energy (eV)')
  plt.ylabel('Total DOS (a.u.)')
  # Plot the fermi energy surface with a dashed line
  plt.hlines(0.0, x_min, x_max, colors="black",
             linestyles="-", linewidth=0.7, zorder=3)
  # Grid 
  plt.grid(linestyle='--', linewidth=0.5)
  # Plot the dos Structure
  x = lib_dos["energys"]
  if lib_dos["spin_num"] == 1:
    yl = lib_dos["doss"]
    yc = calc_dos["doss"]
    dos_plot.plot(x, yl, '-', color='red', linewidth=1.2)
    dos_plot.plot(x, yc, '--', color='black', linewidth=1.2)
  elif lib_dos["spin_num"] == 2:
    yl = lib_dos["doss"]["up"]
    yc = calc_dos["doss"]["up"]
    dos_plot.plot(x, yl, '-', color='red', linewidth=1.2)
    dos_plot.plot(x, yc, '--', color='black', linewidth=1.2)
    yl = lib_dos["doss"]["dn"]
    yc = calc_dos["doss"]["dn"]
    dos_plot.plot(x, yl, '-', color='blue', linewidth=1.2)
    dos_plot.plot(x, yc, '--', color='black', linewidth=1.2)
  # Save the figure
  plot_format = 'png'
  plot_dpi = 300
  dos_plot_file = '%s.dos.%s' %(obj, plot_format)
  plt.savefig(dos_plot_file, format=plot_format, dpi=plot_dpi)
  return 'report/figure/%s' %(dos_plot_file)


def calc_dos_diff(lib_dos, calc_dos):
  dos_diff = 0
  total_energy_number = len(lib_dos["doss"])
  if lib_dos["spin_num"] == 1:
    yl = lib_dos["doss"]
    yc = calc_dos["doss"]
    for index in range(len(yl)):
      dos_diff += (yl[index]-yc[index])**2
  elif lib_dos["spin_num"] == 2:
    yl = lib_dos["doss"]["up"]
    yc = calc_dos["doss"]["up"]
    for index in range(len(yl)):
      dos_diff += (yl[index]-yc[index])**2
    yl = lib_dos["doss"]["dn"]
    yc = calc_dos["doss"]["dn"]
    for index in range(len(yl)):
      dos_diff += (yl[index]-yc[index])**2
    dos_diff /= 2
  dos_diff /= total_energy_number
  dos_diff = dos_diff ** 0.5
  return dos_diff


def plot_compare_dos(calc_objs_infos, calc_obj_list):
  os.chdir("report/figure")
  for obj in calc_obj_list:
    lib_dos_json = calc_objs_infos[obj]["lib"]["dosplot"]
    calc_dos_json = calc_objs_infos[obj]["calc"]["dosplot"]
    lib_dos_json = os.path.join('..', '..', lib_dos_json)
    calc_dos_json = os.path.join('..', '..', calc_dos_json)
    with open(lib_dos_json) as jfrp:
      lib_dos = json.load(jfrp)
    with open(calc_dos_json) as jfrp:
      calc_dos = json.load(jfrp)
    # DOS plot 
    dos_plot_file = dos_plot(lib_dos, calc_dos, obj)
    calc_objs_infos[obj]["compare"]["dosplot"] = dos_plot_file
    # Compare dos in number
    dos_diff = calc_dos_diff(lib_dos, calc_dos)
    calc_objs_infos[obj]["compare"]["dos_diff"] = dos_diff
  os.chdir("../..")
  return calc_objs_infos


def report_with_json(calc_objs_infos):
  os.chdir("report")
  with open('report.json', 'w') as jfwp:
    json.dump(calc_objs_infos, jfwp, indent=2)
  os.chdir("..")
  return 0


def get_report_info(calc_objs_infos, obj):
  lib_cpu_nodes = calc_objs_infos[obj]["lib"]["cpus"]["nodes"]
  lib_cpu_cores = calc_objs_infos[obj]["lib"]["cpus"]["cores"]
  lib_time_relax = calc_objs_infos[obj]["lib"]["time"]["relax"]
  lib_time_ssc = calc_objs_infos[obj]["lib"]["time"]["ssc"]
  lib_time_band = calc_objs_infos[obj]["lib"]["time"]["band"]
  lib_time_dos = calc_objs_infos[obj]["lib"]["time"]["dos"]
  lib_time_total = calc_objs_infos[obj]["lib"]["time"]["total"]
  lib_latt = calc_objs_infos[obj]["lib"]["lattice_para"]["relax"]
  lib_force = calc_objs_infos[obj]["lib"]["force_per_atom"]["relax"]
  lib_fermi_relax = calc_objs_infos[obj]["lib"]["fermi"]["relax"]
  lib_fermi_ssc = calc_objs_infos[obj]["lib"]["fermi"]["ssc"]
  lib_fermi_band = calc_objs_infos[obj]["lib"]["fermi"]["band"]
  lib_fermi_dos = calc_objs_infos[obj]["lib"]["fermi"]["dos"]
  lib_energy_relax = calc_objs_infos[obj]["lib"]["energy"]["relax"]
  lib_energy_ssc = calc_objs_infos[obj]["lib"]["energy"]["ssc"]
  lib_energy_band = calc_objs_infos[obj]["lib"]["energy"]["band"]
  lib_energy_dos = calc_objs_infos[obj]["lib"]["energy"]["dos"]
  lib_band_gap = calc_objs_infos[obj]["lib"]["bandgap"]["band_gap"]
  lib_band_homo = calc_objs_infos[obj]["lib"]["bandgap"]["homo_index"]
  lib_band_vbm = calc_objs_infos[obj]["lib"]["bandgap"]["vbm"] 
  lib_mag_relax = calc_objs_infos[obj]["lib"]["total_mag"]["relax"]
  lib_mag_ssc = calc_objs_infos[obj]["lib"]["total_mag"]["ssc"]
  lib_mag_band = calc_objs_infos[obj]["lib"]["total_mag"]["band"]
  lib_mag_dos = calc_objs_infos[obj]["lib"]["total_mag"]["dos"] 
  calc_cpu_nodes = calc_objs_infos[obj]["calc"]["cpus"]["nodes"]
  calc_cpu_cores = calc_objs_infos[obj]["calc"]["cpus"]["cores"]
  calc_time_relax = calc_objs_infos[obj]["calc"]["time"]["relax"]
  calc_time_ssc = calc_objs_infos[obj]["calc"]["time"]["ssc"]
  calc_time_band = calc_objs_infos[obj]["calc"]["time"]["band"]
  calc_time_dos = calc_objs_infos[obj]["calc"]["time"]["dos"]
  calc_time_total = calc_objs_infos[obj]["calc"]["time"]["total"]
  calc_latt = calc_objs_infos[obj]["calc"]["lattice_para"]["relax"]
  calc_force = calc_objs_infos[obj]["calc"]["force_per_atom"]["relax"]
  calc_fermi_relax = calc_objs_infos[obj]["calc"]["fermi"]["relax"]
  calc_fermi_ssc = calc_objs_infos[obj]["calc"]["fermi"]["ssc"]
  calc_fermi_band = calc_objs_infos[obj]["calc"]["fermi"]["band"]
  calc_fermi_dos = calc_objs_infos[obj]["calc"]["fermi"]["dos"]
  calc_energy_relax = calc_objs_infos[obj]["calc"]["energy"]["relax"]
  calc_energy_ssc = calc_objs_infos[obj]["calc"]["energy"]["ssc"]
  calc_energy_band = calc_objs_infos[obj]["calc"]["energy"]["band"]
  calc_energy_dos = calc_objs_infos[obj]["calc"]["energy"]["dos"]
  calc_band_gap = calc_objs_infos[obj]["calc"]["bandgap"]["band_gap"]
  calc_band_homo = calc_objs_infos[obj]["calc"]["bandgap"]["homo_index"]
  calc_band_vbm = calc_objs_infos[obj]["calc"]["bandgap"]["vbm"] 
  calc_mag_relax = calc_objs_infos[obj]["calc"]["total_mag"]["relax"]
  calc_mag_ssc = calc_objs_infos[obj]["calc"]["total_mag"]["ssc"]
  calc_mag_band = calc_objs_infos[obj]["calc"]["total_mag"]["band"]
  calc_mag_dos = calc_objs_infos[obj]["calc"]["total_mag"]["dos"] 
  com_cpu_nodes = calc_objs_infos[obj]["compare"]["cpus"]["nodes_diff"]
  com_cpu_cores = calc_objs_infos[obj]["compare"]["cpus"]["cores_diff"]
  com_time_relax = calc_objs_infos[obj]["compare"]["time_diff"]["relax"]
  com_time_ssc = calc_objs_infos[obj]["compare"]["time_diff"]["ssc"]
  com_time_band = calc_objs_infos[obj]["compare"]["time_diff"]["band"]
  com_time_dos = calc_objs_infos[obj]["compare"]["time_diff"]["dos"]
  com_time_total = calc_objs_infos[obj]["compare"]["time_diff"]["total"]
  com_latt = calc_objs_infos[obj]["compare"]["lsc_diff"]["relax"]
  com_force = calc_objs_infos[obj]["compare"]["force_diff"]["relax"]
  com_fermi_relax = calc_objs_infos[obj]["compare"]["fermi_diff"]["relax"]
  com_fermi_ssc = calc_objs_infos[obj]["compare"]["fermi_diff"]["ssc"]
  com_fermi_band = calc_objs_infos[obj]["compare"]["fermi_diff"]["band"]
  com_fermi_dos = calc_objs_infos[obj]["compare"]["fermi_diff"]["dos"]
  com_energy_relax = calc_objs_infos[obj]["compare"]["energy_diff"]["relax"]
  com_energy_ssc = calc_objs_infos[obj]["compare"]["energy_diff"]["ssc"]
  com_energy_band = calc_objs_infos[obj]["compare"]["energy_diff"]["band"]
  com_energy_dos = calc_objs_infos[obj]["compare"]["energy_diff"]["dos"]
  com_band_gap = calc_objs_infos[obj]["compare"]["bandgap"]["gap_diff"]
  com_band_homo = calc_objs_infos[obj]["compare"]["bandgap"]["homo_diff"]
  com_band_vbm = calc_objs_infos[obj]["compare"]["bandgap"]["vbm_diff"]
  com_mag_relax = calc_objs_infos[obj]["compare"]["mag_diff"]["relax"]
  com_mag_ssc = calc_objs_infos[obj]["compare"]["mag_diff"]["ssc"]
  com_mag_band = calc_objs_infos[obj]["compare"]["mag_diff"]["band"]
  com_mag_dos = calc_objs_infos[obj]["compare"]["mag_diff"]["dos"]
  com_band_diff = calc_objs_infos[obj]["compare"]["band_diff"]
  com_dos_diff = calc_objs_infos[obj]["compare"]["dos_diff"]
  com_band_plot = 'report/figure/%s.band.png' %obj
  com_dos_plot = 'report/figure/%s.dos.png' %obj
  # Str
  lib_cpu_nodes = str(lib_cpu_nodes)
  lib_cpu_cores = str(lib_cpu_cores)
  lib_time_relax = str(round(lib_time_relax))
  lib_time_ssc = str(round(lib_time_ssc))
  lib_time_band = str(round(lib_time_band))
  lib_time_dos = str(round(lib_time_dos))
  lib_time_total = str(round(lib_time_total))
  lib_latt = [str(val) for val in lib_latt]
  lib_force = ['%e'%val for val in lib_force]
  lib_fermi_relax = str(lib_fermi_relax)
  lib_fermi_ssc = str(lib_fermi_ssc)
  lib_fermi_band = str(lib_fermi_band)
  lib_fermi_dos = str(lib_fermi_dos)
  lib_energy_relax = str(lib_energy_relax)
  lib_energy_ssc = str(lib_energy_ssc)
  lib_energy_band = str(lib_energy_band)
  lib_energy_dos = str(lib_energy_dos)
  lib_band_gap = str(lib_band_gap)
  lib_band_homo = str(lib_band_homo)
  lib_band_vbm = str(lib_band_vbm)
  lib_mag_relax = '%.6f'%lib_mag_relax
  lib_mag_ssc = '%.6f'%lib_mag_ssc
  lib_mag_band = '%.6f'%lib_mag_band
  lib_mag_dos = '%.6f'%lib_mag_dos
  calc_cpu_nodes = str(calc_cpu_nodes)
  calc_cpu_cores = str(calc_cpu_cores)
  calc_time_relax = str(round(calc_time_relax))
  calc_time_ssc = str(round(calc_time_ssc))
  calc_time_band = str(round(calc_time_band))
  calc_time_dos = str(round(calc_time_dos))
  calc_time_total = str(round(calc_time_total))
  calc_latt = [str(val) for val in calc_latt]
  calc_force = ['%e'%val for val in calc_force]
  calc_fermi_relax = str(calc_fermi_relax)
  calc_fermi_ssc = str(calc_fermi_ssc)
  calc_fermi_band = str(calc_fermi_band)
  calc_fermi_dos = str(calc_fermi_dos)
  calc_energy_relax = str(calc_energy_relax)
  calc_energy_ssc = str(calc_energy_ssc)
  calc_energy_band = str(calc_energy_band)
  calc_energy_dos = str(calc_energy_dos)
  calc_band_gap = str(calc_band_gap)
  calc_band_homo = str(calc_band_homo)
  calc_band_vbm = str(calc_band_vbm)
  calc_mag_relax = '%.6f'%calc_mag_relax
  calc_mag_ssc = '%.6f'%calc_mag_ssc
  calc_mag_band = '%.6f'%calc_mag_band
  calc_mag_dos = '%.6f'%calc_mag_dos
  com_cpu_nodes = str(com_cpu_nodes)
  com_cpu_cores = str(com_cpu_cores)
  com_time_relax = str(round(com_time_relax))
  com_time_ssc = str(round(com_time_ssc))
  com_time_band = str(round(com_time_band))
  com_time_dos = str(round(com_time_dos))
  com_time_total = str(round(com_time_total))
  com_latt = [str(val) for val in com_latt]
  com_force = ['%e'%val for val in com_force]
  com_fermi_relax = str(com_fermi_relax)
  com_fermi_ssc = str(com_fermi_ssc)
  com_fermi_band = str(com_fermi_band)
  com_fermi_dos = str(com_fermi_dos)
  com_energy_relax = str(com_energy_relax)
  com_energy_ssc = str(com_energy_ssc)
  com_energy_band = str(com_energy_band)
  com_energy_dos = str(com_energy_dos)
  com_band_gap = str(com_band_gap)
  com_band_homo = str(com_band_homo)
  com_band_vbm = str(com_band_vbm)
  com_mag_relax = '%.6f'%com_mag_relax
  com_mag_ssc = '%.6f'%com_mag_ssc
  com_mag_band = '%.6f'%com_mag_band
  com_mag_dos = '%.6f'%com_mag_dos
  com_band_diff = str(com_band_diff)
  com_dos_diff = str(com_dos_diff)
  return lib_cpu_nodes, lib_cpu_cores, lib_time_relax, lib_time_ssc, \
    lib_time_band, lib_time_dos, lib_time_total, lib_latt, lib_force, \
    lib_fermi_relax, lib_fermi_ssc, lib_fermi_band, lib_fermi_dos, \
    lib_energy_relax, lib_energy_ssc, lib_energy_band, lib_energy_dos, \
    lib_band_gap, lib_band_homo, lib_band_vbm, lib_mag_relax, lib_mag_ssc, \
    lib_mag_band, lib_mag_dos, calc_cpu_nodes, calc_cpu_cores, \
    calc_time_relax, calc_time_ssc, calc_time_band, calc_time_dos, \
    calc_time_total, calc_latt, calc_force, calc_fermi_relax, calc_fermi_ssc,\
    calc_fermi_band, calc_fermi_dos, calc_energy_relax, calc_energy_ssc,\
    calc_energy_band, calc_energy_dos, calc_band_gap, calc_band_homo, \
    calc_band_vbm, calc_mag_relax, calc_mag_ssc, calc_mag_band, calc_mag_dos, \
    com_cpu_nodes, com_cpu_cores, com_time_relax, com_time_ssc, com_time_band,\
    com_time_dos, com_time_total, com_latt, com_force, com_fermi_relax, \
    com_fermi_ssc, com_fermi_band, com_fermi_dos, com_energy_relax, \
    com_energy_ssc, com_energy_band, com_energy_dos, com_band_gap, \
    com_band_homo, com_band_vbm, com_mag_relax, com_mag_ssc, com_mag_band, \
    com_mag_dos, com_band_diff, com_dos_diff, com_band_plot, com_dos_plot


def report_with_txt(calc_objs_infos, calc_obj_list):
  os.chdir("report")
  obj_index = 0
  report_txt = [
  '                                                                    ',
  '                           - VASPRUN SERVER TEST -                  ',
  '                                                                    ',
  ]
  for obj in calc_obj_list:
    lib_cpu_nodes, lib_cpu_cores, lib_time_relax, lib_time_ssc, lib_time_band, \
    lib_time_dos, lib_time_total, lib_latt, lib_force, lib_fermi_relax, \
    lib_fermi_ssc, lib_fermi_band, lib_fermi_dos, lib_energy_relax, \
    lib_energy_ssc, lib_energy_band, lib_energy_dos, lib_band_gap, \
    lib_band_homo, lib_band_vbm, lib_mag_relax, lib_mag_ssc, lib_mag_band, \
    lib_mag_dos, calc_cpu_nodes, calc_cpu_cores, calc_time_relax, \
    calc_time_ssc, calc_time_band, calc_time_dos, calc_time_total, calc_latt, \
    calc_force, calc_fermi_relax, calc_fermi_ssc, calc_fermi_band, \
    calc_fermi_dos, calc_energy_relax, calc_energy_ssc, calc_energy_band, \
    calc_energy_dos, calc_band_gap, calc_band_homo, calc_band_vbm, \
    calc_mag_relax, calc_mag_ssc, calc_mag_band, calc_mag_dos, com_cpu_nodes, \
    com_cpu_cores, com_time_relax, com_time_ssc, com_time_band, com_time_dos, \
    com_time_total, com_latt, com_force, com_fermi_relax, com_fermi_ssc, \
    com_fermi_band, com_fermi_dos, com_energy_relax, com_energy_ssc, \
    com_energy_band, com_energy_dos, com_band_gap, com_band_homo, \
    com_band_vbm, com_mag_relax, com_mag_ssc, com_mag_band, com_mag_dos, \
    com_band_diff, com_dos_diff, com_band_plot, com_dos_plot \
      = get_report_info(calc_objs_infos, obj)
    obj_index += 1
    curr_obj_report_txt = [
    '[Object %d] %s' %(obj_index, obj),
    '==============================================================================',
    ' Items.          ||     benchmark     |   current vasp    |       diff.       ',
    '-----------------++-------------------+-------------------+-------------------',
    ' CPUs    | Nodes || %17s | %17s | %17s '%(lib_cpu_nodes, calc_cpu_nodes, com_cpu_nodes),
    '         | Cores || %17s | %17s | %17s '%(lib_cpu_cores, calc_cpu_cores, com_cpu_cores),
    '-----------------++-------------------+-------------------+-------------------',
    ' Time    | Relax || %17s | %17s | %17s '%(lib_time_relax, calc_time_relax, com_time_relax),
    '  (s)    | SSC   || %17s | %17s | %17s '%(lib_time_ssc, calc_time_ssc, com_time_ssc),
    '         | Band  || %17s | %17s | %17s '%(lib_time_band, calc_time_band, com_time_band),
    '         | DOS   || %17s | %17s | %17s '%(lib_time_dos, calc_time_dos, com_time_dos),
    '         | Total || %17s | %17s | %17s '%(lib_time_total, calc_time_total, com_time_total),
    '-----------------++-------------------+-------------------+-------------------',
    ' Lattice | a     || %17s | %17s | %17s '%(lib_latt[0], calc_latt[0], com_latt[0]),
    '   (A)   | b     || %17s | %17s | %17s '%(lib_latt[1], calc_latt[1], com_latt[1]),
    '         | c     || %17s | %17s | %17s '%(lib_latt[2], calc_latt[2], com_latt[2]),
    '-----------------++-------------------+-------------------+-------------------',
    ' Relaxed | a     || %17s | %17s | %17s '%(lib_force[0], calc_force[0], com_force[0]),
    ' Force   | b     || %17s | %17s | %17s '%(lib_force[1], calc_force[1], com_force[1]),
    ' (eV/A)  | c     || %17s | %17s | %17s '%(lib_force[2], calc_force[2], com_force[2]),
    '-----------------++-------------------+-------------------+-------------------',
    ' Fermi   | Relax || %17s | %17s | %17s '%(lib_fermi_relax, calc_fermi_relax, com_fermi_relax),
    ' Energy  | SSC   || %17s | %17s | %17s '%(lib_fermi_ssc, calc_fermi_ssc, com_fermi_ssc),
    '  (eV)   | Band  || %17s | %17s | %17s '%(lib_fermi_band, calc_fermi_band, com_fermi_band),
    '         | DOS   || %17s | %17s | %17s '%(lib_fermi_dos, calc_fermi_dos, com_fermi_dos),
    '-----------------++-------------------+-------------------+-------------------',
    ' Total   | Relax || %17s | %17s | %17s '%(lib_energy_relax, calc_energy_relax, com_energy_relax),
    ' Energy  | SSC   || %17s | %17s | %17s '%(lib_energy_ssc, calc_energy_ssc, com_energy_ssc),
    '  (eV)   | Band  || %17s | %17s | %17s '%(lib_energy_band, calc_energy_band, com_energy_band),
    '         | DOS   || %17s | %17s | %17s '%(lib_energy_dos, calc_energy_dos, com_energy_dos),
    '-----------------++-------------------+-------------------+-------------------',
    ' Band    | Gap   || %17s | %17s | %17s '%(lib_band_gap, calc_band_gap, com_band_gap),
    ' (eV)    | HOMO  || %17s | %17s | %17s '%(lib_band_homo, calc_band_homo, com_band_homo),
    '         | VBM   || %17s | %17s | %17s '%(lib_band_vbm, calc_band_vbm, com_band_vbm),
    '         | Diff. || %37s '%(com_band_diff),
    '         | Plot  || Check `%s`.' %com_band_plot,
    '-----------------++-------------------+-------------------+-------------------',
    ' DOS     | Diff. || %37s '%(com_dos_diff),
    '         | Plot  || Check `%s`.' %com_dos_plot,
    '-----------------++-------------------+-------------------+-------------------',
    ' Mag.    | Relax || %17s | %17s | %17s '%(lib_mag_relax, calc_mag_relax, com_mag_relax),
    ' (eV)    | SSC   || %17s | %17s | %17s '%(lib_mag_ssc, calc_mag_ssc, com_mag_ssc),
    '         | Band  || %17s | %17s | %17s '%(lib_mag_band, calc_mag_band, com_mag_band),
    '         | DOS   || %17s | %17s | %17s '%(lib_mag_dos, calc_mag_dos, com_mag_dos),
    '==============================================================================',
    ' ',
    ' ',
    ]
    report_txt += curr_obj_report_txt
  with open('report.txt', 'w') as fwp:
    for line in report_txt:
      fwp.write(line + '\n')
  os.chdir("..")
  return 0 


def report_with_pdflatex(calc_objs_infos, calc_obj_list):
  os.chdir("report/latex")
  obj_index = 0
  report_latex = [
  '\\documentclass[a4paper, 12pt]{article}',
  '\\usepackage{float}',
  '\\usepackage{graphicx}',
  '\\usepackage{subfigure}',
  '\\usepackage{multirow}',
  '\\usepackage[colorlinks,linkcolor=red,anchorcolor=blue,citecolor=green]{hyperref}',
  ' ',
  '\\title{\\textbf{VASPRUN SERVER TEST}}',
  '\\author{}',
  ' ',
  '\\begin{document}',
  '\\maketitle',
  '\\tableofcontents',
  '\\clearpage',
  '']
  for obj in calc_obj_list:
    lib_cpu_nodes, lib_cpu_cores, lib_time_relax, lib_time_ssc, lib_time_band, \
    lib_time_dos, lib_time_total, lib_latt, lib_force, lib_fermi_relax, \
    lib_fermi_ssc, lib_fermi_band, lib_fermi_dos, lib_energy_relax, \
    lib_energy_ssc, lib_energy_band, lib_energy_dos, lib_band_gap, \
    lib_band_homo, lib_band_vbm, lib_mag_relax, lib_mag_ssc, lib_mag_band, \
    lib_mag_dos, calc_cpu_nodes, calc_cpu_cores, calc_time_relax, \
    calc_time_ssc, calc_time_band, calc_time_dos, calc_time_total, calc_latt, \
    calc_force, calc_fermi_relax, calc_fermi_ssc, calc_fermi_band, \
    calc_fermi_dos, calc_energy_relax, calc_energy_ssc, calc_energy_band, \
    calc_energy_dos, calc_band_gap, calc_band_homo, calc_band_vbm, \
    calc_mag_relax, calc_mag_ssc, calc_mag_band, calc_mag_dos, com_cpu_nodes, \
    com_cpu_cores, com_time_relax, com_time_ssc, com_time_band, com_time_dos, \
    com_time_total, com_latt, com_force, com_fermi_relax, com_fermi_ssc, \
    com_fermi_band, com_fermi_dos, com_energy_relax, com_energy_ssc, \
    com_energy_band, com_energy_dos, com_band_gap, com_band_homo, \
    com_band_vbm, com_mag_relax, com_mag_ssc, com_mag_band, com_mag_dos, \
    com_band_diff, com_dos_diff, com_band_plot, com_dos_plot \
      = get_report_info(calc_objs_infos, obj)
    obj_index += 1
    obj_report_latex = [
    '\\section{[Object %d] %s}'%(obj_index, obj), 
    '\\begin{table}[H]\\centering',
    '  \\begin{tabular}{l|l||rrr}',
    '    \\hline',
    '    \\hline',
    '    \\multicolumn{2}{l||}{Items} & benchmark & current vasp & diff.\\\\',
    '    \\hline',
    '    \\multirow{2}{*}{CPUs} & Nodes & %10s & %10s & %10s\\\\'%(lib_cpu_nodes, calc_cpu_nodes, com_cpu_nodes),
    '                           & Cores & %10s & %10s & %10s\\\\'%(lib_cpu_cores, calc_cpu_cores, com_cpu_cores),
    '    \\hline',
    '    \\multirow{5}{*}{Time (s)} & Relax & %10s & %10s &%10s\\\\'%(lib_time_relax, calc_time_relax, com_time_relax),
    '                               & SSC   & %10s & %10s &%10s\\\\'%(lib_time_ssc, calc_time_ssc, com_time_ssc),
    '                               & Band  & %10s & %10s &%10s\\\\'%(lib_time_band, calc_time_band, com_time_band),
    '                               & DOS   & %10s & %10s &%10s\\\\'%(lib_time_dos, calc_time_dos, com_time_dos),
    '                               & Total & %10s & %10s &%10s\\\\'%(lib_time_total, calc_time_total, com_time_total),
    '    \\hline',
    '    \\multirow{3}{*}{Lattice (\\AA)} & a & %10s & %10s &%10s\\\\'%(lib_latt[0], calc_latt[0], com_latt[0]),
    '                                     & b & %10s & %10s &%10s\\\\'%(lib_latt[1], calc_latt[1], com_latt[1]),
    '                                     & c & %10s & %10s &%10s\\\\'%(lib_latt[2], calc_latt[2], com_latt[2]),
    '    \\hline',
    '    \\multirow{3}{*}{Relaxed Force (eV/\\AA)} & a & %10s & %10s &%10s\\\\'%(lib_force[0], calc_force[0], com_force[0]),
    '                                              & b & %10s & %10s &%10s\\\\'%(lib_force[1], calc_force[1], com_force[1]),
    '                                              & c & %10s & %10s &%10s\\\\'%(lib_force[2], calc_force[2], com_force[2]),
    '    \\hline',
    '    \\multirow{4}{*}{Fermi Energy (eV)} & Relax & %10s & %10s &%10s\\\\'%(lib_fermi_relax, calc_fermi_relax, com_fermi_relax),
    '                                        & SSC   & %10s & %10s &%10s\\\\'%(lib_fermi_ssc, calc_fermi_ssc, com_fermi_ssc),
    '                                        & Band  & %10s & %10s &%10s\\\\'%(lib_fermi_band, calc_fermi_band, com_fermi_band),
    '                                        & DOS   & %10s & %10s &%10s\\\\'%(lib_fermi_dos, calc_fermi_dos, com_fermi_dos),
    '    \\hline',
    '    \\multirow{4}{*}{Total Energy (eV)} & Relax & %10s & %10s &%10s\\\\'%(lib_energy_relax, calc_energy_relax, com_energy_relax),
    '                                        & SSC   & %10s & %10s &%10s\\\\'%(lib_energy_ssc, calc_energy_ssc, com_energy_ssc),
    '                                        & Band  & %10s & %10s &%10s\\\\'%(lib_energy_band, calc_energy_band, com_energy_band),
    '                                        & DOS   & %10s & %10s &%10s\\\\'%(lib_energy_dos, calc_energy_dos, com_energy_dos),
    '    \\hline',
    '    \\multirow{5}{*}{Band (eV)}  & Gap   & %10s & %10s & %10s\\\\'%(lib_band_gap, calc_band_gap, com_band_gap),
    '                                 & HOMO  & %10s & %10s & %10s\\\\'%(lib_band_homo, calc_band_homo, com_band_homo),
    '                                 & VBM   & %10s & %10s & %10s\\\\'%(lib_band_vbm, calc_band_vbm, com_band_vbm),
    '                                 & Diff. & \\multicolumn{2}{|r}{%10s}\\\\'%(com_band_diff),
    '                                 & Plot  & See FIG.\\ref{fig::banddos::%d}(a)\\\\' %obj_index,
    '    \\hline',
    '    \\multirow{2}{*}{DOS} & Diff. & \\multicolumn{2}{|r}{%10s}\\\\'%(com_dos_diff),
    '                          & Plot  & See FIG.\\ref{fig::banddos::%d}(b)\\\\' %obj_index,
    '                          \\hline',
    '    \\multirow{4}{*}{Mag. (\\(\\mu_B\\))} & Relax & %10s & %10s & %10s\\\\'%(lib_mag_relax, calc_mag_relax, com_mag_relax),
    '                                          & SSC   & %10s & %10s & %10s\\\\'%(lib_mag_ssc, calc_mag_ssc, com_mag_ssc),
    '                                          & Band  & %10s & %10s & %10s\\\\'%(lib_mag_band, calc_mag_band, com_mag_band),
    '                                          & DOS   & %10s & %10s & %10s\\\\'%(lib_mag_dos, calc_mag_dos, com_mag_dos),
    '    \\hline',
    '    \\hline',
    '  \\end{tabular}',
    '\\end{table}',
    '\\begin{figure}[H]\\centering',
    '  \\subfigure[Band compare]{',
    '    \\includegraphics[width=0.9\\textwidth]{%s}}'%(com_band_plot.replace('report','..')),
    '  \\subfigure[DOS compare]{',
    '    \\includegraphics[width=0.9\\textwidth]{%s}}'%(com_dos_plot.replace('report','..')),
    '  \\caption{Band-DOS compare}',
    '  \\label{fig::banddos::%d}'%(obj_index),
    '\\end{figure}',
    ' ',
    ' ']
    report_latex += obj_report_latex
  report_latex.append('\\end{document}')
  # Seve file 
  with open('report.tex', 'w') as fwp:
    for line in report_latex:
      if 'includegraphics' not in line:
        line = line.replace('_', '\\_')
      fwp.write(line + '\n')
  # Try to compile the tex file to pdf
  pdflatex = os.popen('which pdflatex 2>/dev/null').read()
  if pdflatex == '':
    print("[warning] No pdflatex was found in current server...")
    print("[tips] Downloads the whole report folder, and execute: ")
    print("       ` cd report/latex; pdflatex report.tex;  pdflatex report.tex; pdflatex report.tex `")
    print("       to obtain the report.pdf file ...")
  else:
    command = 'pdflatex report.tex > /dev/null;\
               pdflatex report.tex > /dev/null;\
               pdflatex report.tex > /dev/null'
    _ = os.system(command)
    if not os.path.isfile('report.pdf'):
      print("[error] pdflatex failed...")
      sys.exit(1)
    _ = os.system('cp report.pdf ..')
  os.chdir('../..')
  return 0 


def main():
  print(" ")
  print("[do] Checking the envriment...")
  env_check()
  print(" ")
  print("[do] Reading the calculation result...")
  calc_objs_infos, calc_obj_list = get_calc_objs_infos()
  print(" ")
  print("[do] Comparing the calculation result...")
  calc_objs_infos = compare_lib_calc(calc_objs_infos, calc_obj_list)
  print(" ")
  print("[do] Plot the band and dos...")
  calc_objs_infos = plot_compare_band(calc_objs_infos, calc_obj_list)
  calc_objs_infos = plot_compare_dos(calc_objs_infos, calc_obj_list)
  print(" ")
  print("[do] Writing the report file...")
  print("[subdo] Writing report.json file...")
  report_with_json(calc_objs_infos)
  print("[subdo] Writing report.txt file...")
  report_with_txt(calc_objs_infos, calc_obj_list)
  print("[subdo] Writing report.tex file...")
  report_with_pdflatex(calc_objs_infos, calc_obj_list)
  print(" ")
  print("[done] Report succeed!")
  return 0 


if __name__ == "__main__":
  main()
