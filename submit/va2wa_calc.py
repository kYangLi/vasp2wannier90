import os 
import sys 
import json 
import time 


def paras_load():
  with open("v2w.allpara.json") as jfrp:
    all_para_list = json.load(jfrp)
    filename_list = all_para_list["filename"]
    calc_para_list = all_para_list["calc_para"]
    path_list = all_para_list["path_list"]
  return filename_list, calc_para_list, path_list


def grep(tstr, file):
  with open(file) as frp:
    lines = frp.readlines()
  targets = []
  for line in lines:
    if tstr in line:
      line = line.replace('\n','')
      targets.append(line)
  return targets


def grep_index(tstr, file):
  with open(file) as frp:
    lines = frp.readlines()
  targets_line_index = []
  index = 0
  for line in lines:
    if tstr in line:
      targets_line_index.append(index)
    index += 1
  return targets_line_index


def mpirun(filename_list, calc_para_list, calc_prog, calc_prog_log):
  sys_type = calc_para_list["sys_type"]
  nodes_quantity = calc_para_list["nodes_quantity"]
  cores_per_node = calc_para_list["cores_per_node"]
  total_cores_number = nodes_quantity * cores_per_node
  intel_module = calc_para_list["intel_module"]
  # Submit the jobs
  if sys_type == 'pbs':
    mpi_machinefile = filename_list["mpi_machinefile"]
    command = "mpirun -machinefile ../%s -np %d %s >> %s" %(mpi_machinefile,
                                                            total_cores_number,
                                                            calc_prog,
                                                            calc_prog_log)
  elif sys_type == 'slurm':
    command = "srun %s >> %s" %(calc_prog, calc_prog_log)
  elif sys_type == 'nscc':
    command = "yhrun -N %d -n %d %s >> %s" %(nodes_quantity,
                                             total_cores_number,
                                             calc_prog,
                                             calc_prog_log)
  start_time = time.time()
  _ = os.system("date >> %s" %calc_prog_log) 
  _ = os.system(intel_module + '; ' + command)
  _ = os.system("date >> %s" %calc_prog_log)
  end_time = time.time()
  time_spend = end_time - start_time
  return time_spend


def vasp_res_collect(filename_list, time_spend, task_tag):
  # Prepare 
  result_folder = filename_list["result_folder"]
  result_folder = '../%s' %result_folder
  if not os.path.isdir(result_folder):
    os.mkdir(result_folder)
  res_json_file = filename_list['result_json']
  res_json_file = os.path.join(result_folder, res_json_file)
  if os.path.isfile(res_json_file):
    with open(res_json_file) as jfrp:
      res_record = json.load(jfrp)
  else:
    res_record = {"time"             : {},
                  "lattice_para"     : {},
                  "fermi"            : {}, 
                  "energy"           : {}, 
                  "force_per_atom"   : {}, 
                  "total_mag"        : {},
                  "w90_fitting_time" : {},
                  "w90_band_diff"    : {"curr_min" : ['none', 99999999999],
                                        "all"      : {}
                                       }
    }
  # Lattice constant
  with open('OUTCAR') as frp:
    lines = frp.readlines()
  index = 0
  for line in lines:
    if 'length of vectors' in line:
      lc_index = index
    index += 1
  lc_index += 1
  lcs = lines[lc_index].split()
  lcs = [float(val) for val in lcs[:3]]
  # Fermi level
  fermi_levels = grep('fermi', 'OUTCAR')
  fermi_level = fermi_levels[-1].split(':')[1].split('X')[0].replace(' ','')
  fermi_level = float(fermi_level)
  # Total energy
  total_energys = grep ('sigma', 'OUTCAR')
  total_energy = total_energys[-1].split('=')[2].replace(' ','')
  total_energy = float(total_energy)
  # Total force
  with open('POSCAR') as frp:
    lines = frp.readlines()
  atom_num = lines[6]
  atom_num = atom_num.replace('\n','')
  atom_num = atom_num.split()
  atom_num = [int(val) for val in atom_num]
  atom_num = sum(atom_num)
  force_per_atoms = grep('total drift', 'OUTCAR')
  force_per_atom = force_per_atoms[-1].split(':')[1].split()
  force_per_atom[0] = float(force_per_atom[0])/atom_num
  force_per_atom[1] = float(force_per_atom[1])/atom_num
  force_per_atom[2] = float(force_per_atom[2])/atom_num
  # Total magnet
  total_mags = grep('mag=', 'OSZICAR')
  total_mag = total_mags[-1].split('=')[4].split()
  if len(total_mag) == 3:
    total_mag = (float(total_mag[0])**2 + \
                 float(total_mag[1])**2 + \
                 float(total_mag[2])**2)**0.5
  else:
    total_mag = float(total_mag[0])
  # Total time
  total_time = res_record["time"].get("total", 0)
  total_time += time_spend
  # Result record
  res_record["time"]["total"] = total_time
  res_record["time"][task_tag] = time_spend
  res_record["lattice_para"][task_tag] = lcs
  res_record["fermi"][task_tag] = fermi_level
  res_record["energy"][task_tag] = total_energy
  res_record["force_per_atom"][task_tag] = force_per_atom
  res_record["total_mag"][task_tag] = total_mag
  with open(res_json_file, 'w') as jfwp:
    json.dump(res_record, jfwp, indent=2)
  with open('RUN_TIME', 'w') as fwp:
    fwp.write('%f\n' %time_spend)
  return 0


