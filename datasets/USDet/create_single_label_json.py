#read USDet_edf_info_all.csv and load all columns into a dataframe
import pandas as pd
import os
from typing import List, Dict, Tuple
from dataclasses import dataclass

csv_data_dir = '/home/mdani31/akata-shared/datasets/USDet/'

df = pd.read_csv('USDet_edf_info_all.csv')
print(df.head())
print(df.columns)

#@dataclass
class Data_Annotation:
    start: float = 0.0
    end: float = 0.0
    label: str = ''

    @property
    def segment(self) -> List[float]:
        return [self.start, self.end]

#@dataclass
class Video_Details:
    id: int 
    subset: str = ''
    fps: int = 30
    duration: float = 150.0
    annotations: List[List[Data_Annotation]]= []

#@dataclass
class Sezdet_Data:    
    #use this for single_label
    classes: List[str] = ['Seizure', 'Non-Seizure']
    database: List[Video_Details] = []


sezdet_data = Sezdet_Data()

# filter rows with 'AB_EEG_SL': first occurence is start of seizure, second occurence is end of seizure
filtered_df = df[df['EEG Annotation'].str.startswith(('AB_EEG_SL')) | df['EEG Annotation'].str.startswith(('AE_EEG_SL'))]
print(filtered_df)
#get unique video ids
unique_video_ids = filtered_df['Video_ID'].unique()

#loop through unique video ids
for video_id in unique_video_ids:
    #create a Video_Details object
    video_det = Video_Details()
    list_annotations = []
    #filter the dataframe for the video id
    vid_filter_df = filtered_df[filtered_df['Video_ID']==video_id]

    #add to Video_Details object
    video_det.id = video_id
    video_det.subset = filtered_df['subset'].iloc[0]

    data_annotation = Data_Annotation()
    #add Non-Seizure annotation before first Seizure annotation
    data_annotation.label = 'Non-Seizure'
    data_annotation.start = 0.0
    data_annotation.end = filtered_df['Video time'].iloc[0] 
    list_annotations.append(data_annotation)

    #add Seizure annotation
    data_annotation = Data_Annotation()
    data_annotation.label = 'Seizure'
    data_annotation.start = filtered_df['Video time'].iloc[0]
    data_annotation.end = filtered_df['Video time'].iloc[1]
    list_annotations.append(data_annotation)

    #add Non-Seizure annotation after the Seizure annotation
    data_annotation = Data_Annotation()
    data_annotation.label = 'Non-Seizure'
    data_annotation.start = filtered_df['Video time'].iloc[1]
    #find last occurence of the video id
    data_annotation.end = df[df['Video_ID']==video_id]['Video time'].iloc[-1]
    list_annotations.append(data_annotation)

    #append the Data_Annotation object to the Video_Details object
    video_det.annotations.append(list_annotations)

    #append the Video_Details object to the Sezdet_Data object
    sezdet_data.database.append(video_det)
    print(sezdet_data.database)



##################################################DATA FORMAT##################################################
#form a dictionary from the Sezdet_Data object such that the heirarchy is maintained as follows:
# {'classes': ['Seizure', 'Non-Seizure'],
#  'database': {'video_id_1':{
#         'subset': 'train',
#         'fps': 30,
#         'duration': 150,
#         'annotations': [{'label': 'Seizure', 'segment': [0.0, 5.0]},
#                         {'label': 'Non-Seizure', 'segment': [5.0, 10.0]}]
#  },
#             'video_id_2':{  
#         'subset': 'train',
#         'fps': 30,
#         'duration': 150,
#         'annotations': [{'label': 'Seizure', 'segment': [0.0, 5.0]},
#                         {'label': 'Non-Seizure', 'segment': [5.0, 10.0]}]
#             }
#  }}
    
sezdet_data_dict = {'classes': sezdet_data.classes, 'database': {}}
#loop over the database list in sezdet_data with index
for idx, video_det in enumerate(sezdet_data.database):
    video_id = str(video_det.id)
    sezdet_data_dict['database'][video_id] = {'subset': video_det.subset, 'fps': video_det.fps, 'duration': video_det.duration, 'annotations': []}
    for annotation in video_det.annotations[idx]:
        sezdet_data_dict['database'][video_id]['annotations'].append({'label': annotation.label, 'segment': annotation.segment})

#save as json
import json

#use this for single_label
with open('sezdet_data_single.json', 'w') as fp:
    json.dump(sezdet_data_dict, fp, indent=4)
