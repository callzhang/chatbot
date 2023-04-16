import os, pandas as pd, sys
from pathlib import Path
from . import utils

def convert_md_csv():
    chat_folder = Path('chats')
    files = chat_folder.glob('*.md')
    for md in files:
        fn = os.path.basename(md)
        name = fn.split('.')[0]
        histories = utils.get_history(name, to_dict=True)
        if not histories:
            print(f'Not history found for [{fn}]')
            continue
        target_folder = chat_folder/name
        conversations = []
        os.makedirs(target_folder, exist_ok=True)
        for date_str, chats in histories.items():
            csv_file = target_folder/f'{date_str}.csv'
            df = pd.DataFrame(chats)
            # df.sort_values(by='time', inplace=True)
            df.to_csv(csv_file)
            conversations.append({
                'time': df.time.min(),
                'title': date_str,
                'file': csv_file
            })
        chat_history = pd.DataFrame(conversations).sort_values('title', ascending=False)
        chat_history.to_csv(target_folder/'history.csv')
        print(f'Chat converted: {md}')
