
"""
record.py
---------------

Main Function for recording a video sequence into cad (color-aligned-to-depth) 
images and depth images

This code is compatible with legacy camera models supported on librealsense SDK v1
and use 3rd party python wrapper https://github.com/toinsson/pyrealsense

For the newer D series cameras, please use record2.py


"""

# record for 30s after a 5s count down
# or exit the recording earlier by pressing q

RECORD_LENGTH = 30

import png
import json
import logging
logging.basicConfig(level=logging.INFO)
import numpy as np
import cv2
from primesense import openni2
import time
import os
import sys

def make_directories(folder):
    if not os.path.exists(folder+"JPEGImages/"):
        os.makedirs(folder+"JPEGImages/")
    if not os.path.exists(folder+"depth/"):
        os.makedirs(folder+"depth/")

def print_usage():
    
    print("Usage: record.py <foldername>")
    print("foldername: path where the recorded data should be stored at")
    print("e.g., record.py LINEMOD/mug")
    

if __name__ == "__main__":
    try:
        folder = sys.argv[1]+"/"
    except:
        print_usage()
        exit()

    make_directories(folder)
    # save_color_intrinsics(folder)
    FileName=0
    openni2.initialize("/home/zyf/src/OpenNI-Linux-x64-2.3.0.66/Redist/")
    dev = openni2.Device.open_any()

    depth_stream = dev.create_depth_stream()
    depth_stream.start()

    cap = cv2.VideoCapture(0)

    # Save color intrinsics to the corresponding folder
    # https://github.com/Riotpiaole/rgbd
    camera_parameters = {'fx': 553.797, 'fy': 553.722,
                            'ppx': 320, 'ppy': 240,
                            'height': 480, 'width': 640,
                            'depth_scale':0.001}

    with open(folder+'intrinsics.json', 'w') as fp:
        json.dump(camera_parameters, fp)

    # Set frame rate
    cnt = 0
    last = time.time()
    smoothing = 0.9
    fps_smooth = 30
    T_start = time.time()
    
    
    while True:
        cnt += 1
        if (cnt % 10) == 0:
            now = time.time()
            dt = now - last
            fps = 10/dt
            fps_smooth = (fps_smooth * smoothing) + (fps * (1.0-smoothing))
            last = now
        _, c = cap.read()
        # d = dev.dac
        frame = depth_stream.read_frame()
        dframe_data = np.array(frame.get_buffer_as_triplet()).reshape([480, 640, 2])
        dpt1 = np.asarray(dframe_data[:, :, 0], dtype='uint16')
        dpt2 = np.asarray(dframe_data[:, :, 1], dtype='uint16')
        dpt2 *= 255
        d = cv2.flip(dpt1 + dpt2,1)

        
        # Visualize count down
    
        if time.time() -T_start > 5:
            filecad= folder+"JPEGImages/%s.jpg" % FileName
            filedepth= folder+"depth/%s.png" % FileName
            cv2.imwrite(filecad,c)
            with open(filedepth, 'wb') as f:
                writer = png.Writer(width=d.shape[1], height=d.shape[0],
                                    bitdepth=16, greyscale=True)
                zgray2list = d.tolist()
                writer.write(f, zgray2list)

            FileName+=1
            
        if time.time() -T_start > RECORD_LENGTH + 5:
            dev.close()
            depth_stream.stop()
            break

        if time.time() -T_start < 5:
            cv2.putText(c,str(5-int(time.time() -T_start)),(240,320), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 4,(0,0,255),2,cv2.LINE_AA)
        if time.time() -T_start > RECORD_LENGTH:
            cv2.putText(c,str(RECORD_LENGTH+5-int(time.time()-T_start)),(240,320), cv2.FONT_HERSHEY_SCRIPT_SIMPLEX, 4,(0,0,255),2,cv2.LINE_AA)
        cv2.imshow('COLOR FRAME',c)
        
    
            
        # press q to quit the program
        if cv2.waitKey(1) & 0xFF == ord('q'):
            dev.close()
            depth_stream.stop()
            break

    # Release everything if job is finished
    cv2.destroyAllWindows()
