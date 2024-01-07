#solution 0
from Google import Create_Service # download source from the link in the description
import pandas as pd

def run_batchUpdate_request(service, google_sheet_id, request_body_json):
    try:
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=google_sheet_id,
            body=request_body_json
        ).execute()
        return response
    except Exception as e:
        print(e)
        return None
    
import os
from Google import Create_Service

CLIENT_SECRET_FILE = 'client_secret.json'
API_SERVICE_NAME = 'sheets'
API_VERSION = 'v4'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
GOOGLE_SHEET_ID = '1d7hnMOi1-Otxb7w6nbzejJMaLnHWrLaoVAv7Xp5khdY'
service = Create_Service(CLIENT_SECRET_FILE, API_SERVICE_NAME, API_VERSION, SCOPES)

gsheets = service.spreadsheets().get(spreadsheetId=GOOGLE_SHEET_ID).execute()
sheets = gsheets['sheets']

#solution 1
# import requests

# def download_google_sheet_as_csv(spreadsheet_id, csv_file_path):
#     #url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv'
#     #url = f'https://docs.google.com/spreadsheets/d/1Z6jZ3QbTqj4c0f5kYtV8t7s9gX7Q4ZqfZ5Zy4h7Y5n0/export?format=csv'
#     url = f'https://docs.google.com/spreadsheets/d/1d7hnMOi1-Otxb7w6nbzejJMaLnHWrLaoVAv7Xp5khdY/export?format=csv'
#     print(f'Downloading Google Sheet as CSV from: {url}')
#     response = requests.get(url)
#     if response.status_code == 200:
#         with open(csv_file_path, 'wb') as f:
#             f.write(response.content)
#         print(f'Google Sheet downloaded as CSV to: {csv_file_path}')
#     else:
#         print('Failed to download Google Sheet as CSV')

# # Call the function with the spreadsheet ID and the desired CSV file path
# download_google_sheet_as_csv(0, 'all_info.csv')


#solution 2
# import pandas as pd

# def build_sheet_url(doc_id, sheet_id):
#     return f'https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv&gid={sheet_id}'

# def write_df_to_local(df, file_path):
#     df.to_csv(file_path)

# doc_id = '1d7hnMOi1-Otxb7w6nbzejJMaLnHWrLaoVAv7Xp5khdY'
# sheet_id = '0'
# sheet_url = build_sheet_url(doc_id, sheet_id)
# df = pd.read_csv(sheet_url)
# file_path = 'FILE_PATH'
# write_df_to_local(df, file_path)