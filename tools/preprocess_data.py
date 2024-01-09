#Preprocess the data

#Step 1: PseudoAnonymization of patient name 

#Step 2: we write this code to read the folders from '/home/mdani31/akata-shared/datasets/USDet' 
# in each subfolder we find all .avi / .mp4 files and merge them into one single video
# once done we remove multiple videos

#Step 2.5: Transfer all videos to a single folder names 'videos'

#Step 3: create a .csv file after reading .txt for sync event and .edf for seizure event

#Step 4: create a .json file for each video with the following format
# call create single label json file

import os
from glob import glob
import pyedflib
import datetime
import subprocess

ALL_VIDEOS_DIR = '/home/mdani31/akata-shared/datasets/USDet/videos/'
ALL_EDF_DIR = '/home/mdani31/akata-shared/datasets/USDet/edf/'
ALL_SYNC_EVENT_DIR = '/home/mdani31/akata-shared/datasets/USDet/sync_event/'
ALL_REPORT_DIR = '/home/mdani31/akata-shared/datasets/USDet/reports/'
DATA_DIR = '/home/mdani31/akata-shared/datasets/USDet/data'

def rename(file_type):
    if file_type == 'edf':
        extension = '.edf'
        FILE_DIR = ALL_EDF_DIR
    elif file_type == 'sync_event':
        extension = 'ent.txt' # as some files have syncevent.txt and some have SyncEvent.txt. To avoid case issue
        FILE_DIR = ALL_SYNC_EVENT_DIR
    elif file_type == 'report':
        extension = 'Text.txt'
        FILE_DIR = ALL_REPORT_DIR
    else:
        print('Invalid file type')
        return
    
    if not os.path.exists(FILE_DIR):
        os.makedirs(FILE_DIR)

    for file in glob(DATA_DIR + '/**/*' + extension, recursive=True):
        print(file)
        folder_name = file.split('/')[-2]
        new_file_name = folder_name  + extension
        #os.shutil.copy(file, FILE_DIR+new_file_name)
        os.rename(file, FILE_DIR + new_file_name)

def pseudoanonymize_patient_name():
    # Step 1: PseudoAnonymization of patient name 
    # read all the folders in /home/mdani31/akata-shared/datasets/USDet
    
    #run these rename commands only once!
    rename('edf')
    rename('sync_event')
    rename('report')     
    
    # if an .avi file is found, merge them into one single video and name it as per its folder name
    merge_videos(DATA_DIR, ALL_VIDEOS_DIR)
    return

def merge_videos(input_folder, output_folder):
    for root, dirs, files in os.walk(input_folder): #change this to avoid going recursively in sub-folders
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            output_subfolder = os.path.join(output_folder, os.path.relpath(dir_path, input_folder))
            
            if not os.path.exists(output_subfolder):
                os.makedirs(output_subfolder)

            #check if there are subfolders in the folder
            subdirectories = [subdir for subdir in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, subdir)) and subdir.startswith(dir_name+"_FA")]
            
            if subdirectories:
                for subdirectory in subdirectories:
                    sub_dir_path = os.path.join(dir_path, subdirectory)
                    input_files = [file for file in glob(sub_dir_path + '/**/*.avi', recursive=True)]
                    
                    if input_files:
                        output_file = os.path.join(output_subfolder, f"{subdirectory}_merged.avi")
                        input_paths = [os.path.join(dir_path, f) for f in input_files]
                        
                        # Use ffmpeg to concatenate the videos
                        cmd = ["ffmpeg", "-i", f"concat:{'|'.join(input_paths)}", "-c", "copy", output_file]
                        #run only if the output file does not exist
                        if not os.path.exists(output_file):
                            subprocess.run(cmd)
                        print(f"Concatenated {len(input_files)} videos into {output_file}")

    # transfer it to a common main folder videos and delete the folder from where it was picked up
    return

def concat_time(dt1, dt2):
    d1 = datetime.datetime.strptime(dt1, "%H:%M:%S.%f")
    d2 = datetime.datetime.strptime(dt2, "%H:%M:%S.%f")
    dt1 = datetime.timedelta(minutes=d1.minute, seconds=d1.second, microseconds=d1.microsecond)
    dt2 = datetime.timedelta(minutes=d2.minute, seconds=d2.second, microseconds=d2.microsecond)
    fin = dt1 + dt2
    return str(fin)

def find_sync_event(video_id, eeg_sync_time):
    """
    This function finds the sync event time from the sync_event.txt file
    Input: video_id, eeg_sync_time
    Output: time gap between video and eeg
    """
    sync_event_file = ALL_SYNC_EVENT_DIR + video_id + 'ent.txt'

    #read and fetch video number and sync event time for that video
    with open(sync_event_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('V_' or 'v_'):
                video_num = line.split('_')[-1]
            #if lines mathes datetime pattern --:--:--.--- then it is the sync event time
            if line.startswith('--:--:--.---'):
                sync_event_time = line
    #find video in DATA_DIR and find the duration of all videos before that video
    video_duration = 0
    #get exact folder to look into
    main_folder = video_id.split('_')[0]
    sub_folder = video_id.split('.')[:-3]
    video_folder = os.path.join(DATA_DIR, main_folder, sub_folder)
    files_to_consider = []
    for glob_file in glob(video_folder + '/**/*.avi', recursive=True):
        if int(glob_file.split('_')[-1]) < int(video_num):
            files_to_consider.append(glob_file)

    return concat_time(eeg_sync_time, sync_event_time)


def read_edf(edf_path):
    #read edf files and save it in a csv file
    for file in glob(edf_path + '/**/*.edf', recursive=True):
        #define values to add to .csv file
        video_id = file.split('/')[-1].split('.')[0]
        video_subset = 'val'
        eeg_time = []
        eeg_annotation = []
        #find sync time from sync_event.txt for same file
        sync_time = read_txt(file)
        video_time = eeg_time + sync_time

        
        print(file)
        edf_file = pyedflib.EdfReader(file)
        annotations = edf_file.readAnnotations()
        print(annotations)
        edf_file.close()
    return

def read_txt(txt_path):
    #read txt file 
    return

def create_csv():
    #create csv file
    return

#pseudoanonymize_patient_name()
read_edf(ALL_EDF_DIR)