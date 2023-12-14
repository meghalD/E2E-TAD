import os

# Set the frame rate
fps = 10

# Set the directory containing the videos
video_dir = '/home/mdani31/akata-shared/datasets/USDet/404/' #for all videos use till USDet

# Set the directory to save the frames
frame_dir = '/home/mdani31/akata-shared/datasets/USDet/frames_{}fps'.format(fps)

# Loop through all the videos in the directory
for root, dirs, files in os.walk(video_dir):
    count =0
    for file in files:
        # Check if the file is a video file
        if file.endswith('.avi'):
            # Set the path to the video file
            video_path = os.path.join(root, file)
            # Set the path to the frame directory
            #frame_path = os.path.join(frame_dir, os.path.splitext(os.path.basename(root))[0])
            frame_path = os.path.join(frame_dir, root.split('/')[-2])
            # Create the frame directory if it does not exist
            if not os.path.exists(frame_path):
                os.makedirs(frame_path)
            # Set the ffmpeg command to extract frames
            #if file is from same folder then img_1%06d.jpg if video is 001.avi else img_%07d.jpg
            cmd = 'ffmpeg -i "{}" -vf fps={} "{}/img_{}%06d.jpg"'.format(video_path, fps, frame_path,count)
            # Execute the ffmpeg command
            ret_code = os.system(cmd)
            # Check if the ffmpeg command was executed successfully
            if ret_code == 0:
                # Create a file to indicate that frames were extracted
                count = count+1
                print('successfully extracted frames from {}'.format(video_path))

