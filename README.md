# Vertigo Nystagmus Stroke assessment stimulus presentation

[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/downloads/release/python-397/)

This is the stroke assessment stimulus and data recording software. It takes about ~5m to run, depending on how long it takes to position the glasses. *If you're not sure what this is, you're probably in the wrong place.*

---
## Assessment
1. **Stare**
The participant stares at a cross in the centre of the screen for 20s.
2. **Pursuit**
A dot appears and begins to move to the left, then right, then up, then down. There is also a secondary portion where the dot will move to the final position and hold for approx. 1s. 
3. **Vestibulo-ocular response**
While fixating on the centre cross, the participant will rotate their entire head up, then down, then centre, then left, then right. This tests if the VOR is still intact.
4. **Jump**
A fixation cross appears in the centre. Then a dot will appear on either the left or right with a pseudorandom inter-stimulus-interval (centred around ~1.5s) the dot will appear on the opposite side, with a return to the centre in between.
5. **Brightness**
While fixating on the centre cross, the background will change from black to white, eliciting a pupillary response.
---
## Conda environment
There is a conda environment YAML file included [`environment.yml`](environment.yml) that you can use. It will use the [`requirements.txt`](requirements.txt) file to get the dependencies.

To do this, run:
`conda env create -f environment.yml`

The default name for the environment is `stroke`.

## Running
Equip the eyetracker, and run the Pupil Labs recorder program. Ensure the LSL plugin is active.
Open a terminal and make sure you are in the `stroke` conda evironment: `conda activate stroke`
Then, run `python run_stimulus.py`

The other way to run the stimulus is to open a command prompt or terminal that can see `conda` (make sure it's added to your system path) and run:
`./run.bat`

This will enter the `stroke` conda environment and run the `run_stimulus.py` script. Note that there is no error-checking right now, so it will not exit gracefully.

### Questions
If you have any questions, please email me: sastone@ualberta.ca
