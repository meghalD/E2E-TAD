import pandas as pd
import json

# Example DataFrame creation (you can skip this if you already have your DataFrame)
data = {'Video_ID': ['video_id1', 'video_id1', 'video_id2', 'video_id2', 'video_id3'],
        'subset': ['train', 'train', 'val', 'val', 'test'],
        'annotation': ['X_3', 'M_4', 'A_7_7_1', 'X_2', 'M_5'],
        'Video_time': [1, 2, 3, 4, 5]}
df = pd.DataFrame(data)

# Sort the DataFrame by 'Video_ID' and 'Video_time'
df = df.sort_values(by=['Video_ID', 'Video_time'])

# Initialize the dictionary to store the ActivityNet dataset format
activitynet_dict = {'database': {}}

# Iterate through the sorted DataFrame to populate the dictionary
for index, row in df.iterrows():
    video_id = row['Video_ID']
    subset = row['subset']
    annotation = row['annotation']
    video_time = row['Video_time']

    if video_id not in activitynet_dict['database']:
        # If the video_id is not in the dictionary, add it with initial values
        activitynet_dict['database'][video_id] = {'duration': 0, 'annotations': []}

    if not activitynet_dict['database'][video_id]['duration']:
        # If the duration is not set, update it with the current Video_time
        activitynet_dict['database'][video_id]['duration'] = video_time

    if annotation.startswith(('X', 'M', 'A')):
        # If the annotation starts with 'X', 'M', or 'A', add it to the annotations list
        label = annotation
        start_time = video_time
        end_time = video_time  # Assuming each annotation has a duration of 0 (instantaneous)
        activitynet_dict['database'][video_id]['annotations'].append({
            'label': label,
            'segment': [start_time, end_time]
        })

print(activitynet_dict)
# Write the dictionary to a JSON file
with open('activitynet_dataset.json', 'w') as json_file:
    json.dump(activitynet_dict, json_file, indent=2)

print("ActivityNet dataset JSON file created successfully.")
