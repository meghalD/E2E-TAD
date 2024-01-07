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
import shutil

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
    rename('edf')
    #print('edf files renamed')
    rename('sync_event')
    rename('report')     
    
    # if an .avi file is found, merge them into one single video and name it as per its folder name
    merge_videos()
    return

def merge_videos():
    # read all the folders in /home/mdani31/akata-shared/datasets/USDet
    for folder in glob(DATA_DIR + '/*'):
        print(folder)
        folder_name = folder.split('/')[-1]
        print(folder_name)
        # check if the folder has .avi files
        if os.path.exists(folder + '/' + folder_name + '.avi'):
            print('avi file found')
            # check if there are multiple .avi files
            if len(glob(folder + '/*.avi')) > 1:
                print('multiple avi files found')
                # merge them into one single video
                os.system('ffmpeg -i concat:"{}/*.avi" -c copy {}/{}.mp4'.format(folder, ALL_VIDEOS_DIR, folder_name))
                # delete the multiple videos
                for file in glob(folder + '/*.avi'):
                    os.remove(file)
            else:
                print('single avi file found')
                # rename the single .avi file to folder_name.mp4
                os.rename(folder + '/' + folder_name + '.avi', ALL_VIDEOS_DIR + folder_name + '.mp4')
        elif os.path.exists(folder + '/' + folder_name + '.mp4'):
            print('mp4 file found')
            # check if there are multiple .mp4 files
            if len(glob(folder + '/*.mp4')) > 1:
                print('multiple mp4 files found')
                # merge them into one single video
                os.system('ffmpeg -i concat:"{}/*.mp4" -c copy {}/{}.mp4'.format(folder, ALL_VIDEOS_DIR, folder_name))
                # delete the multiple videos
                for file in glob(folder + '/*.mp4'):
                    os.remove(file)
            else:
                print('single mp4 file found')
                # rename the single .mp4 file to folder_name.mp4
                os.rename(folder + '/' + folder_name + '.mp4', ALL_VIDEOS_DIR + folder_name + '.mp4')
        else:
            print('no video file found')
            # if no video file is found, skip the folder
            continue
    #merging code


    # transfer it to a common main folder videos and delete the folder from where it was picked up
    return

def read_edf(edf_path):
    #read edf file 
    return

def read_txt(txt_path):
    #read txt file 
    return

def create_csv():
    #create csv file
    return

pseudoanonymize_patient_name()