# Copyright 2022
# Author: scott.allan.stone@gmail.com (Scott Stone)
from analyzer import Analyzer
from glob import glob
import multiprocessing as mp
import time

def process(file: str):
    start_time = time.perf_counter()
    analyzer = Analyzer(file,
                        stimulus_marker_name='Stimulus_Markers',
                        gaze_name='pupil_capture')
    analyzer.analyze()

    # Also do the dispersion of the brightness condition
    analyzer.calculate_dispersion(phase='brightness')
    #analyzer.calculate_frequency()
    print(f"\t{file}: took: {time.perf_counter() - start_time:.2f}s")

def main():
    files = glob('data/pt*/*.xdf')
    with mp.Pool() as pool:
        pool.map(process, files)

if __name__ == '__main__':
    main()