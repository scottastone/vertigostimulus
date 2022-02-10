from analyzer import Analyzer

def main():
    analyzer = Analyzer('data\pt_2022-2-3_11-49-58\pt_2022-2-3_11-49-58_R001.xdf',
                         stimulus_marker_name='Stimulus_Markers',
                         gaze_name='TobiiGaze')
    analyzer._verify_integrity()
    analyzer.calculate_distance()
    analyzer.calculate_dispersion()
    analyzer.calculate_velocity()
    analyzer.plot()

if __name__ == '__main__':
    main()