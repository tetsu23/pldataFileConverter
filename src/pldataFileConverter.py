#Copyright (c) 2022 tetsu23 (SenBayLab)
#This software is released under the MIT License, see LICENSE.

import msgpack
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import PySimpleGUI as sg


class ConvEyeFatigue2csv:
    def __enter__(self):
        self.plpath = ''
        self.elapsed_time = 0.0
        self.deltaTime = 0.0
        self.eyeType = 0
        self.leftDis = 0
        self.rightDis = 0
        self.df_new1 = 0
        print('START')
        return self


    #func Export .pldata to pandas DataFrame.
    def pldata2dataframe(self, columns, method_is_3d):
        # """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
        # Very important notes for existing users!!
        # PyPI package name
        # Package name on PyPI was changed from msgpack-python to msgpack from 0.5.
        # When upgrading from msgpack-0.4 or earlier, do pip uninstall msgpack-python 
        # before pip install -U msgpack.
        # """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
        #Export .pldata to pandas DataFrame.
        # Parameters
        # ----------
        # plpath: str
        #     Path to the pupil.pldata.
        # columns: list-like
        #     Items to export from pupil.pldata.
        # method_is_3d: bool
        #     Use data detected by 3D method or 2D method.
        #Returns
        # -------
        # dataframe: pandas.DataFrame
        # """
        if method_is_3d == True:
            method = '3'
        else:
            method = '2'

        with open(self.plpath, 'rb') as f:
            payloads = [payload for _, payload in msgpack.Unpacker(f)
                    if msgpack.unpackb(payload)['method'].startswith('3') and msgpack.unpackb(payload)['id'] == self.eyeType] # ここが右目０左目１
            data = [
                [msgpack.unpackb(payload)[col]
                for col in columns] 
                    for payload in payloads]
        return pd.DataFrame(data, columns=columns)

    # Edit and Draw graphs using extracted data from .pldata 
    def EditDataAndDrawGraph(self, str_plpath, eyetype):

        if eyetype == 0: # right eye
            print('EyeType is right')
        else:
            print('EyeType is left')

        print('success to input path',str_plpath)
        self.eyeType = eyetype
        self.plpath = str_plpath
        #'//XXX//000//pupil.pldata'
        columns = ['timestamp', 'id', 'method', 'confidence', 'norm_pos']
        
        is3d = True 
        df = CEF2C.pldata2dataframe(columns, is3d)
    
        # convert pupil timestamp to real timestamp
        rtime = df['timestamp'] - df.iloc[0,0]
        self.elapsedTime = pd.Series(data=rtime, name = 'elapsed_time', dtype='float')

        # divid norm_pos_x and norm_pos_y from norm_pos
        splitted = df['norm_pos'].apply(pd.Series)
        splitted.columns = ['norm_pos_x', 'norm_pos_y']

        # delete norm_pos
        df_new = df.drop( columns='norm_pos' )


        #calculate L2-norm of norm_pos_x and norm_pos_y
        np_splitted = splitted.values
        norm_L2 = np.apply_along_axis(np.linalg.norm, 1, np_splitted)
    
        #conver from numpy data to pandas Series
        L2 = pd.Series(data=norm_L2, name='pos_L2_norm', dtype='float')
        # merge each data
        self.df_new1 = pd.concat([self.elapsedTime, df_new, splitted, L2.T], axis=1 )
        print(self.df_new1)

    def DrawGraph(self):
        #----------- Draw graph ------------
        fig, axes = plt.subplots(2, 1, figsize=(10, 14), sharey=True)
        self.df_new1.plot(x = 'elapsed_time', y = 'confidence', ax=axes.flatten()[0])
        self.df_new1.plot(x = 'elapsed_time', y = 'norm_pos_x', ax=axes.flatten()[1])

        return fig

    # save graph figure
    def saveGraphImage(self, fig, outpath):    
        fig.savefig(outpath)

    # export .csv file
    def savePupilData2Cvs(self, outpath):
        self.df_new1.to_csv(outpath)


    def draw_plot(self, fig):

        plt.show(block=False)
        # must set (block=False)

    def del_plot(self, fig):
        plt.close()

    def __exit__(self, exception_type, exception_value, traceback):
        self.ser.close()
        print('END')



# ==================== global function =================== 

# GUI layout by pySimpleGUI
layout = [[sg.Text('Input .pldata file')],
          [sg.InputText(key='INPUT_FILE', enable_events=True, size=(45,1)),sg.FileBrowse('参照', file_types=(('pldataファイル', '*.pldata'),))],
          [sg.Text('Select an eye')],
          [sg.Radio('Left eye', group_id='radioint',key='EYE_LEFT'),sg.Radio('Right eye', group_id='radioint',key='EYE_RIGHT',default=True)],
          [sg.Text('Display graph'),sg.Button('Display',key='-display-')],
          [sg.Text('Output', key='-dis_status-')],
          [sg.Text('------------------------------------ Export result files ------------------------------------')],
          [sg.Checkbox('Save a graph image', key='SAVE_GRAPH', default=True,)],
          [sg.InputText(key='OUTPUT_IMG_FILE', enable_events=True, size=(45,1)),
           sg.FileSaveAs('Browse', file_types=(('png file', '*.png'),))],
          [sg.Checkbox('Output .csv file', key='SAVE_CSV',default=True)],
          [sg.InputText(key='OUTPUT_CSV_FILE', enable_events=True, size=(45,1)),
           sg.FileSaveAs('Browse', file_types=(('csv file', '*.csv'),))],
          [sg.Button('Save',key='-save-'),sg.Text('Output：',key='-output-')],
          [sg.Exit()]
         ]

sg.theme('Light Blue 2')
window = sg.Window('pldataFileConverter', layout, location=(100, 100), finalize=True)

CEF2C = ConvEyeFatigue2csv()
pre_plpath = ''
Disp_cnt = 1

while True:
    event, values = window.read()

    # Input .pldata file
    str_plpath = str(values['INPUT_FILE'])
    # set right or left eye
    if values['EYE_RIGHT'] == True:
        eyeType = 0
    elif values['EYE_LEFT'] == True:
        eyeType = 1


    # display  graphs
    if event == '-display-':
        if len(str_plpath) > 0:
            window['-output-'].update('出力:')
            CEF2C.EditDataAndDrawGraph(str_plpath, eyeType)
            fig_=CEF2C.DrawGraph()
            CEF2C.draw_plot(fig_)
            window['-dis_status-'].update(f'出力:Display figure {Disp_cnt}')
            Disp_cnt = Disp_cnt + 1
        else:
            window['-dis_status-'].update(f'出力:There is not file path!')



    
    #  save graph and csv 
    if event == '-save-':
        if values['SAVE_GRAPH'] == True:
            str_graph = str(values['OUTPUT_IMG_FILE'])
            CEF2C.saveGraphImage(fig_, str_graph)

        # convert .pldata to .csv
        if values['SAVE_CSV'] == True:
            str_csv = str(values['OUTPUT_CSV_FILE'])
            CEF2C.savePupilData2Cvs(str_csv)

        window['-output-'].update(f'Data of Figrue {Disp_cnt}: Finished to output files!')


    if event in (None, 'Exit'):
        break

window.close()
