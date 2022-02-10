from analyzer import Analyzer
from glob import glob
import multiprocessing as mp
import time

def process(file: str):
    start_time = time.perf_counter()
    analyzer = Analyzer(file,
                        stimulus_marker_name='Stimulus_Markers',
                        gaze_name='TobiiGaze')
    analyzer.calculate_distance()
    analyzer.calculate_dispersion()
    analyzer.calculate_velocity()
    analyzer.plot()
    print(f"\t\t{file}: took: {time.perf_counter() - start_time:.2f}s")

def main():
    pt_files = glob('data/pt*/*.xdf')
    with mp.Pool() as pool:
        pool.map(process, pt_files)

if __name__ == '__main__':
    main()