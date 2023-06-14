#!/usr/bin/env python3

from BlazeposeRenderer import BlazeposeRenderer
import argparse
import pickle
import pandas as pd
import numpy as np

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
parser_renderer.add_argument("-o","--output", type=str, default="data", help="Path to output video file")
 

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

renderer = BlazeposeRenderer(
                tracker, 
                show_3d=args.show_3d, 
                output=args.output + ".mp4")

landmarks_world_list = []
landmarks_list = []
visibility_list = []
presence_list = []
xyzs = []


while True:
    # Run blazepose on next frame
    frame, body = tracker.next_frame()
    if frame is not None and body is not None:
        
        # Grab the relevant data from the Body data structure
        landmarks_list.append(body.landmarks)
        lms_world = body.landmarks_world.flatten()
        landmarks_world_list.append(lms_world)
        # visibility_list.append(body.visibility)
        # presence_list.append(body.presence)
        # xyzs.append(body.xyz)

        # Draw 2d skeleton
        frame = renderer.draw(frame, body)
        key = renderer.waitKey(delay=1)
        if key == 27 or key == ord('q'):
            break

# Make the csv file for this recording
col_labels = [str(i) for i in range(np.array(landmarks_world_list).shape[1])]
dynamic_gesture_df = pd.DataFrame(landmarks_world_list, columns=col_labels)
dynamic_gesture_df.to_csv(f"{args.output}.csv")

output_dict = {
    'landmarks' : landmarks_list,
    'landmarks_world' : landmarks_world_list,
    # 'visibility' : visibility_list,
    # 'presence' : presence_list,
    # 'xyzs' : xyzs
}

with open(args.output + ".pickle", "wb") as file:
    # pickle.dump(bodies, file, protocol=pickle.HIGHEST_PROTOCOL)
    pickle.dump(output_dict, file, protocol=pickle.HIGHEST_PROTOCOL)

renderer.exit()
tracker.exit()
