# generated by run_all_notebooks.py
echo "running 14 notebooks"

set -ev
jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_anticrossing.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_awg_to_plunger.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_charge_sensor.ipynb
xvfb-run -a jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_coulomb_peak.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_doublegauss_expdecay_rts.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_elzerman_readout.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_fermi_fitting.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_fit_ramsey.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_gate_pinchoff.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_lever_arm_charging_energy.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_ohmic.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_onedot_scan.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_PAT_fitting.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/analysis/example_polFitting.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/simulation/example_PAT_simulations.ipynb
jupyter nbconvert --to notebook --execute docs/notebooks/datasets/example_dataset_processing.ipynb
