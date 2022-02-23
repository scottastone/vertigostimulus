# Copyright 2022
# Author: scott.allan.stone@gmail.com (Scott Stone)
from msilib.schema import Error
import liesl
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
from pandas import set_eng_float_format

class Analyzer:
    def __init__(self, 
                 file: str,
                 stimulus_marker_name: str,
                 gaze_name: str,
                 phases: str = None,
                 dpi: int = 300):

        self.file = file
        self.stimulus_marker_name = stimulus_marker_name
        self.gaze_name = gaze_name
        self.data = liesl.XDFFile(file, verbose=True) # verbose is broken
        self.sample_rate = self.data[self.gaze_name]._stream['info']['effective_srate']
        self.phases = phases # default to None
        self.dpi = dpi # default to 300, for image output

        self._pull_marker_data()
        self._find_start_end_phase_indices()
        self._convert_idx_to_timestamps()
        self._get_gaze_data()
        self._get_gaze_by_phase()
        valid = self._verify_integrity
        if valid is False:
            raise Error("\tData integrity check failed")
        else:
            print(f"\tData validity passed. Found {len(self.phases)} phases and {len(self.gaze_data)} gaze chunks.")

    def _verify_integrity(self) -> bool:
        """Verify that we have all of the data (5 streams)
        Checks if: 
            - There are 5 streams
            - There are the correct number of markers
            - There are the correct number of gaze chunks
        """
        if len(self.data) != len(self.phases):
            return False

        for stream in zip(self.data, self.phases):
            gaze, phase = stream
            # Check if gaze has any data in it
            if len(gaze) == 0:
                return False
            # Check if the phase has any data in it
            if len(phase) == 0:
                return False

        return True

    def _pull_marker_data(self) -> None:
        """Pull the data from the file and store it
        """
        self.markers = self.data[self.stimulus_marker_name]
        if self.phases is None:
            self.phases = ['stare','pursuit','vor', 'jump', 'brightness']
        self.phase_starts = self.phases.copy()
        self.phase_ends = [phase + '_end' for phase in self.phase_starts]

    def _find_start_end_phase_indices(self) -> None:
        """Find the indices of the start and end of each phase
        """
        self.marker_start_idx, self.marker_end_idx = [], []
        for marker in self.markers.time_series:
            for marker_start in self.phase_starts:
                if marker[0] == marker_start:
                    self.marker_start_idx.append(self.markers.time_series.index(marker))
            for marker_end in self.phase_ends:
                if marker[0] == marker_end:
                    self.marker_end_idx.append(self.markers.time_series.index(marker))

    def _convert_idx_to_timestamps(self) -> None:
        """Convert the marker_stimulus timestamps to gaze timestamps so we can extract the data
        """
        self.timestamps_start, self.timestamps_end = [], []
        for idx in zip(self.marker_start_idx, self.marker_end_idx):
            self.timestamps_start.append(self.markers.time_stamps[idx[0]])
            self.timestamps_end.append(self.markers.time_stamps[idx[1]])
            
    def _get_gaze_data(self) -> None:
        """Get gaze data for each phase
        """
        self.gaze = self.data[self.gaze_name]
        self.gaze_timestamps_start, self.gaze_timestamps_end = [], []
        for ts in zip(self.timestamps_start, self.timestamps_end):
            self.gaze_timestamps_start.append(np.min(np.abs(ts[0] - self.gaze.time_stamps).argmin()))
            self.gaze_timestamps_end.append(np.min(np.abs(ts[1] - self.gaze.time_stamps).argmin()))

    def _get_gaze_by_phase(self) -> None:
        """Get gaze data for each phase
        """
        self.gaze_data = []
        for idx in zip(self.gaze_timestamps_start, self.gaze_timestamps_end):
            start, end = idx
            self.gaze_data.append(self.gaze.time_series[start:end, 1:3])

    def calculate_velocity(self, save=True, show=False) -> None:
        """Calculate the velocity of gaze data for each phase
        """
        self.velocity = []
        for gaze_data in self.gaze_data:
            self.velocity.append(np.linalg.norm(np.gradient(gaze_data, axis=0), axis=1))

        # Plot the velocity
        for velocity, phase in zip(self.velocity, self.phases):
            plt.figure()
            plt.title(f"Velocity of {phase} data")
            plt.plot(velocity)
            if save is True:
                plt.savefig(f'{self.file[:-4]}_{phase}_velocity.png', dpi=self.dpi)   
            if show is True:
                plt.show()
            
            plt.clf()

    def calculate_distance(self) -> None:
        """Calculate the distance between gaze data for each phase
        """
        def dist(x1, y1, x2, y2):
            return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        self.distances = []
        for gaze_data in self.gaze_data:
            distance = 0
            for gaze_idx in range(len(gaze_data) - 1):
                distance += dist(gaze_data[gaze_idx, 0], gaze_data[gaze_idx, 1],
                                      gaze_data[gaze_idx + 1, 0], gaze_data[gaze_idx + 1, 1])
            self.distances.append(distance)

    def calculate_dispersion(self, phase: str='stare', save=True, show=False) -> None:
        """Calculate the dispersion of gaze data for each phase
        """
        phase_idx = self.phases.index(phase)
        gaze = self.gaze_data[phase_idx]

        # Get the standard deviate of the gaze data along each dimension
        self.mean_gaze = np.mean(gaze, axis=0)
        self.dispersion_x = np.std(gaze[:, 0])
        self.dispersion_y = np.std(gaze[:, 1])

        # Draw ellipsoid of the dispersion
        plt.figure()
        plt.title(f"Dispersion of {phase} data")
        plt.plot(gaze[:, 0], gaze[:, 1])
        plt.plot(self.mean_gaze[0], self.mean_gaze[1], '.k')
        ellipse = Ellipse((self.mean_gaze), self.dispersion_x, self.dispersion_y, fill=False, color='r')
        plt.gca().add_patch(ellipse)

        if save is True:
            plt.savefig(f'{self.file[:-4]}_{phase}_dispersion.png', dpi=self.dpi)
        if show is True:
            plt.show()

        plt.clf()

    def calculate_frequency(self) -> None:
        """Calculate the nystagmus frequency of gaze data for each phase
        """

        for i in zip(self.gaze_data, self.phases):
            # Get the stare data from the gaze
            gaze, phase = i
            print(f'\tCalculating frequency for {phase} data')

            gaze_x, gaze_y = gaze[:, 0], gaze[:, 1]

            # Calculate the nystagmus frequency using the FFT of the gaze data
            N = len(gaze)
            T = 1 / self.sample_rate

            yf_x = np.abs(np.fft.fft(gaze[:, 0]))
            yf_x = yf_x[:int(N/2)]
            yf_y = np.abs(np.fft.fft(gaze[:, 1]))
            yf_y = yf_y[:int(N/2)]
            xf = np.fft.fftfreq(N, T)[:N//2]

            freq_idx = np.where((xf <= 5) & (xf > 0)) # cut of 0hz and above 5hz
            plt.plot(xf[freq_idx], yf_x[freq_idx])
            plt.plot(xf[freq_idx], yf_y[freq_idx])
            plt.legend(['x', 'y'])
            plt.title(f'Frequency decomposition of {phase} data')
            plt.ylabel('Power')
            plt.xlabel('Frequency (Hz)')
            plt.savefig(f'{self.file[:-4]}_{phase}_frequency.png', dpi=self.dpi)
            plt.clf()

    def plot(self, save=True, show=False) -> None:
        """Plot gaze data for each phase (and save it if wanted)
        """
        for gaze_data, phase in zip(self.gaze_data, self.phases):
            plt.plot(gaze_data[:, 0], gaze_data[:, 1], label=phase)
            plt.title(phase)
            if save is True:
                plt.savefig(f'{self.file[:-4]}_{phase}.png', dpi=self.dpi)
            if show is True:
                plt.show()
            plt.clf()
    
    def analyze(self) -> None:
        """Simple alias to run all of the calculations and plotting commands, since this 
           is the most common use case.
        """
        self.calculate_dispersion()
        self.calculate_distance()
        self.calculate_velocity()
        self.plot()