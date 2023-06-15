from BlazeposeRenderer import BlazeposeRenderer
import argparse
import pickle
import pandas as pd
import numpy as np
import time
import datetime
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('-e', '--edge', action="store_true",
                    help="Use Edge mode (postprocessing runs on the device)")
parser_tracker = parser.add_argument_group("Tracker arguments")                 
parser_tracker.add_argument('-i', '--input', type=str, default="rgb", 
                    help="'rgb' or 'rgb_laconic' or path to video/image file to use as input (default=%(default)s)")
parser_tracker.add_argument("--pd_m", type=str,
                    help="Path to an .blob file for pose detection model")
parser_tracker.add_argument("--lm_m", type=str,
                    help="Landmark model ('full' or 'lite' or 'heavy') or path to an .blob file")
parser_tracker.add_argument('-xyz', '--xyz', action="store_true", default=True, 
                    help="Get (x,y,z) coords of reference body keypoint in camera coord system (only for compatible devices)")
parser_tracker.add_argument('-c', '--crop', action="store_true", 
                    help="Center crop frames to a square shape before feeding pose detection model")
parser_tracker.add_argument('--no_smoothing', action="store_true", 
                    help="Disable smoothing filter")
parser_tracker.add_argument('-f', '--internal_fps', type=int, 
                    help="Fps of internal color camera. Too high value lower NN fps (default= depends on the model)")                    
parser_tracker.add_argument('--internal_frame_height', type=int, default=640,                                                                                    
                    help="Internal color camera frame height in pixels (default=%(default)i)")                    
parser_tracker.add_argument('-s', '--stats', action="store_true", 
                    help="Print some statistics at exit")
parser_tracker.add_argument('-t', '--trace', action="store_true", 
                    help="Print some debug messages")
parser_tracker.add_argument('--force_detection', action="store_true", 
                    help="Force person detection on every frame (never use landmarks from previous frame to determine ROI)")

parser_renderer = parser.add_argument_group("Renderer arguments")
parser_renderer.add_argument('-3', '--show_3d', choices=[None, "image", "world", "mixed"], default=None,
                    help="Display skeleton in 3d in a separate window. See README for description.")


parser_renderer.add_argument("-o","--output", type=str, default="data", help="Name of the output data files")
 

args = parser.parse_args()

if args.edge:
    from BlazeposeDepthaiEdge import BlazeposeDepthai
else:
    from BlazeposeDepthai import BlazeposeDepthai
tracker = BlazeposeDepthai(input_src=args.input, 
            pd_model=args.pd_m,
            lm_model=args.lm_m,
            smoothing=not args.no_smoothing,   
            xyz=args.xyz,            
            crop=args.crop,
            internal_fps=args.internal_fps,
            internal_frame_height=args.internal_frame_height,
            force_detection=args.force_detection,
            stats=True,
            trace=args.trace)   

landmarks_world_list = []
visibility_list = []
presence_list = []
xyzs = []

now = datetime.datetime.now()
month = str(now.month).zfill(2)
day = str(now.day).zfill(2)
hour = str(now.hour).zfill(2)
minute = str(now.minute).zfill(2)
secs = str(now.second).zfill(2)
timestamp = f"{now.year}{month}{day}_{hour}{minute}{secs}"
data_dir = Path(__file__).cwd().resolve().joinpath(args.output + "_" + timestamp)
print(f"Data directory: {data_dir}")
data_dir.mkdir()

renderer = BlazeposeRenderer(
                tracker, 
                show_3d=args.show_3d, 
                output=str(data_dir.joinpath(args.output+".mp4")))

time.sleep(2)

while True:
    # Run blazepose on next frame
    frame, body = tracker.next_frame()
    if frame is not None and body is not None:
        
        # Grab the relevant data from the Body data structure
        lms_world = body.landmarks_world.flatten()
        landmarks_world_list.append(lms_world)
        visibility_list.append(body.visibility)
        presence_list.append(body.presence)
        xyzs.append(body.xyz)

        # Draw 2d skeleton
        frame = renderer.draw(frame, body)
        key = renderer.waitKey(delay=1)
        if key == 27 or key == ord('q'):
            break

# Make the csv file for this recording
landmark_col_labels = [str(i) for i in range(np.array(landmarks_world_list).shape[1])]
dynamic_gesture_df = pd.DataFrame(landmarks_world_list, columns=landmark_col_labels)
gesture_out_path = data_dir.joinpath(args.output+"_landmarks.csv")
dynamic_gesture_df.to_csv(gesture_out_path)

# Probability of keypoints that exist and are *not* occluded
gesture_vis_col_labels = [str(i) for i in range(np.array(visibility_list).shape[1])]
gesture_visibility_df = pd.DataFrame(visibility_list, columns=gesture_vis_col_labels)
vis_out_path = data_dir.joinpath(args.output+"_visibility.csv")
gesture_visibility_df.to_csv(vis_out_path)

# Probability of keypoints that exist in the frame
gesture_pres_col_labels = [str(i) for i in range(np.array(presence_list).shape[1])]
gesture_presence_df = pd.DataFrame(presence_list, columns=gesture_pres_col_labels)
presence_out_path = data_dir.joinpath(args.output + "_presence.csv")
gesture_presence_df.to_csv(presence_out_path)

# Store the human's center xyz estimate
xyz_labels = ['x','y','z']
xyz_df = pd.DataFrame(xyzs, columns=xyz_labels)
xyz_out_path = data_dir.joinpath(args.output + "_xyz.csv")
xyz_df.to_csv(xyz_out_path)


# output_dict = {
#     'visibility' : visibility_list,
#     'presence' : presence_list,
# }
# with open(args.output + ".pickle", "wb") as file:
#     pickle.dump(output_dict, file, protocol=pickle.HIGHEST_PROTOCOL)

renderer.exit()
tracker.exit()
