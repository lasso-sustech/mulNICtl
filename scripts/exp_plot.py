import os, inspect
# Move data into a dictionary
current_path = os.getcwd()
parent_path = os.path.dirname(current_path)
script_folder_path = os.path.join(parent_path, 'expSrc')
data_folder_path = os.path.join(parent_path, 'logs')

NAME2EXPTIME = lambda name: name.split('_')[1:]

def get_exp_file(name, ppath):
    [year, month, day, exp_name] = NAME2EXPTIME(name)
    files = os.listdir(ppath)
    folder_1 = f'{year}-{month}-{day}'
    if folder_1 not in files:
        raise FileNotFoundError(f'File {file_path} not found in {ppath}')
    file_path = os.path.join(script_folder_path, folder_1)
    folder_2 = f'{exp_name}'
    files = os.listdir(file_path)
    if folder_2 not in files:
        raise FileNotFoundError(f'File {file_path} not found in {ppath}')
    file_path = os.path.join(file_path, folder_2)
    return file_path

def exp_2024_4_5_channelRTTComp():
    exp_name = inspect.stack()[0][3]
    script_path = get_exp_file(exp_name, script_folder_path)
    data_path = get_exp_file(exp_name, data_folder_path)
    data_name = f'exp:{NAME2EXPTIME(exp_name)[-1]}'
    print(script_path, data_path, data_name)
    ## Move data into script
    
exp_2024_4_5_channelRTTComp()