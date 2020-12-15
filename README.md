# vasp2wannier

A python scirpt to submit the wannier90 fitting task based on VASP projectors.

## Basic Info

`Author` liyang@cmt.tsinghua

`Start Date` 2020.8.3

`Last Update` 2019.10.10

`Version` 1.1.0

## Description

A python script to submit the VASP calculation task in different job managemet system.

## Installtion

* Download the source code from:
https://github.com/kYangLi/vasp2wannier90/archive/master.zip

* Unzip it, and add the whole folder to the `PATH`. 
```bash
echo "export PATH=<vasprun>/<path>/:${PATH}" >> ~/.bashrc
```

## Input File
  
To enable this script, you need perpare the following files:
- `v2w.input.json` ======> (Optional)
- `POSCAR` ==============> (Necessary)
- `POTCAR` ==============> (Necessary)
- `KPOINTS.WNR` =========> (Necessary)
- `INCAR.WNR` ===========> (Necessary)
- `WAVECAR.WNR` =========> (Optional)
- `CHGCAR.WNR` ==========> (Optional)
- `KPOINTS.BAND` ========> (Necessary)
- `INCAR.BAND` ==========> (Necessary)
- `wannier90.win.vasp` ==> (Necessary)
- `wannier90.win.w90` ===> (Necessary)

### `vr.input.json`
The `v2w.input.json` contains the necessary parameters for a VASP task.
Here is an example of the `vr.input.json`:
```json
{
  "task_name":"va2wa",
  "intel_module": "ml intel/20u1",
  "wnr_vasp":"/home/liyang1/Software/CalcProg/VASP/Main/vasp-544-patched_wannier90-1.2_20u1/bin/vasp_ncl",
  "wannier90":"/home/liyang1/Software/CalcProg/Wannier90/wannier90-3.1.0_20u1/wannier90.x",
  "vaspkit":"/home/liyang1/Software/CalcProg/VASP/Tools/VaspKit/vaspkit-1.12/bin/vaspkit",
  "frowin_min_list":[-2.0, -0.5],
  "frowin_max_list":[2.0, 0.5],
  "sys_type":"pbs",
  "cores_per_node":24,
  "nodes_quantity":1,
  "pbs_walltime":48,
  "job_queue":"unset-queue",
  "plot_energy_window":[-2,2]
}
```

### `POSCAR`
VASP POSCAR file.

### `POTCAR`
VASP POTCAR file.

### `INCAR.[tag]`
VASP INCAR file, where the tag = `WNR`, `BAND`

### `KPOINTS.[tag]`
VASP KPOINTS file, where the tag = `WNR`, `BAND`

### `WAVECAR.WNR` `CHGCAR.WNR`
Files for VASP continue calculation.

### `wannier90.win.vasp`
wanier90.win file for the VASP projection.

### `wannier90.win.w90`
wannier90.win file for Wannier90 calculations.

## Submit the Task
After prepare the necessary file, just run `vasprun` in the calculation folder to submit the task.

## Result Output
The Calcualtion result can be found in the folder `RESULT`.

## Kill the Job
```bash
./_KILLJOBS.sh
```

## Clean the Foder to Initial
```bash
./_CLEAN.sh
```