def vasp_wnr(filename_list, calc_para_list):
  wnr_folder = filename_list["wnr_folder"]
  wnr_vasp = calc_para_list["wnr_vasp"]
  vasp_log = filename_list["vasp_log"]
  if os.path.isdir(wnr_folder):
    print("[info] Folder %s already exist, skip." %wnr_folder)
    os.chdir(wnr_folder)
    with open('RUN_TIME') as frp:
      time_spend = float(frp.readlines()[0].replace('\n',''))
    vasp_res_collect(filename_list, time_spend, 'wnr')
    os.chdir('..')
  else:
    print("[do] Calculate VASP to Wannier...")
    # File prepare
    os.mkdir(wnr_folder)
    os.chdir(wnr_folder)
    _ = os.system('cp ../INCAR.WNR INCAR')
    _ = os.system('ln -s ../POTCAR POTCAR')
    _ = os.system('cp ../POSCAR .')
    _ = os.system('cp ../KPOINTS.WNR KPOINTS')
    _ = os.system('cp ../wannier90.win.vasp wannier90.win')
    # Job Submit
    time_spend = mpirun(filename_list, calc_para_list, wnr_vasp, vasp_log)
    # Res. Collect
    vasp_res_collect(filename_list, time_spend, 'wnr')
    _ = os.system('cp wannier90.win ../wannier90.win.vasp.res')
    # Quit Dir.
    os.chdir('..')
  return 0


def vasp_band_plot_collect(filename_list, calc_para_list, path_list, mode):
  ## Prepare 
  curr_path = os.getcwd()
  result_folder = filename_list["result_folder"]
  result_folder = '../%s' %result_folder
  if not os.path.isdir(result_folder):
    print("[error] No result folder avaliable...")
    sys.exit(1)
  band_res_folder = filename_list["band_res_folder"]
  band_res_folder = os.path.join(result_folder, band_res_folder)
  if not os.path.isdir(band_res_folder):
    os.mkdir(band_res_folder)
  ## Use vaspkit to generate the file
  vaspkit = calc_para_list["vaspkit"]
  vaspkit_log = filename_list["vaspkit_log"]
  if mode == 'scan':
    vaspkit_band_code = '252'
    vaspkit_pband_code = '254'
  else: #pbe mode
    vaspkit_band_code = '211'
    vaspkit_pband_code = '213'
  # Total Band 
  command = '(echo %s; echo 0) | %s >> %s' \
            %(vaspkit_band_code, vaspkit, vaspkit_log)
  _ = os.system(command)
  # Projected Band
  command = '(echo %s) | %s >> %s' %(vaspkit_pband_code, vaspkit, vaspkit_log)
  _ = os.system(command)
  # Copy Band file 
  _ = os.system('cp KLABELS %s' %band_res_folder)
  _ = os.system('cp BAND.dat %s' %band_res_folder)
  _ = os.system('cp PBAND_*.dat %s' %band_res_folder)
  _ = os.system('cp BAND_GAP %s' %band_res_folder)
  # Plot Band 
  va2wa_path = path_list["va2wa_path"]
  band_plot_script = "%s/plot/vaspkit_band.py" %va2wa_path
  python_exec = path_list["python_exec"]
  band_fig = filename_list["band_fig"]
  pew = calc_para_list["plot_energy_window"]
  os.chdir(band_res_folder)
  command = "%s %s -n %s -u %f -d %f" %(python_exec, band_plot_script,
                                        band_fig, pew[1], pew[0])
  _ = os.system(command)
  _ = os.system("rm band_plot.py 2>/dev/null")
  _ = os.system("ln -s %s band_plot.py" %band_plot_script)
  os.chdir(curr_path)
  return 0


