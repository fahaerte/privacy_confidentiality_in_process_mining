import pm4py
import pandas as pd
import requests
import utility
import os

def import_xes(file_path):
    event_log = pm4py.read_xes(file_path)
    event_log['time:timestamp'] = pd.to_datetime(event_log['time:timestamp'], utc=True)
    return event_log


def translate_text(text_to_translate, url, auth_key):
    headers = {
        'Authorization': f'DeepL-Auth-Key {auth_key}'
    }

    data = {
        'text': text_to_translate,
        'target_lang': 'EN'
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        result = response.json()
        return result['translations'][0]['text']
    else:
        print("Error: {}".format(response.status_code))
        return "Error: {}".format(response.status_code)
    

def translate_durch_to_english(event_log, url, auth_key):

    concept_names_dutch = event_log['concept:name'].unique()
    concept_names_translations = {}

    for i in range(0, len(concept_names_dutch)):
        translation = translate_text(concept_names_dutch[i], url=url, auth_key=auth_key)
        concept_names_translations[concept_names_dutch[i]] = translation
    
    return concept_names_translations


if __name__ == '__main__':
    settings = utility.read_variables_from_file('settings.ini')
    import_path = settings.get('import_path', '')
    export_path = settings.get('export_path', '')
    deepl_url = settings.get('deepl_url', '')
    deepl_auth_key = settings.get('deepl_auth_key', '')

    event_log = import_xes(import_path)
    translations_dict = translate_durch_to_english(event_log, url=deepl_url, auth_key=deepl_auth_key)
    event_log['concept:name'] = event_log['concept:name'].replace(translations_dict)
    pm4py.write_xes(event_log, export_path, case_id_key='case:concept:name')