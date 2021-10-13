from io import TextIOWrapper
import pygame
from pygame.locals import *
from pylsl import StreamOutlet, StreamInfo
from datetime import datetime
import os
import random
import socket
import numpy as np
from time import sleep
from LabRecorderCLI import LabRecorderCLI

'''
TODO: 
 - Fix the way we call LabRecorder. seems very janky and not very reliable.
'''

"""
Main function for the program
"""
DEBUG_FLAG = False
def main():
    random.seed()

    # Setup the outgoing LSL stream - this is the flags stream to mark which task is being performed
    outlet.push_sample(['stimulus_begin'])

    # Initialization of PyGame
    pygame.init()
    window_w = pygame.display.Info().current_w
    window_h = pygame.display.Info().current_h
    size = WIDTH, HEIGHT = window_w, window_h
    screen = pygame.display.set_mode(size=size, flags=pygame.FULLSCREEN | pygame.HWSURFACE) # 
    pygame.mouse.set_visible(False)
    pygame.display.flip()
    pygame.display.set_caption("Stimulus Presentation")
    surface = pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA) # For drawing transparent circles
    FPS = 60 
    clock = pygame.time.Clock()
    clock.tick(FPS)

    # PyGame font 
    pygame.font.init()
    font = pygame.font.SysFont('courier.ttf', 36)

    # Constants
    BRIGHTNESS_TRIAL_LENGTH = 10 # This can be shorter than the main trial length
    SCREEN_CENTRE = (WIDTH/2, HEIGHT/2)
    STIM_ORDER = ['stare', 'pursuit', 'vor', 'jump', 'brightness']
    #STIM_ORDER = ['brightness', 'vor']
    
    '''
    Main execution loop
    '''
    RUNNING = True # Flag to turn off the program
    while RUNNING is True:
        # Handle quitting events ... gracefully ... ish
        for event in pygame.event.get():
            if (event.type == KEYDOWN and event.key == K_ESCAPE) or (event.type == pygame.QUIT):
                RUNNING = False
                print("Quitting ...")
                pygame.quit()
                exit()
            
        def clear_screen():
            '''
            Inline:
            Resets the screen to black
            '''
            screen.fill((0,0,0))
            surface.fill((0,0,0))   
        
        def draw_fixation_cross(centre=SCREEN_CENTRE, color=(255,255,255)):
            '''
            Inline:
            Draw a white cross at the centre of the coordinates given
            You can change the color by passing a tuple of colors in RGB
            '''
            LINE_LENGTH = 10
            start_pos_h = (centre[0], centre[1]-LINE_LENGTH)
            end_pos_h = (centre[0], centre[1]+LINE_LENGTH)
            start_pos_v = (centre[0]-LINE_LENGTH, centre[1])
            end_pos_v = (centre[0]+LINE_LENGTH, centre[1])

            # Draw the cross
            pygame.draw.line(screen, color, start_pos_h, end_pos_h, 4)
            pygame.draw.line(screen, color, start_pos_v, end_pos_v, 4)

        # Let the experimenter know the stimulus is loaded and up and running
        text = font.render("Stimulus loaded. Press space to begin ...", True, (255, 255, 255))
        txt_rect = text.get_rect(center=(WIDTH/2, HEIGHT/2 - 0.4*HEIGHT))
        screen.blit(text, txt_rect)

        pygame.display.flip()
        wait_for_space()
        clear_screen()
        
        for stim in STIM_ORDER:
            ''' 
            TRIAL TYPE   :      DESCRIPTION
            stare        :      pt stares at the target in the centre of the screen for duration      
            pursuit      :      pt follows target with eyes as it moves left / right for duration
            far          :      pt looks at target at each of the extremities
            vor          :      pt locks gaze and rotates head. will almost certainly need demonstration
            jump         :      pt follows target. it will jump left / right.
            brightness   :      pt looks at target and holds gaze for few seconds. brightness inverts.
            '''
            clear_screen()
            # NOTE: This is debug info - set using $DEBUG_FLAG
            if DEBUG_FLAG:
                img = font.render(stim, True, (255, 255, 255))
                txt_rect = img.get_rect(center=(WIDTH/2, HEIGHT/2 - 0.4*HEIGHT))
                screen.blit(img, txt_rect)
            
            '''
            Stare condition
            '''
            if stim == 'stare':
                # NOTE: This draws a dot on the screen for 20s, then ends. Very simple.
                STARE_TIME = 20 # seconds
                STARE_FRAMES = STARE_TIME * FPS

                print(str(stim))
                outlet.push_sample([stim])
                draw_fixation_cross()
                pygame.display.flip()

                for _ in range(0, STARE_FRAMES):
                    clock.tick(FPS)

            '''
            Pursuit condition
            '''
            if stim == 'pursuit':
                # NOTE: Draws a dot and moves left / right for ~20s.
                # NOTE: left/right left-hold 5 right-hold 5
                # NOTE: do the same for up/down
                print(stim)
                outlet.push_sample([stim])
                #create_data_csv(stim)

                # Extremes for how far our dot can move
                L_EDGE = WIDTH * 0.1          
                R_EDGE = WIDTH - (WIDTH * 0.1)
                T_EDGE = HEIGHT * 0.1
                B_EDGE = HEIGHT - (HEIGHT * 0.1)
                CENTRE_X = WIDTH / 2
                CENTRE_Y = HEIGHT / 2

                # Dot parameters
                TARG_SIZE = 20  # pixels
                HOLD_TIME = 3   # seconds
                TRAVEL_TIME = 2 # seconds ( to get to the end position at a constant velocity )
                TRAVEL_FRAMES = TRAVEL_TIME * FPS
                ONE_SEC_FRAMES = FPS
                HOLD_FRAMES = HOLD_TIME * FPS
                HOLD_FLAG = False
                order = ('left', 'right_centre', 'right', 'left_centre',
                         'left_hold', 'right_centre', 'right_hold', 'left_centre', 
                         'top', 'bottom_centre', 'bottom', 'top_centre',
                         'top_hold', 'bottom_centre', 'bottom_hold', 'top_centre')
                
                for dir in order:
                    # Push the sample over LSL
                    outlet.push_sample(["pursuit_" + dir + "_start"])
                    print("\t-" + dir + ":" + str(HOLD_FLAG))
                    HOLD_FLAG = False # hard reset

                    if "_hold" in dir:
                        HOLD_FLAG = True
                    else:
                        HOLD_FLAG = False

                    if dir == 'left':
                        '''
                        Move to the left from centre
                        '''
                        # Calculate the X values before hand since we can't move sub-pixel at a time
                        pos_trajectory_x = np.round(np.linspace(CENTRE_X, L_EDGE, TRAVEL_FRAMES))
                        pos_trajectory_y = np.ones(len(pos_trajectory_x)) * CENTRE_Y
                        pos = [pos_trajectory_x, pos_trajectory_y]
                        HOLD_FLAG = False

                    if dir == 'right_centre':
                        '''
                        Move back to centre rightwards
                        '''
                        # Calculate the X values before hand since we can't move sub-pixel at a time
                        pos_trajectory_x = np.round(np.linspace(L_EDGE, CENTRE_X, TRAVEL_FRAMES))
                        pos_trajectory_y = np.ones(len(pos_trajectory_x)) * CENTRE_Y
                        pos = [pos_trajectory_x, pos_trajectory_y]

                    if dir == 'right':
                        '''
                        Move to the right from centre
                        '''
                        # Calculate the X values before hand since we can't move sub-pixel at a time
                        pos_trajectory_x = np.round(np.linspace(CENTRE_X, R_EDGE, TRAVEL_FRAMES))
                        pos_trajectory_y = np.ones(len(pos_trajectory_x)) * CENTRE_Y
                        pos = [pos_trajectory_x, pos_trajectory_y]

                    if dir == 'left_centre':
                        '''
                        Move back to centre leftwards
                        '''
                        # Calculate the X values before hand since we can't move sub-pixel at a time
                        pos_trajectory_x = np.round(np.linspace(R_EDGE, CENTRE_X, TRAVEL_FRAMES))
                        pos_trajectory_y = np.ones(len(pos_trajectory_x)) * CENTRE_Y
                        pos = [pos_trajectory_x, pos_trajectory_y]

                    if dir == 'left_hold':
                        '''
                        Go to the leftmost side and hold for $HOLD_TIME (default: 3) seconds
                        '''
                        # Calculate the X values before hand since we can't move sub-pixel at a time
                        pos_trajectory_x = np.round(np.linspace(CENTRE_X, L_EDGE, TRAVEL_FRAMES))
                        pos_trajectory_y = np.ones(len(pos_trajectory_x)) * CENTRE_Y
                        pos = [pos_trajectory_x, pos_trajectory_y]

                    if dir == 'right_hold':
                        # Calculate the X values before hand since we can't move sub-pixel at a time
                        pos_trajectory_x = np.round(np.linspace(CENTRE_X, R_EDGE, TRAVEL_FRAMES))
                        pos_trajectory_y = np.ones(len(pos_trajectory_x)) * CENTRE_Y
                        pos = [pos_trajectory_x, pos_trajectory_y]

                    if dir == 'top':
                        '''
                        Move to the top from centre
                        '''
                        # Calculate the X values before hand since we can't move sub-pixel at a time
                        pos_trajectory_y = np.round(np.linspace(CENTRE_Y, T_EDGE, TRAVEL_FRAMES))
                        pos_trajectory_x = np.ones(len(pos_trajectory_y)) * CENTRE_X
                        pos = [pos_trajectory_x, pos_trajectory_y]

                    if dir == 'bottom_centre':
                        '''
                        Move to the centre downwards from the top
                        '''
                        # Calculate the X values before hand since we can't move sub-pixel at a time
                        pos_trajectory_y = np.round(np.linspace(T_EDGE, CENTRE_Y, TRAVEL_FRAMES))
                        pos_trajectory_x = np.ones(len(pos_trajectory_y)) * CENTRE_X
                        pos = [pos_trajectory_x, pos_trajectory_y]

                    if dir == 'bottom':
                        '''
                        Move to the bottom from the centre
                        '''
                        # Calculate the X values before hand since we can't move sub-pixel at a time
                        pos_trajectory_y = np.round(np.linspace(CENTRE_Y, B_EDGE, TRAVEL_FRAMES))
                        pos_trajectory_x = np.ones(len(pos_trajectory_y)) * CENTRE_X
                        pos = [pos_trajectory_x, pos_trajectory_y]

                    if dir == 'top_centre':
                        '''
                        Move to the centre from bottom upwards
                        '''
                        # Calculate the X values before hand since we can't move sub-pixel at a time
                        pos_trajectory_y = np.round(np.linspace(B_EDGE, CENTRE_Y, TRAVEL_FRAMES))
                        pos_trajectory_x = np.ones(len(pos_trajectory_y)) * CENTRE_X
                        pos = [pos_trajectory_x, pos_trajectory_y]

                    if dir == 'top_hold':
                        '''
                        Move to the top upwards and hold
                        '''
                        # Calculate the X values before hand since we can't move sub-pixel at a time
                        pos_trajectory_y = np.round(np.linspace(CENTRE_Y, T_EDGE, TRAVEL_FRAMES))
                        pos_trajectory_x = np.ones(len(pos_trajectory_y)) * CENTRE_X
                        pos = [pos_trajectory_x, pos_trajectory_y]
                            

                    if dir == 'bottom_hold':
                        '''
                        Move to the bottom downwards and hold
                        '''
                        # Calculate the X values before hand since we can't move sub-pixel at a time
                        pos_trajectory_y = np.round(np.linspace(CENTRE_Y, B_EDGE, TRAVEL_FRAMES))
                        pos_trajectory_x = np.ones(len(pos_trajectory_y)) * CENTRE_X
                        pos = [pos_trajectory_x, pos_trajectory_y]

                    ''' 
                    Animate the dot
                    '''
                    for f in range(0, TRAVEL_FRAMES):
                            curr_pos = (int(pos[0][f]), int(pos[1][f]))
                            pygame.draw.circle(screen, (255,255,255), curr_pos, TARG_SIZE, 0)
                            pygame.display.flip()
                            clear_screen()
                            clock.tick(FPS)

                    # Check if we should hold
                    if HOLD_FLAG is True:
                        for _ in range(0, int(HOLD_FRAMES)):
                            clock.tick(FPS)
                    elif HOLD_FLAG is False:
                        for _ in range(0, int(ONE_SEC_FRAMES/2)):
                            clock.tick(FPS)
                        

                    outlet.push_sample(["pursuit_" + dir + "_end"])
        
            '''
            VOR condition
            DONE for now
            '''       
            if stim == 'vor':
                # NOTE: Patient keeps gaze steady on target, rotates head while maintaining fixation. Same as 'stare'
                #VOR_TIME = 20 # seconds
                #VOR_FRAMES = VOR_TIME * FPS

                print(stim)
                outlet.push_sample([stim])
                #create_data_csv(stim)
                draw_fixation_cross()
                pygame.display.flip()

                #for _ in range(0, VOR_FRAMES):
                    #clock.tick(FPS)
                
                # The user picks how long they want to do this one
                wait_for_space()

            '''
            Jump condition
            DONE for now
            '''
            if stim == 'jump':
                # NOTE: Target appears on left, then disappears and reappears on the right.
                
                print(stim)
                outlet.push_sample([stim])
                #create_data_csv(stim)
                draw_fixation_cross()

                # Order of where the stimulus hops to
                MIN_S = 0.5
                MAX_S = 1.5
                order = ('cross', 'left', 'cross', 'right', 'cross', 'left', 'cross', 'right', 'cross', 'left', 'cross', 'right', 'cross', 'left', 'cross', 'right', 'cross')
                N_JUMPS = len(order)
                target_times = [random.uniform(MIN_S, MAX_S) for i in range(N_JUMPS)]
                target_times[0] = 3 # first one should be 3s
                #target_times = (3, random.uniform(MIN_S, MAX_S), random.uniform(MIN_S, MAX_S), random.uniform(MIN_S, MAX_S), random.uniform(MIN_S, MAX_S), random.uniform(MIN_S, MAX_S), random.uniform(MIN_S, MAX_S), random.uniform(MIN_S, MAX_S), random.uniform(MIN_S, MAX_S), random.uniform(MIN_S, MAX_S), random.uniform(MIN_S, MAX_S), random.uniform(MIN_S, MAX_S), random.uniform(MIN_S, MAX_S), random.uniform(MIN_S, MAX_S), random.uniform(MIN_S, MAX_S))                
                # At the beginning, there is a 3s buffer time to when the target first appears on the left. 
                # They will need to fixate on the target cross, and a dot will show up.
                # After that the target will appear to 2s, then the subject shifts back to the centre cross for ~3s.
                # Then a target shows up on the right for 2s
                for i in range(0, len(order)):
                    if order[i] == 'cross':
                        outlet.push_sample(['jump_cross'])
                        draw_fixation_cross()

                    if order[i] == 'left':
                        outlet.push_sample(['jump_left'])
                        pygame.draw.circle(screen, (255,255,255), (int(WIDTH/20), int(HEIGHT/2)), 20)

                    if order[i] == 'right':
                        outlet.push_sample(['jump_right'])
                        pygame.draw.circle(screen, (255,255,255), (int(WIDTH-WIDTH/20), int(HEIGHT/2)), 20)
                    
                    pygame.display.flip()
                    # Hold it for however long target_times[i] says
                    jump_start_time = pygame.time.get_ticks()
                    while (pygame.time.get_ticks() - jump_start_time) / 1000 <= target_times[i]:
                        pass
                    
                    clear_screen()

                pygame.draw.circle(surface, (255,255,255), (int(WIDTH/2), int(HEIGHT/2)), 20, 0)
                pygame.display.flip()

            
            '''
            Brightness condition
            DONE
            '''
            if stim == 'brightness':
                print(stim)

                BRIGHTNESS_FRAMES = BRIGHTNESS_TRIAL_LENGTH * FPS

                outlet.push_sample([stim])
                #create_data_csv(stim)
                draw_fixation_cross()

                for i in range(0, BRIGHTNESS_FRAMES):
                    clock.tick(FPS)
                    if i >= BRIGHTNESS_FRAMES/2:
                        screen.fill((255, 255, 255))
                        draw_fixation_cross(color=(0,0,0))
                    if i == BRIGHTNESS_FRAMES/2:
                        print("\t-brightness_high")
                        outlet.push_sample(["brightness_high"])
                    
                    pygame.display.flip()

            if stim == 'brightness':
                img = font.render("Trial over! Hit spacebar to continue.", True, (0, 0, 0))  
            else:
                img = font.render("Trial over! Hit spacebar to continue.", True, (255, 255, 255))   
                
            txt_rect = img.get_rect(center=(WIDTH/2, HEIGHT/2 + 0.4*HEIGHT))
            screen.blit(img, txt_rect)
            pygame.display.flip()
            outlet.push_sample([stim + "_end"])
            wait_for_space()

        # Kill the program
        RUNNING = False