def pbe_band(filename_list, calc_para_list, path_list):
  band_folder = filename_list["band_folder"]
  wnr_folder = filename_list["wnr_folder"]
  band_vasp = calc_para_list["wnr_vasp"]
  vasp_log = filename_list["vasp_log"]
  # File prepare
  os.mkdir(band_folder)
  os.chdir(band_folder)
  _ = os.system('cp ../INCAR.BAND INCAR')
  _ = os.system('ln -s ../POTCAR POTCAR')
  _ = os.system('cp ../POSCAR .')
  _ = os.system('cp ../KPOINTS.BAND KPOINTS')
  chgcar = '../%s/CHGCAR' %(wnr_folder)
  if os.stat(chgcar).st_size == 0:
    print("[error] CHGCAR is empty, cannot calculate scan band...")
    sys.exit(1)
  _ = os.system('ln -s %s CHGCAR' %chgcar)
  _ = os.system('ln -s ../%s/DOSCAR DOSCAR.WNR' %wnr_folder)
  # Job Submit
  time_spend = mpirun(filename_list, calc_para_list, band_vasp, vasp_log)
  # Res. Collect
  vasp_res_collect(filename_list, time_spend, 'band')
  _ = os.system('mv DOSCAR DOSCAR.BAND')
  _ = os.system('mv DOSCAR.WNR DOSCAR')
  vasp_band_plot_collect(filename_list, calc_para_list, path_list, 'pbe')
  # Quit Dir.
  os.chdir('..')
  return 0


def get_kpath_ibzk():
  with open('KPATH.in') as frp:
    lines = frp.readlines()
  kpoints_per_path = int(lines[1].replace(' ','').replace('\n',''))
  kpath_ibzk_origin_lines = lines[4:]
  kiols = []
  for kiol in kpath_ibzk_origin_lines:
    if (kiol.replace(' ','').replace('\n','') == ''):
      continue
    kiols.append(kiol)
  kpath_num = len(kiols)
  if kpath_num%2 == 1:
    print("[error] KPOINTS.BAND error, the kpath lines number is odd...")
    sys.exit(1)
  kpath_num //= 2
  kpath_ibzk_lines = []
  for kpath_index in range(kpath_num):
    hsk_beg_index = 2 * kpath_index
    hsk_end_index = 2 * kpath_index + 1
    hsk_begin = kiols[hsk_beg_index].split()[:3]
    hsk_begin = [float(val) for val in hsk_begin]
    hsk_end = kiols[hsk_end_index].split()[:3]
    hsk_end = [float(val) for val in hsk_end]
    hsk_array = [
      hsk_end[0] - hsk_begin[0],
      hsk_end[1] - hsk_begin[1],
      hsk_end[2] - hsk_begin[2]
    ]
    for index in range(kpoints_per_path):
      kx = hsk_begin[0] + (index/(kpoints_per_path-1)) * hsk_array[0] 
      ky = hsk_begin[1] + (index/(kpoints_per_path-1)) * hsk_array[1]
      kz = hsk_begin[2] + (index/(kpoints_per_path-1)) * hsk_array[2]
      kpath_ibzk_line = '%.8f  %.8f  %.8f  0' %(kx, ky, kz)
      kpath_ibzk_lines.append(kpath_ibzk_line)
  return kpath_num, kpoints_per_path, kpath_ibzk_lines


