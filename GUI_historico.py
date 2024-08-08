import PySimpleGUI as sg
import sqlite3
import config
import json
import requests
import datetime
import numpy as np

import io
import os
import PySimpleGUI as sg



sg.theme('Dark')


# top row

top_row = [[sg.Text('Pedido', size=(5, 1)), sg.InputText(do_not_clear=False, size=(5, 1)),sg.Button('Go', visible=False, bind_return_key=True),sg.Text('Peso estimado', size=(12, 1)),sg.Text(key='-P_Estimado-',text='',size=(6, 1)),sg.Text('Peso Real', size=(10, 1)),sg.Text(key='-P_Real-',text='',size=(6, 1))]]
# First colum vazia, para centrar as restantes colunas

right_col = [[sg.Text('Pick List',font=("Arial CE",16))],[sg.MLine(key='-ML3-'+sg.WRITE_ONLY_KEY, size=(60,30),font=("Arial CE", 11),background_color="lightgrey",text_color="black",no_scrollbar = True)]]


# ----- Full layout -----
#layout = [top_row,[sg.Column(empty_col, element_justification='c',vertical_alignment='t'),sg.Column(left_col, element_justification='c',vertical_alignment='t'), sg.VSeperator(),sg.Column(midle_col, element_justification='c',vertical_alignment='t'), sg.VSeperator(),sg.Column(right_col, element_justification='c',vertical_alignment='t')]]


#a='D:\Programa_Python\Producao_25_08_21\Fotos\\20210927_19h50m08s_99835'


# create the form that also returns keyboard events
form = sg.FlexForm('Image Browser', return_keyboard_events=True, location=(0,0), use_default_focus=False )

# make these 2 elements outside the layout because want to "update" them later
# initialize to the first PNG file in the list
image_elem = sg.Image(filename='')
filename_display_elem = sg.Text('', size=(60, 2))
list_box= sg.Listbox(values='', size=(30,30), key='listbox')


# define layout, show and read the form
col = [[filename_display_elem],
          [image_elem]]

col_files = [[list_box],
             [sg.ReadFormButton('Read')]]
layout = [[sg.Column(top_row)],[sg.Column(col_files), sg.Column(col), sg.Column(right_col)]]


window = sg.Window('Demo - Apresentador McDelivery', layout, finalize=True, resizable = True, location=(0,0), size=(1400,900),keep_on_top=True)

button, values = window.read()          # Shows form on screen




# loop reading the user input and displaying image, filename
filename = ""
file_foto= ""
i=0
while True:
    file_foto= ""
    

    # perform button and keyboard operations
    if button is None:
        break
    
    if button == 'Go':
        window['-ML3-'+sg.WRITE_ONLY_KEY].update('')
        window['-P_Estimado-'].update('')
        window['-P_Real-'].update('')
        # update window with new list
        list_box.Update(values='')
        # update window with new image
        image_elem.Update(filename='')
        # update window with filename
        filename_display_elem.Update('')


        #procura a pick list correspondete
            
        if len(values[0])>2:   #para códigos uber/glovo/Jet
            a=values[0]+"%"
        else:               #para códigos internos [1:100]
            a=values[0]
        
        con = sqlite3.connect(config.db)
        cur = con.cursor()
        #cur.execute("SELECT * FROM pick_list WHERE delivery_name LIKE :name ORDER BY id DESC LIMIT 1",{"name":a})
        cur.execute("SELECT * FROM pesagem INNER JOIN pick_list on pick_list.id = pesagem.pick_list_id WHERE pick_list.delivery_name LIKE :name ORDER BY id DESC",{"name":a})
        resposta=cur.fetchall()
        con.close()

        if resposta:
            print(resposta)
            filenames_only=[]
            for n in resposta:
                filenames_only.append(str(n[0]) +', '+ str(n[6]))
            print(filenames_only)
            #filename = folder + '\\' + values['listbox'][0]
            # print(filename)


    if button == 'Read' and values['listbox'] :
        window['-ML3-'+sg.WRITE_ONLY_KEY].update('')
        # update window with new list
        list_box.Update('')
        # update window with new image
        image_elem.Update(filename='')
        # update window with filename
        filename_display_elem.Update('')


        
        print(values['listbox'][0])
        my_list = values['listbox'][0].split(",")
        print(my_list)
        con = sqlite3.connect(config.db)
        cur = con.cursor()
        cur.execute("SELECT * FROM pesagem INNER JOIN pick_list on pick_list.id = pesagem.pick_list_id WHERE pesagem.rowid = :id",{"id":my_list[0]})
        resposta=cur.fetchall()
        con.close()

        if resposta:
            window['-P_Estimado-'].update(str(resposta[0][2]))
            window['-P_Real-'].update(str(resposta[0][3]))
            
            
            if resposta[0][4] is not None:
                print(resposta)
                print(len(resposta[0][4]))
                file_foto=config.img_path+resposta[0][4]
                
            if resposta[0][8] is not None:
                print(resposta)
                print(len(resposta[0][8]))
                file_picklist=resposta[0][8]

                
                config.file_dir_pick_list
                lines=[]
                #abre o ficheiro e processa linha a linha
                with open(config.file_dir_pick_list+'\\'+file_picklist, "r") as file:
                    for line in file: 
                        line = line.upper()
                        #print(line)
                        line = line.replace("\\X1BD","").replace("\\X1DVB","").replace("\\N'","").replace('\\N"',"").replace("\\X1BE","").replace("\\X00","").replace("\\X1BA","").replace("\\X1D!","")
                        #print(line)
                        line = line.replace("B'","").replace('B"',"").replace('"',"").replace("\\X01","").replace("\\X11","").replace("\\R\\X1DL","").strip()
                        #print (line)
                        lines.append(line) #storing everything in memory!
                        if len(line)>1:
                            window['-ML3-'+sg.WRITE_ONLY_KEY].print("  "+line)
            
        


    try:
        
        # update window with new list
        list_box.Update(values=filenames_only)


        # update window with new image
        image_elem.Update(filename=file_foto)
        # update window with filename
        filename_display_elem.Update(file_foto)


        
    except Exception as e:
        print('erro')

    # read the form
    button, values = window.read()

window.close()


