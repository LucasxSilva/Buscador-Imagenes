from PyQt6.QtWidgets import QFileDialog,QInputDialog
from PyQt6.QtGui import QStandardItemModel
from threading import Thread
from time import sleep
from keyboard import is_pressed
import multiprocessing as mp
import pyautogui
pyautogui.FAILSAFE = False
import win32api
import win32con
import shutil
import ctypes #obtener posicion actual y volver a ella
import math
import cv2
import os

current_dir = os.getcwd()
img_path = os.path.join(current_dir, "Imagenes","")
if not os.path.exists(img_path):
    os.makedirs(img_path)

included_extensions = ['JPG','jpg','jpeg', 'bmp','PNG', 'png', 'gif','',' ']
file_names = [fn for fn in os.listdir(img_path)
    if any(fn.endswith(ext) for ext in included_extensions)]

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long),
                ("y", ctypes.c_long)]


class clase_funciones():
    def __init__(self,gui):
        super().__init__()
        self.gui = gui
        self.img_search_model = QStandardItemModel()
        self.img_saved_model = QStandardItemModel()
        self.lista_img_buscar=[[]]          #lista de listas de nombres de archivos por cb_index
        self.lista_img=[[]]                 #lista de listas de imagenes por cb_index
        self.lista_activado=[False]         #lista de activado por cb_index
        self.lista_posiciones=[[0,0,1366,768]]  #lista de 4 numeros por cb_index
        self.lista_threads = []                 #listas de thread por cb_index, cada uno busca 1 lista de imagenes cuando esta activado
        self.lista_confidence=[0.9]             #determina similitud necesaria para hacer click con la imagen. Acepta valores entre 0.0 y 1.0
        self.lista_nombres=["Inicial"]
        #crea thread para manejar teclado
        self.input_thread = Thread(target=self.handle_input, daemon=True)
        self.input_thread.start()   

        self.buscar=[False,False]   # [0]permite buscar   [1]pos inicial [2]pos final

        self.color_default=(0,0,0)
        self.click_thread = None
        
        self.pausa = mp.Value('b', False)
        self.salir = mp.Value('b', False)
        self.point = POINT()
        
        self.user32 = ctypes.windll.user32
        self.user32.GetCursorPos(ctypes.byref(self.point))
    
    def cambiar_si_inicial_mayor_final(self):
        cambios=False
        if self.lista_posiciones[self.gui.cb_index][0]>self.lista_posiciones[self.gui.cb_index][2]: #x inicial mayor a x final
            tmp=self.lista_posiciones[self.gui.cb_index][0]
            self.lista_posiciones[self.gui.cb_index][0]=self.lista_posiciones[self.gui.cb_index][2]
            self.lista_posiciones[self.gui.cb_index][2]=tmp
            cambios=True
            
        if self.lista_posiciones[self.gui.cb_index][1]>self.lista_posiciones[self.gui.cb_index][3]: #y inicial mayor a y final
            tmp=self.lista_posiciones[self.gui.cb_index][1]
            self.lista_posiciones[self.gui.cb_index][1]=self.lista_posiciones[self.gui.cb_index][3]
            self.lista_posiciones[self.gui.cb_index][3]=tmp    
            cambios=True

        if cambios:
            self.gui.txtno_top_left_x.setText(str(self.lista_posiciones[self.gui.cb_index][0]))
            self.gui.txtno_top_left_y.setText(str(self.lista_posiciones[self.gui.cb_index][1]))
            self.gui.txtno_bot_right_x.setText(str(self.lista_posiciones[self.gui.cb_index][2]))
            self.gui.txtno_bot_right_y.setText(str(self.lista_posiciones[self.gui.cb_index][3]))
            self.gui.cb_posicion.setItemText(self.gui.cb_posicion.currentIndex(),
                                            self.lista_nombres[self.gui.cb_index]+"     "+
                                            str(self.lista_posiciones[self.gui.cb_index][0])+" "+
                                            str(self.lista_posiciones[self.gui.cb_index][1])+" "+
                                            str(self.lista_posiciones[self.gui.cb_index][2])+" "+
                                            str(self.lista_posiciones[self.gui.cb_index][3]))

    def handle_input(self):
        while True:
            if is_pressed('*'):
                self.lista_activado=[False] * len(self.lista_activado)
                self.gui.rb_activado.setChecked(False)
                print("Desactivar todo")

            if is_pressed('p'):
                self.pausa.value=True
                self.gui.rb_activado.setChecked(False)
                print("Pausa")
            if is_pressed('+'):
                for i,lista in enumerate(self.lista_img):#index de cb_index, es el index que contiene lista de imagenes
                    for j,img in enumerate(lista):        #recorre el index de cada imagen en esa lista
                        #print(pyautogui.locateOnScreen(lista[j]))
                        location=pyautogui.locateOnScreen(lista[j],confidence=self.lista_confidence[i])
                        if location != None:
                            self.lista_posiciones[i] = [location[0],location[1],location[0]+location[2],location[1]+location[3]]
                            self.gui.txtno_top_left_x.setText(str(location[0]))
                            self.gui.txtno_top_left_y.setText(str(location[1]))
                            self.gui.txtno_bot_right_x.setText(str(location[0]+location[2]))
                            self.gui.txtno_bot_right_y.setText(str(location[1]+location[3]))
            
            
            if self.pausa.value==True:
                if is_pressed('r'):
                    self.pausa.value=False
                    print("Reanudar")
                    # si en self.lista_activado, esta activado, llama a la funcion con el correspondiente index
                    threads = [Thread(target=self.detectar_imagenes, args=(index,))
                            for index, activado in enumerate(self.lista_activado) if activado]

                    # Start all threads
                    for thread in threads:
                        thread.start()
                    if self.lista_activado[self.gui.cb_index]==True:
                        self.gui.rb_activado.setChecked(True)  
            sleep(0.1)
            
    def detectar_imagen_singular(self,img, region,confidence):
        location=None
        try:
            location = pyautogui.locateCenterOnScreen(img, region=region, confidence=confidence, grayscale=True)
            print(location)
        except:
            print("Region inadecuada, reajustando")
            height, width = img.shape[:2]
            
            region[0]=region[0]-width//2
            if region[0]<0:
                region[0]=0
                region[2]=region[2]+width
            else:
                region[2]=region[2]+width//2
                
            region[1]=region[1]-height//2
            if region[1]<0:
                region[1]=0
                region[3]=region[3]+width
            else:
                region[3]=region[3]+width//2
            #print(region)
            screen_width, screen_height = pyautogui.size()
            if region[2]>screen_width:
                region[2]=screen_width
            if region[3]>screen_height:
                region[3]=screen_height

        if location:
            self.user32.GetCursorPos(ctypes.byref(self.point))
            while location!=None:
                pyautogui.click(location.x,location.y)
                location = pyautogui.locateCenterOnScreen(img, region=region, confidence=confidence, grayscale=True)
                if is_pressed('*'):
                    self.lista_activado=[False] * len(self.lista_activado)
                    self.gui.rb_activado.setChecked(False)
                    print("Desactivar todo")
                    break

                if is_pressed('p'):
                    self.pausa.value=True
                    self.gui.rb_activado.setChecked(False)
                    print("self.Pausa")
                    break
                
                if not location:
                    break
            sleep(0.1)
            self.user32.SetCursorPos(self.point.x, self.point.y)

    def detectar_imagenes(self,cb_index):
        while self.lista_activado[cb_index]==True and len(self.lista_img[cb_index])>0:  
            #print(cb_index)
            if self.pausa.value==False:     
                for img in self.lista_img[cb_index]:
                    self.detectar_imagen_singular(img,self.lista_posiciones[cb_index],self.lista_confidence[cb_index])
                    sleep(0.3)
            else:
                break
        
    def mouse_store_start(self,x):
        self.buscar[x]=True
        if self.click_thread != None and self.click_thread.is_alive():
            print("click_thread ocupado")
        else:
            if self.buscar[0]==True:
                self.color_default = self.gui.btn_inicial.palette().color(self.gui.btn_inicial.backgroundRole())
                self.color_default = tuple(self.color_default.getRgb()[:3])
                sleep(0.001)
                self.gui.btn_inicial.setStyleSheet("background-color: red;")
                self.gui.btn_final.setStyleSheet(f"background-color: rgb{self.color_default};")

            elif self.buscar[1]==True:
                self.color_default = self.gui.btn_final.palette().color(self.gui.btn_final.backgroundRole())
                self.color_default = tuple(self.color_default.getRgb()[:3])
                sleep(0.001)
                self.gui.btn_final.setStyleSheet("background-color: red;")
                self.gui.btn_inicial.setStyleSheet(f"background-color: rgb{self.color_default};")          
            # create and start a new thread
            self.click_thread = Thread(target=self.store_mouse_pos, daemon=True)
            self.click_thread.start() 

    def store_mouse_pos(self):  
        if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) != 0:  # detecta click mouse izquierdo
            while True:
                #pyautogui.mouseInfo()
                if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) != 0:  # detecta click mouse izquierdo
                    x, y = pyautogui.position()
                    if self.buscar[0]==True: #determina pos inicial
                        self.lista_posiciones[self.gui.cb_index][0]=x
                        self.lista_posiciones[self.gui.cb_index][1]=y
                        self.gui.txtno_top_left_x.setText(str(x))
                        self.gui.txtno_top_left_y.setText(str(y))
                        self.buscar[:2]=[False,False]
                        self.gui.cb_posicion.setItemText(self.gui.cb_posicion.currentIndex(),self.lista_nombres[self.gui.cb_index]+"     "+str(self.lista_posiciones[self.gui.cb_index][0])+" "+str(self.lista_posiciones[self.gui.cb_index][1])+" "+str(self.lista_posiciones[self.gui.cb_index][2])+" "+str(self.lista_posiciones[self.gui.cb_index][3]))
                        self.cambiar_color(self.gui.btn_inicial,(255,0,0),self.color_default,150)
                        break
                    if self.buscar[1]==True: #determina pos final
                        self.lista_posiciones[self.gui.cb_index][2]=x
                        self.lista_posiciones[self.gui.cb_index][3]=y 
                        self.gui.txtno_bot_right_x.setText(str(x))
                        self.gui.txtno_bot_right_y.setText(str(y))
                        self.buscar[:2]=[False,False]        
                        self.gui.cb_posicion.setItemText(self.gui.cb_posicion.currentIndex(),self.lista_nombres[self.gui.cb_index]+"     "+str(self.lista_posiciones[self.gui.cb_index][0])+" "+str(self.lista_posiciones[self.gui.cb_index][1])+" "+str(self.lista_posiciones[self.gui.cb_index][2])+" "+str(self.lista_posiciones[self.gui.cb_index][3]))  
                        self.cambiar_color(self.gui.btn_final,(255,0,0),self.color_default,150)
                        break
                sleep(0.1)
            self.cambiar_si_inicial_mayor_final()

    def cambiar_color(self,widget,start,end,tick_interval):
        diff = tuple(end[i] - start[i] for i in range(3))
        # Calcula el incremento para cada tick
        tick_increment = tuple(diff[i] / tick_interval for i in range(3))
        for tick in range(tick_interval):
            intermediate = tuple(start[i] + tick * tick_increment[i] for i in range(3))
            intermediate = tuple(math.floor(val + 0.5) if math.isclose(val % 1, 0.5) else round(val) for val in intermediate)  # Efficient rounding of RGB values
            sleep(0.001)    # problema en sincronizacion, sin sleep es tan rapido que se rompe
            widget.setStyleSheet(f"background-color: rgb{intermediate};")
        widget.setStyleSheet(f"background-color: rgb{end};")




    def check_txt_empty(self,text):
        if not text: #se fija si esta vacio
            sender = self.sender()    #obtiene el objeto que llamo a esta funcion
            sender.setText('0')       #cambia el text a 0  
        
    def add_pos(self):
        #print(self.gui.cb_posicion.count())
        #print(self.gui.cb_posicion.currentIndex())

        self.gui.cb_posicion.addItem(self.gui.txt_nombre.text()+"     "+self.gui.txt_top_left_x.text()+" "+self.gui.txt_top_left_y.text()+" "+self.gui.txt_bot_right_x.text()+" "+self.gui.txt_bot_right_y.text())       

        self.gui.txtno_top_left_x.setText(self.gui.txt_top_left_x.text())
        self.gui.txtno_top_left_y.setText(self.gui.txt_top_left_y.text())
        self.gui.txtno_bot_right_x.setText(self.gui.txt_bot_right_x.text())
        self.gui.txtno_bot_right_y.setText(self.gui.txt_bot_right_y.text())
        try:
            if float(self.gui.txt_confidence.text())<0 or float(self.gui.txt_confidence.text())>1:
                self.gui.txt_confidence.setText("0.9")
        except:
            self.gui.txt_confidence.setText("0.9")
            
        self.gui.txtno_confidence.setText(self.gui.txt_confidence.text())

        #guarda imagen y posicion
        self.lista_nombres.append(self.gui.txt_nombre.text())
        self.lista_img_buscar.append([])
        self.lista_img.append([])
        self.lista_activado.append(False)
        self.lista_posiciones.append([int(self.gui.txt_top_left_x.text()), int(self.gui.txt_top_left_y.text()), int(self.gui.txt_bot_right_x.text()), int(self.gui.txt_bot_right_y.text())])
        self.lista_confidence.append(self.gui.txt_confidence.text())
        self.gui.cb_posicion.setCurrentIndex(self.gui.cb_posicion.count()-1)
        self.gui.rb_activado.setChecked(False)
        self.gui.rb_activado.setEnabled(False)
        self.cambiar_si_inicial_mayor_final()

        # count empieza en 1, currentIndex en 0

    def mod_pos(self):  

        self.gui.cb_posicion.setItemText(self.gui.cb_posicion.currentIndex(),self.gui.txt_nombre.text()+"     "+self.gui.txt_top_left_x.text()+" "+self.gui.txt_top_left_y.text()+" "+self.gui.txt_bot_right_x.text()+" "+self.gui.txt_bot_right_y.text())
                
        self.lista_posiciones[self.gui.cb_index][0]=int(self.gui.txt_top_left_x.text())
        self.lista_posiciones[self.gui.cb_index][1]=int(self.gui.txt_top_left_y.text())
        self.lista_posiciones[self.gui.cb_index][2]=int(self.gui.txt_bot_right_x.text())
        self.lista_posiciones[self.gui.cb_index][3]=int(self.gui.txt_bot_right_y.text())
        if float(self.gui.txt_confidence.text())<0.0 or float(self.gui.txt_confidence.text())>1.0:
            self.gui.txt_confidence.setText("0.9")
        self.lista_confidence[self.gui.cb_index]=self.gui.txt_confidence.text()
        self.lista_nombres[self.gui.cb_index]=self.gui.txt_nombre.text()
        
        self.gui.txtno_top_left_x.setText(self.gui.txt_top_left_x.text())
        self.gui.txtno_top_left_y.setText(self.gui.txt_top_left_y.text())
        self.gui.txtno_bot_right_x.setText(self.gui.txt_bot_right_x.text())
        self.gui.txtno_bot_right_y.setText(self.gui.txt_bot_right_y.text())
        self.gui.txtno_confidence.setText(self.gui.txt_confidence.text())
        self.cambiar_si_inicial_mayor_final()

    def remover(self):
        index = self.gui.cb_posicion.currentIndex()
        self.gui.cb_posicion.removeItem(index)

        if len(self.lista_img_buscar)>1:
            self.lista_img_buscar.pop(index)
            self.lista_img.pop(index)
            self.lista_posiciones.pop(index)
            self.lista_activado.pop(index)
            self.lista_confidence.pop(index)

    def add_img(self):
        if (self.gui.lw_img_guardadas.currentItem()!=None):
            selected_item = self.gui.lw_img_guardadas.currentItem()
            text=selected_item.text()
            existe=False
            for item in self.lista_img_buscar[self.gui.cb_index]:
                if text==item:
                    existe=True
            if existe==False:
                self.gui.lw_img_buscar.addItem(text)
                self.lista_img_buscar[self.gui.cb_index].append(selected_item.text())
                self.lista_img[self.gui.cb_index].append(cv2.imread(img_path+selected_item.text()))
                self.gui.rb_activado.setEnabled(True)

    def rem_img(self):

        if (self.gui.lw_img_buscar.currentItem()!=None):
            selected_item = self.gui.lw_img_buscar.currentItem()
            item_row=self.gui.lw_img_buscar.currentRow()
            self.lista_img_buscar[self.gui.cb_index].pop(item_row)
            self.lista_img[self.gui.cb_index].pop(item_row)
            self.gui.lw_img_buscar.takeItem(self.gui.lw_img_buscar.row(selected_item))
            if len(self.lista_img_buscar[self.gui.cb_index])<=0:
                self.gui.rb_activado.setChecked(False)
                self.gui.rb_activado.setEnabled(False)
                self.lista_activado[self.gui.cb_index]=False
        
    def activar(self,checked):
        if checked:
            if self.lista_activado[self.gui.cb_index]==False:
                self.lista_activado[self.gui.cb_index]=True

                if len(self.lista_img[self.gui.cb_index])>0: #se fija si hay imagenes
                    thread = Thread(target=self.detectar_imagenes, args=(self.gui.cb_index,), daemon=True)
                    self.lista_threads.append(thread)
                    thread.start()                    
        else:
            self.lista_activado[self.gui.cb_index]=False

    def subir_img(self):
        
        options = QFileDialog.Option(0)
        file_name, _ = QFileDialog.getSaveFileName(None, "Save File", "", "All Files (*);;Text Files (*.txt)", options=options)

        if file_name:
            # Handle the file as needed
            # Get the base filename of the selected file
            base_filename = os.path.basename(file_name)
            # Copy the file to the subdirectory
            destination_path = os.path.join(img_path, base_filename)#directorio del archivo python/Imagenes/archivo
            try:
                shutil.copy(file_name, destination_path)
            except shutil.SameFileError:
                pass
            #print(f"Selected file path: {file_name}")
        else:
            pass
        
    def cambios_carpeta_imagen(self):
        # The folder has changed, update the QListWidget with the new files         #buscar archivos con esas extension en el subdirectorio /imagenes
        file_names = [fn for fn in os.listdir(img_path)
            if any(fn.endswith(ext) for ext in included_extensions)]

        self.gui.lw_img_guardadas.clear()
        self.gui.lw_img_guardadas.addItems(file_names)  
        
    def mod_img_nombre(self):
        if (self.gui.lw_img_buscar.currentItem()!=None):
            selected_item = self.gui.lw_img_buscar.currentItem()
            new_text, ok = QInputDialog.getText(self.gui.lw_img_buscar.parent(), 'Modificar nombre', 'Introduzca el nuevo nombre:', text=selected_item.text())
            if ok:
                os.rename(img_path+selected_item.text(),img_path+new_text)
                selected_item.setText(new_text)
        
    def stop_all(self):
        self.lista_activado=[False] * len(self.lista_activado)
        self.gui.rb_activado.setChecked(False)

    def cambio_espacio(self):
        self.gui.lw_img_buscar.clear()
        self.gui.cb_index=self.gui.cb_posicion.currentIndex()
        for item in self.lista_img_buscar[self.gui.cb_index]:
            self.gui.lw_img_buscar.addItem(item)
        self.gui.txtno_top_left_x.setText(str(self.lista_posiciones[self.gui.cb_index][0])) 
        self.gui.txtno_top_left_y.setText(str(self.lista_posiciones[self.gui.cb_index][1])) 
        self.gui.txtno_bot_right_x.setText(str(self.lista_posiciones[self.gui.cb_index][2])) 
        self.gui.txtno_bot_right_y.setText(str(self.lista_posiciones[self.gui.cb_index][3])) 
        self.gui.rb_activado.setChecked(self.lista_activado[self.gui.cb_index]) 
        if len(self.lista_img_buscar[self.gui.cb_index])>0:
            self.gui.rb_activado.setEnabled(True)
        else:
            self.gui.rb_activado.setEnabled(False)