def combine_ssc_band_kpoints():
  with open('KPOINT.WNR') as frp:
    lines = frp.readlines()
  try:
    kgrid = lines[3].replace('\n','')
    kgrid = kgrid.split()
    kgrid = [int(val) for val in kgrid[0:3]]
  except BaseException:
    print("[error] Cannot read the kgrid from KPOINTS.WNR.")
    print("[error] Please make sure the KPOINTS.WNR is under the grid mode.")
  with open('IBZKPT.WNR') as frp:
    lines = frp.readlines()
  wnr_kp_num = int(lines[1].replace(' ','').replace('\n',''))
  wnr_ibzk_lines = lines[3:(wnr_kp_num+3)]
  wnr_ibzk_lines = [val.replace('\n','') for val in wnr_ibzk_lines]
  kpath_num, kpoints_per_path, kpath_ibzk_lines = get_kpath_ibzk()
  band_kp_num = kpath_num * kpoints_per_path
  total_kpoints_lines_num = wnr_kp_num + band_kp_num
  # Write the KPOINTS for SCAN band
  kpath_kpoints_str = ''
  for _ in range(kpath_num):
    kpath_kpoints_str += '%d '%kpoints_per_path
  paras_line = '-9999  %d %d %d  %d  -9999  %d  %d  %s'%(kgrid[0], kgrid[1], kgrid[2], wnr_kp_num, band_kp_num, kpath_num, kpath_kpoints_str)
  with open('KPOINTS', 'w') as fwp:
    fwp.write('%s\n'%(paras_line))
    fwp.write('      %d\n'%(total_kpoints_lines_num))
    fwp.write('Reciprocal lattice\n')
    for wnr_ibzk_line in wnr_ibzk_lines:
      fwp.write(wnr_ibzk_line + '\n')
    for kpath_ibzk_line in kpath_ibzk_lines:
      fwp.write(kpath_ibzk_line + '\n')
  return 0


def scan_band(filename_list, calc_para_list, path_list):
  band_folder = filename_list["band_folder"]
  wnr_folder = filename_list["wnr_folder"]
  band_vasp = calc_para_list["wnr_vasp"]
  vasp_log = filename_list["vasp_log"]
  # File prepare
  os.mkdir(band_folder)
  os.chdir(band_folder)
  _ = os.system('cp ../INCAR.BAND INCAR')
  _ = os.system('ln -s ../POTCAR POTCAR')
  _ = os.system('cp ../POSCAR .')
  _ = os.system('cp ../KPOINTS.BAND KPATH.in')
  _ = os.system('cp ../KPOINT.WNR KPOINTS.WNR')
  ibzkpt = '../%s/IBZKPT'%(wnr_folder)
  if not os.path.isfile(ibzkpt):
      print("[error] No IBZKPT file was found in VASP.WNR folder...")
      print("[error] Please make sure the KPOINTS.WNR is under the grid mode.")
      sys.exit(1)
  _ = os.system('cp %s IBZKPT.WNR' %ibzkpt)
  combine_ssc_band_kpoints()
  wavecar = "../%s/WAVECAR" %(wnr_folder)
  if os.stat(wavecar).st_size == 0:
    print("[error] WAVECAR is empty, cannot calculate scan band...")
    sys.exit(1)
  _ = os.system('ln -s %s WAVECAR' %wavecar)
  # Job Submit
  time_spend = mpirun(filename_list, calc_para_list, band_vasp, vasp_log)
  # Res. Collect
  vasp_res_collect(filename_list, time_spend, 'band')
  vasp_band_plot_collect(filename_list, calc_para_list, path_list, 'scan')
  # Quit Dir.
  os.chdir('..')
  return 0