def wait_for_space():
    ''' 
    Simply wait for the user to press the spacebar before continuing.
    Used between trials.
    '''
    KEY_NOT_PRESSED = True
    while KEY_NOT_PRESSED:
        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_SPACE:
                KEY_NOT_PRESSED = False

def generate_subject_name(date: datetime):
    '''
    Generate a subject name based on the current date / time
    '''
    return "pt_" + str(date.year) + "-" + str(date.month) + "-" + str(date.day) + "_" + str(date.hour) + "-" + str(date.minute) + "-" +  str(date.second)

def create_data_csv(name):
    '''
    Create the individual CSV for each trial - just named after the phase the pt is currently on
    '''
    header = ('confidence', 'norm_pos_x', 'norm_pos_y', 
              'gaze_point_3d_x', 'gaze_point_3d_y', 'gaze_point_3d_z',
              'eye_0_center_x', 'eye_0_center_y', 'eye_0_center_z', 
              'eye_1_center_x', 'eye_1_center_y', 'eye_1_center_z',
              'gaze_normal_3d_eye_0_x', 'gaze_normal_3d_eye_0_y', 'gaze_normal_3d_eye_0_z',
              'gaze_normal_3d_eye_1_x', 'gaze_normal_3d_eye_1_y', 'gaze_normal_3d_eye_1_z',
              'diameter_2d_eye_0', 'diameter_2d_eye_1', 
              'diameter_3d_eye_0', 'diameter_3d_eye_1')
    file_name = "data/" + subject_name + "/" + name + ".csv"
    file = open(file_name, 'a')
    file.write(",".join(header));
    file.write("\n")
    return file

