import liesl
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from matplotlib.patches import Ellipse

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
        self.data = liesl.XDFFile(file)
        self.phases = phases # default to None
        self.dpi = dpi

        self._pull_data()
        self._find_start_end_phase_indices()
        self._convert_idx_to_timestamps()
        self._get_gaze_data()
        self._get_gaze_by_phase()

    def _verify_integrity(self) -> None:
        return NotImplementedError

    def _pull_data(self) -> None:
        """Pull the data from the file and store it
        """
        self.markers = self.data[self.stimulus_marker_name]
        if self.phases is None:
            self.phases = ['stare','pursuit','vor', 'jump', 'brightness']
        self.phase_starts = ['stare','pursuit','vor', 'jump', 'brightness']
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
            self.gaze_data.append(self.gaze.time_series[idx[0]:idx[1], 1:3])

    def calculate_velocity(self, save=True, show=False):
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

        # Function that calculates the distance between two points
        def _distance(x1, y1, x2, y2):
            return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

        self.distances = []
        for gaze_data in self.gaze_data:
            distance = 0
            for gaze_idx in range(len(gaze_data) - 1):
                distance += _distance(gaze_data[gaze_idx, 0], gaze_data[gaze_idx, 1],
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
        plt.title("Dispersion of Stare data")
        plt.plot(gaze[:, 0], gaze[:, 1])
        plt.plot(self.mean_gaze[0], self.mean_gaze[1], '.k')
        ellipse = Ellipse((self.mean_gaze), self.dispersion_x, self.dispersion_y, fill=False, color='r')
        plt.gca().add_patch(ellipse)

        if save is True:
            plt.savefig(f'{self.file[:-4]}_stare_dispersion.png', dpi=self.dpi)
        if show is True:
            plt.show()

        plt.clf()

    def plot(self, save=True, show=False) -> None:
        """Plot gaze data for each phase (and save it if wanted)
        """
        for gaze_data, phase in tqdm(zip(self.gaze_data, self.phases), total=len(self.phases)):
            plt.plot(gaze_data[:, 0], gaze_data[:, 1], label=phase)
            plt.title(phase)
            if save is True:
                plt.savefig(f'{self.file[:-4]}_{phase}.png', dpi=self.dpi)
            if show is True:
                plt.show()
            plt.clf()