def vasp_band(filename_list, calc_para_list, path_list):
  band_folder = filename_list["band_folder"]
  # Band mode
  if os.path.isfile('INCAR.BAND'):
    band_mode = 'pbe'
    with open('INCAR.BAND') as frp:
      lines = frp.readlines()
    for line in lines:
      upl = line.upper()
      upl = upl.split('#')[0]
      if ('METAGGA' in upl) and ('SCAN' in upl):
        band_mode = 'scan'
        break
  # Calc band or not 
  if os.path.isdir(band_folder):
    print("[info] Folder %s already exist, skip." %band_folder)
    os.chdir(band_folder)
    with open('RUN_TIME') as frp:
      time_spend = float(frp.readlines()[0].replace('\n',''))
    vasp_res_collect(filename_list, time_spend, 'band')
    vasp_band_plot_collect(filename_list, calc_para_list, path_list, band_mode)
    os.chdir('..')
  else:
    if band_mode == 'scan':
      print("[do] Calculate SCAN band ...")
      scan_band(filename_list, calc_para_list, path_list)
    else:
      print("[do] Calculate PBE band ...")
      pbe_band(filename_list, calc_para_list, path_list)
  return 0


def wannier_res_collect(filename_list, path_list, time_spend, tag):
  result_folder = os.path.join('../..', filename_list["result_folder"])
  res_json_file = os.path.join(result_folder, filename_list["result_json"])
  wannier_res = os.path.join(result_folder, filename_list["w90_res_folder"])
  va2wa_path = path_list["va2wa_path"]
  python_exec = path_list["python_exec"]
  w90_plot_py = os.path.join(va2wa_path, 'plot', 'wannier90_band.py')
  vasp_band_json = os.path.join(result_folder, 
                                filename_list["band_res_folder"], 
                                filename_list["band_fig"]+'.json')
  band_file_json = 'band_' + tag + '.json'
  band_figure = 'band_' + tag + '.png'
  # Read in fermi level
  with open('../input/E_FERMI')  as frp:
    fermi_level = frp.readlines()
    fermi_level = float(fermi_level[0].replace('\n', '').replace(' ',''))
  if not os.path.isdir(wannier_res):
    os.mkdir(wannier_res)
  with open(res_json_file) as jfrp:
    result_json = json.load(jfrp)
  result_json["w90_fitting_time"][tag] = time_spend
  # Collect the wannier band
  if os.path.isfile('wannier90_band.dat') or \
     (os.path.isfile('wannier90.up_band.dat') and \
      os.path.isfile('wannier90.dn_band.dat')):
    # Plot band
    command = '%s %s -t %s -b %s -e %f' \
              %(python_exec, w90_plot_py, tag, vasp_band_json, fermi_level)
    _ = os.system(command)
    _ = os.system('cp %s %s/' %(band_figure, wannier_res))
    _ = os.system('cp %s %s/' %(band_file_json, wannier_res))
    _ = os.system('ln -s %s . ' %w90_plot_py)
    with open('current_band_diff.json') as jfrp:
      cbd = json.load(jfrp)
    cbd = cbd['cbd']
    curr_min_diff = result_json["w90_band_diff"]["curr_min"][1]
    if cbd < curr_min_diff:
      result_json["w90_band_diff"]["curr_min"] = [tag, cbd]
  else:
    error_file = os.path.join(wannier_res, tag+'.error')
    with open(error_file, 'w') as fwp:
      fwp.write('band calc error...\n')
    cbd = 'error'
  result_json["w90_band_diff"]['all'][tag] = cbd
  # Dump json data 
  with open(res_json_file, 'w') as jfwp:
    json.dump(result_json, jfwp, indent=2)
  with open('RUN_TIME', 'w') as fwp:
          fwp.write('%f\n' %time_spend)
  return 0