def write_data_csv(file: TextIOWrapper, data):
    '''
    Convert the data in the LSL inlet to a CSV friendly string format and write to file
    '''
    file.write(",".join(map(str, data)))
    file.write("\n")
    return 1

if __name__ == '__main__':
    # Do some house cleaning around the current subject
    # Create their folder in the "data/" directory
    if not os.path.exists('data'):
        print("Warning! No data folder found. Creating one ...")
        os.mkdir("data")

    subject_name = generate_subject_name(datetime.now())
    os.mkdir("data/" + subject_name)
    print("Created subject folder " + subject_name + "/ in data/")

    # LSL outlet
    info = StreamInfo('Stimulus_Markers', 'Markers', 1, 0, 'string', 'stim-prog-1')
    outlet = StreamOutlet(info)
    print("Setting up LSL stream ..")

    # Name of participant
    wd = os.getcwd() + "\\data\\" + subject_name + "\\" + subject_name + ".xdf "
    cli_arg = "\"name=\"\"{0}\"\"\"".format("Stimulus_Markers")
    lsl_args = wd + cli_arg
    streams = "type='Markers' type'Gaze'"

    LR = LabRecorderCLI("./LabRecorderCLI.exe")
    LR.start_recording(filename=wd, streams=streams)  

    print("Started recording on LabRecorder ...")

    # Check if consumer is connected
    outlet.wait_for_consumers(3)
    while outlet.have_consumers() is False:
        print("Waiting for connection ...")
        sleep(1)
    
    # Run the main script
    print('Starting PyGame backend ...')
    main() # Main entry point
    outlet.push_sample(['stimulus_end'])
    
    # Stop recording
    print("Stopping LSL recording ...")
    LR.stop_recording()
    sleep(0.5)