def wnr90_band(filename_list, calc_para_list, path_list):
  w90_folder = filename_list["w90_folder"]
  wnr_folder = filename_list["wnr_folder"]
  wnr90_log = filename_list["wnr90_log"]
  wannier90 = calc_para_list["wannier90"]
  frowin_min_list = calc_para_list["frowin_min_list"]
  frowin_max_list = calc_para_list["frowin_max_list"]
  if not os.path.isdir(w90_folder):
    os.mkdir(w90_folder)
  os.chdir(w90_folder)
  # Get the ISPIN numnber
  spin_num = grep('ISPIN', '../%s/OUTCAR'%(wnr_folder))
  spin_num = int(spin_num[-1].split()[2])
  # Create the perpare input folder
  if not os.path.isdir('input'):
    os.mkdir('input')
    os.chdir('input')
    # Copy files
    _ = os.system('cp ../../wannier90.win.vasp.res wannier90.win.vasp')
    _ = os.system('cp ../../wannier90.win.w90 .')
    _ = os.system('cp ../../KPOINTS.BAND .')
    if spin_num == 1:
      _ = os.system('ln -s ../../%s/wannier90.eig .' %(wnr_folder))
      _ = os.system('ln -s ../../%s/wannier90.mmn .' %(wnr_folder))
      _ = os.system('ln -s ../../%s/wannier90.amn .' %(wnr_folder))
    else:
      _ = os.system('ln -s ../../%s/wannier90.up.eig .' %(wnr_folder))
      _ = os.system('ln -s ../../%s/wannier90.up.mmn .' %(wnr_folder))
      _ = os.system('ln -s ../../%s/wannier90.up.amn .' %(wnr_folder))
      _ = os.system('ln -s ../../%s/wannier90.dn.eig .' %(wnr_folder))
      _ = os.system('ln -s ../../%s/wannier90.dn.mmn .' %(wnr_folder))
      _ = os.system('ln -s ../../%s/wannier90.dn.amn .' %(wnr_folder))
  else:
    os.chdir('input')
  # Fermi energy 
  fermi_levels = grep('fermi', '../../%s/OUTCAR' %(wnr_folder))
  fermi_level = fermi_levels[-1].split(':')[1].split('X')[0].replace(' ','')
  fermi_level = float(fermi_level)
  with open('E_FERMI','w')  as fwp:
    fwp.write('%f\n' %fermi_level)
  # Band K path
  with open('KPOINTS.BAND') as frp:
    kpath_data = frp.readlines()
  bnp = kpath_data[1].replace(' ','').replace('\n','')
  bnp = int(bnp)
  kpath_win = ['\n',
                'bands_num_points = %d \n' %bnp,
                'begin kpoint_path\n']
  hsk_list = []
  for line in kpath_data[4:]:
    line = line.replace('\n','')
    if line.replace(' ','') == '':
      continue
    hsk_list.append(line)
  if len(hsk_list)%2 != 0:
    print("[error] KPOINTS.BAND kpath number is odd...")
    sys.exit(1)
  kpath_num = len(hsk_list) // 2
  for kapth_index in range(kpath_num):
    beg_k_index = 2 * kapth_index
    end_k_index = 2 * kapth_index + 1
    beg_k_line = hsk_list[beg_k_index].split()
    end_k_line = hsk_list[end_k_index].split()
    beg_k_str = '  '.join([beg_k_line[3], beg_k_line[0], 
                            beg_k_line[1],beg_k_line[2]])
    end_k_str = '  '.join([end_k_line[3], end_k_line[0], 
                            end_k_line[1],end_k_line[2]])
    kpath_str = beg_k_str + '    ' + end_k_str
    kpath_win.append(kpath_str + '\n')
  kpath_win.append('end kpoint_path\n')
  # Read in the win file for vasp
  with open('wannier90.win.vasp') as frp:
    vasp_win = frp.readlines()
  if spin_num == 1:
    eig_wannier = 'wannier90.eig'
  else:
    eig_wannier = 'wannier90.up.eig'
  with open(eig_wannier) as frp:
    lines = frp.readlines()
  last_band_index = 0
  for line in lines:
    band_index = int(line.split()[0])
    if last_band_index > band_index:
      break
    last_band_index = band_index
  band_num = last_band_index
  for line_index in range(len(vasp_win)):
    if 'num_bands' in vasp_win[line_index]:
      vasp_win[line_index] = 'num_bands = %d \n' %band_num
    elif 'exclude_bands' in vasp_win[line_index]:
      vasp_win[line_index] = '#' + vasp_win[line_index]
  # Read in the win file for wannier90 
  with open('wannier90.win.w90') as frp:
    w90_win = frp.readlines()
  # Quit the input folder
  os.chdir('..')
  # Loop for each froz_win folder
  for frowin_min in frowin_min_list:
    real_frowin_min = frowin_min + fermi_level
    for frowin_max in frowin_max_list:
      real_frowin_max = frowin_max + fermi_level
      tag = '%.2f_%.2f' %(frowin_min, frowin_max)
      curr_fw_folder = 'fw_%s' %(tag)
      ## If the froz folder exist
      if os.path.isdir(curr_fw_folder):
        print("[info] Folder %s/%s already exist, skip."
              %(w90_folder, curr_fw_folder))
        # Recollect the result
        os.chdir(curr_fw_folder)
        with open('RUN_TIME') as frp:
          time_spend = float(frp.readlines()[0].replace('\n',''))
        wannier_res_collect(filename_list, path_list, time_spend, tag)
        os.chdir('..')
        continue
      ## If the froz folder not exist
      print("[do] Calculating tag: %s" %tag)
      # Froz window Dir.
      os.mkdir(curr_fw_folder)
      os.chdir(curr_fw_folder)
      # Create the wannier90.win
      fw_win = ['\n',
                'dis_froz_min = %f \n' %real_frowin_min,
                'dis_froz_max = %f \n' %real_frowin_max,
                '\n']
      with open('wannier90.win', 'w') as fwp:
        total_win = vasp_win + fw_win + w90_win + kpath_win
        fwp.writelines(total_win) 
      # eig, amn & mmn
      if spin_num == 1:
        _ = os.system('ln -s ../input/wannier90.eig .')
        _ = os.system('ln -s ../input/wannier90.mmn .')
        _ = os.system('ln -s ../input/wannier90.amn .')
      else:
        _ = os.system('ln -s ../input/wannier90.up.eig .')
        _ = os.system('ln -s ../input/wannier90.up.mmn .')
        _ = os.system('ln -s ../input/wannier90.up.amn .')
        _ = os.system('ln -s ../input/wannier90.dn.eig .')
        _ = os.system('ln -s ../input/wannier90.dn.mmn .')
        _ = os.system('ln -s ../input/wannier90.dn.amn .')
        _ = os.system('cp wannier90.win wannier90.up.win')
        _ = os.system('mv wannier90.win wannier90.dn.win')
      # Job Submit
      old_mf = filename_list["mpi_machinefile"]
      filename_list["mpi_machinefile"] = '../%s' %old_mf
      if spin_num == 1:
        w90 = wannier90 + '  wannier90'
        time_spend = mpirun(filename_list, calc_para_list, w90, wnr90_log)
      else:
        w90_up = wannier90 + '  wannier90.up'
        w90_dn = wannier90 + '  wannier90.dn'
        time_up = mpirun(filename_list, calc_para_list, w90_up, wnr90_log)
        time_dn = mpirun(filename_list, calc_para_list, w90_dn, wnr90_log)
        time_spend = time_up + time_dn
      filename_list["mpi_machinefile"] = old_mf
      # Collect the result
      wannier_res_collect(filename_list, path_list, time_spend, tag)
      # Quit the Dir.
      os.chdir('..')
  return 0 


def main():
  ## Prepare 
  filename_list, calc_para_list, path_list = paras_load()
  ## Calculate
  vasp_wnr(filename_list, calc_para_list)
  vasp_band(filename_list, calc_para_list, path_list)
  wnr90_band(filename_list, calc_para_list, path_list)
  print("[done]")
  return 0


if __name__ == "__main__":
  main()
