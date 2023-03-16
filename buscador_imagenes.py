from PyQt6 import QtCore, QtWidgets 
from PyQt6.QtWidgets import QFileDialog,QInputDialog
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtCore import QFileSystemWatcher
from PyQt6.QtGui import QIntValidator,QIcon
from threading import Thread
from time import sleep
from keyboard import is_pressed
import shutil
import sys
import win32api
import win32con
import ctypes #obtener posicion actual y volver a ella
import cv2
import pyautogui
pyautogui.FAILSAFE = False
import multiprocessing as mp
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

class Ui_Buscador(QtWidgets.QWidget, QtCore.QObject):

    def __init__(self):
        super().__init__()
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
        
        
    def cambiar_si_inicial_mayor_final(self):
        cambios=False
        if self.lista_posiciones[self.cb_index][0]>self.lista_posiciones[self.cb_index][2]: #x inicial mayor a x final
            tmp=self.lista_posiciones[self.cb_index][0]
            self.lista_posiciones[self.cb_index][0]=self.lista_posiciones[self.cb_index][2]
            self.lista_posiciones[self.cb_index][2]=tmp
            cambios=True
            
        if self.lista_posiciones[self.cb_index][1]>self.lista_posiciones[self.cb_index][3]: #y inicial mayor a y final
            tmp=self.lista_posiciones[self.cb_index][1]
            self.lista_posiciones[self.cb_index][1]=self.lista_posiciones[self.cb_index][3]
            self.lista_posiciones[self.cb_index][3]=tmp    
            cambios=True

        if cambios:
            self.txtno_top_left_x.setText(str(self.lista_posiciones[self.cb_index][0]))
            self.txtno_top_left_y.setText(str(self.lista_posiciones[self.cb_index][1]))
            self.txtno_bot_right_x.setText(str(self.lista_posiciones[self.cb_index][2]))
            self.txtno_bot_right_y.setText(str(self.lista_posiciones[self.cb_index][3]))
            self.cb_posicion.setItemText(self.cb_posicion.currentIndex(),
                                         self.lista_nombres[self.cb_index]+"     "+
                                         str(self.lista_posiciones[self.cb_index][0])+" "+
                                         str(self.lista_posiciones[self.cb_index][1])+" "+
                                         str(self.lista_posiciones[self.cb_index][2])+" "+
                                         str(self.lista_posiciones[self.cb_index][3]))
    
    def handle_input(self):
        while True:
            if is_pressed('*'):
                self.lista_activado=[False] * len(self.lista_activado)
                self.rb_activado.setChecked(False)
                print("Desactivar todo")

            if is_pressed('p'):
                pausa.value=True
                self.rb_activado.setChecked(False)
                print("Pausa")
            if is_pressed('+'):
                for i,lista in enumerate(self.lista_img):#index de cb_index, es el index que contiene lista de imagenes
                    for j,img in enumerate(lista):        #recorre el index de cada imagen en esa lista
                        print(pyautogui.locateOnScreen(lista[j]))
                        location=pyautogui.locateOnScreen(lista[j],confidence=self.lista_confidence[i])
                        if location != None:
                            self.lista_posiciones[i] = [location[0],location[1],location[0]+location[2],location[1]+location[3]]
                            self.txtno_top_left_x.setText(str(location[0]))
                            self.txtno_top_left_y.setText(str(location[1]))
                            self.txtno_bot_right_x.setText(str(location[0]+location[2]))
                            self.txtno_bot_right_y.setText(str(location[1]+location[3]))
            
            
            if pausa.value==True:
                if is_pressed('r'):
                    pausa.value=False
                    print("Reanudar")
                    # si en self.lista_activado, esta activado, llama a la funcion con el correspondiente index
                    threads = [Thread(target=self.detectar_imagenes, args=(index,))
                            for index, activado in enumerate(self.lista_activado) if activado]

                    # Start all threads
                    for thread in threads:
                        thread.start()
                    if self.lista_activado[self.cb_index]==True:
                        self.rb_activado.setChecked(True)  
            sleep(0.1)
            
    def detectar_imagen_singular(self,img, region,confidence):
        location=None
        print(type(region),type(region[0]),type(region[1]),type(region[2]),type(region[3]))
        print(confidence)
        try:
            location = pyautogui.locateCenterOnScreen(img, region=region, confidence=confidence, grayscale=True)
        except:
            print("Region pequeña, reajustando")
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
            user32.GetCursorPos(ctypes.byref(point))
            while location!=None:
                pyautogui.click(location.x,location.y)
                location = pyautogui.locateCenterOnScreen(img, region=region, confidence=confidence, grayscale=True)
                if is_pressed('*'):
                    self.lista_activado=[False] * len(self.lista_activado)
                    self.rb_activado.setChecked(False)
                    print("Desactivar todo")
                    break

                if is_pressed('p'):
                    pausa.value=True
                    self.rb_activado.setChecked(False)
                    print("Pausa")
                    break
                
                if not location:
                    break
            sleep(0.1)
            user32.SetCursorPos(point.x, point.y)

    def detectar_imagenes(self,cb_index):
        while self.lista_activado[cb_index]==True and len(self.lista_img[cb_index])>0:  
            #print(cb_index)
            if pausa.value==False:     
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
                self.color_default = self.btn_inicial.palette().color(self.btn_inicial.backgroundRole())
                self.color_default = tuple(self.color_default.getRgb()[:3])
                self.btn_inicial.setStyleSheet("background-color: red;")
                self.btn_final.setStyleSheet(f"background-color: rgb{self.color_default};")

            elif self.buscar[1]==True:
                self.color_default = self.btn_final.palette().color(self.btn_final.backgroundRole())
                self.color_default = tuple(self.color_default.getRgb()[:3])
                self.btn_final.setStyleSheet("background-color: red;")
                self.btn_inicial.setStyleSheet(f"background-color: rgb{self.color_default};")      
                                
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
                        self.lista_posiciones[self.cb_index][0]=x
                        self.lista_posiciones[self.cb_index][1]=y
                        self.txtno_top_left_x.setText(str(x))
                        self.txtno_top_left_y.setText(str(y))
                        self.buscar[:2]=[False,False]
                        self.cb_posicion.setItemText(self.cb_posicion.currentIndex(),self.lista_nombres[self.cb_index]+"     "+str(self.lista_posiciones[self.cb_index][0])+" "+str(self.lista_posiciones[self.cb_index][1])+" "+str(self.lista_posiciones[self.cb_index][2])+" "+str(self.lista_posiciones[self.cb_index][3]))
                        self.cambiar_color(self.btn_inicial,(255,0,0),self.color_default,25)
                        break
                    if self.buscar[1]==True: #determina pos final
                        self.lista_posiciones[self.cb_index][2]=x
                        self.lista_posiciones[self.cb_index][3]=y 
                        self.txtno_bot_right_x.setText(str(x))
                        self.txtno_bot_right_y.setText(str(y))
                        self.buscar[:2]=[False,False]        
                        self.cb_posicion.setItemText(self.cb_posicion.currentIndex(),self.lista_nombres[self.cb_index]+"     "+str(self.lista_posiciones[self.cb_index][0])+" "+str(self.lista_posiciones[self.cb_index][1])+" "+str(self.lista_posiciones[self.cb_index][2])+" "+str(self.lista_posiciones[self.cb_index][3]))  
                        self.cambiar_color(self.btn_final,(255,0,0),self.color_default,25)
                        break
                sleep(0.1)
            self.cambiar_si_inicial_mayor_final()

    def cambiar_color(self,widget,start,end,tick_interval):
        diff = tuple(end[i] - start[i] for i in range(3))
        # Calculate the increment for each tick
        tick_increment = tuple(diff[i] / tick_interval for i in range(3))
        for tick in range(tick_interval):
            intermediate = tuple(start[i] + tick * tick_increment[i] for i in range(3))
            intermediate = tuple(int(round(val)) for val in intermediate)
            widget.setStyleSheet(f"background-color: rgb{intermediate};")
            sleep(0.0001)
        widget.setStyleSheet(f"background-color: rgb{end};")

    def setupUi(self, Buscador):
        Buscador.setObjectName("Buscador")
        Buscador.resize(490, 324)
        self.gridLayout = QtWidgets.QGridLayout(Buscador)
        self.gridLayout.setObjectName("gridLayout")
        self.lyt_main = QtWidgets.QVBoxLayout()
        self.lyt_main.setObjectName("lyt_main")
        self.lyt_up_pos = QtWidgets.QHBoxLayout()
        self.lyt_up_pos.setObjectName("lyt_up_pos")
        self.lyt_posicion_select = QtWidgets.QVBoxLayout()
        self.lyt_posicion_select.setContentsMargins(5, 6, 5, 6)
        self.lyt_posicion_select.setSpacing(6)
        self.lyt_posicion_select.setObjectName("lyt_posicion_select")
        self.cb_posicion = QtWidgets.QComboBox(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cb_posicion.sizePolicy().hasHeightForWidth())
        self.cb_posicion.setSizePolicy(sizePolicy)
        self.cb_posicion.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
        self.cb_posicion.setObjectName("cb_posicion")
        self.cb_posicion.addItem("")
        self.cb_index=self.cb_posicion.currentIndex()

        self.lyt_posicion_select.addWidget(self.cb_posicion)
        self.lyt_pos_inicial_2 = QtWidgets.QHBoxLayout()
        self.lyt_pos_inicial_2.setObjectName("lyt_pos_inicial_2")
        self.lblno_top_left_inicial = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblno_top_left_inicial.sizePolicy().hasHeightForWidth())
        self.lblno_top_left_inicial.setSizePolicy(sizePolicy)
        self.lblno_top_left_inicial.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblno_top_left_inicial.setObjectName("lblno_top_left_inicial")
        self.lyt_pos_inicial_2.addWidget(self.lblno_top_left_inicial)
        self.lblno_top_leftx = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblno_top_leftx.sizePolicy().hasHeightForWidth())
        self.lblno_top_leftx.setSizePolicy(sizePolicy)
        self.lblno_top_leftx.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblno_top_leftx.setObjectName("lblno_top_leftx")
        self.lyt_pos_inicial_2.addWidget(self.lblno_top_leftx)
        self.txtno_top_left_x = QtWidgets.QLineEdit(parent=Buscador)
        self.txtno_top_left_x.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtno_top_left_x.sizePolicy().hasHeightForWidth())
        self.txtno_top_left_x.setSizePolicy(sizePolicy)
        self.txtno_top_left_x.setInputMask("")
        self.txtno_top_left_x.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.txtno_top_left_x.setObjectName("txtno_top_left_x")
        self.lyt_pos_inicial_2.addWidget(self.txtno_top_left_x)
        self.lblno_top_lefty = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblno_top_lefty.sizePolicy().hasHeightForWidth())
        self.lblno_top_lefty.setSizePolicy(sizePolicy)
        self.lblno_top_lefty.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblno_top_lefty.setObjectName("lblno_top_lefty")
        self.lyt_pos_inicial_2.addWidget(self.lblno_top_lefty)
        self.txtno_top_left_y = QtWidgets.QLineEdit(parent=Buscador)
        self.txtno_top_left_y.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtno_top_left_y.sizePolicy().hasHeightForWidth())
        self.txtno_top_left_y.setSizePolicy(sizePolicy)
        self.txtno_top_left_y.setInputMask("")
        self.txtno_top_left_y.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.txtno_top_left_y.setObjectName("txtno_top_left_y")
        self.lyt_pos_inicial_2.addWidget(self.txtno_top_left_y)
        self.lyt_posicion_select.addLayout(self.lyt_pos_inicial_2)
        self.lyt_pos_final_2 = QtWidgets.QHBoxLayout()
        self.lyt_pos_final_2.setObjectName("lyt_pos_final_2")
        self.lblno_bot_right_final = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblno_bot_right_final.sizePolicy().hasHeightForWidth())
        self.lblno_bot_right_final.setSizePolicy(sizePolicy)
        self.lblno_bot_right_final.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblno_bot_right_final.setObjectName("lblno_bot_right_final")
        self.lyt_pos_final_2.addWidget(self.lblno_bot_right_final)
        self.lblno_bot_rightx = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblno_bot_rightx.sizePolicy().hasHeightForWidth())
        self.lblno_bot_rightx.setSizePolicy(sizePolicy)
        self.lblno_bot_rightx.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblno_bot_rightx.setObjectName("lblno_bot_rightx")
        self.lyt_pos_final_2.addWidget(self.lblno_bot_rightx)
        self.txtno_bot_right_x = QtWidgets.QLineEdit(parent=Buscador)
        self.txtno_bot_right_x.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtno_bot_right_x.sizePolicy().hasHeightForWidth())
        self.txtno_bot_right_x.setSizePolicy(sizePolicy)
        self.txtno_bot_right_x.setInputMask("")
        self.txtno_bot_right_x.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.txtno_bot_right_x.setObjectName("txtno_bot_right_x")
        self.lyt_pos_final_2.addWidget(self.txtno_bot_right_x)
        self.lblno_bot_righty = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblno_bot_righty.sizePolicy().hasHeightForWidth())
        self.lblno_bot_righty.setSizePolicy(sizePolicy)
        self.lblno_bot_righty.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblno_bot_righty.setObjectName("lblno_bot_righty")
        self.lyt_pos_final_2.addWidget(self.lblno_bot_righty)
        self.txtno_bot_right_y = QtWidgets.QLineEdit(parent=Buscador)
        self.txtno_bot_right_y.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtno_bot_right_y.sizePolicy().hasHeightForWidth())
        self.txtno_bot_right_y.setSizePolicy(sizePolicy)
        self.txtno_bot_right_y.setInputMask("")
        self.txtno_bot_right_y.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.txtno_bot_right_y.setObjectName("txtno_bot_right_y")
        self.lyt_pos_final_2.addWidget(self.txtno_bot_right_y)
        self.lyt_posicion_select.addLayout(self.lyt_pos_final_2)
        
        
        
        self.lyt_confidence_2 = QtWidgets.QHBoxLayout()
        self.lyt_confidence_2.setObjectName("lyt_confidence_2")
        self.lblno_confidence = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblno_confidence.sizePolicy().hasHeightForWidth())
        self.lblno_confidence.setSizePolicy(sizePolicy)
        self.lblno_confidence.setObjectName("lblno_confidence")
        self.lyt_confidence_2.addWidget(self.lblno_confidence)
        self.txtno_confidence = QtWidgets.QLineEdit(parent=Buscador)
        self.txtno_confidence.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtno_confidence.sizePolicy().hasHeightForWidth())
        self.txtno_confidence.setSizePolicy(sizePolicy)
        self.txtno_confidence.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.txtno_confidence.setObjectName("txtno_confidence")
        self.lyt_confidence_2.addWidget(self.txtno_confidence)
        self.lyt_posicion_select.addLayout(self.lyt_confidence_2)
        
        
        self.lyt_up_pos.addLayout(self.lyt_posicion_select)
        self.lyt_op_posiciones = QtWidgets.QVBoxLayout()
        self.lyt_op_posiciones.setContentsMargins(5, 0, 5, 0)
        self.lyt_op_posiciones.setObjectName("lyt_op_posiciones")
        self.btn_add_pos = QtWidgets.QPushButton(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_add_pos.sizePolicy().hasHeightForWidth())
        self.btn_add_pos.setSizePolicy(sizePolicy)
        self.btn_add_pos.setObjectName("btn_add_pos")
        self.lyt_op_posiciones.addWidget(self.btn_add_pos)
        self.btn_mod_pos = QtWidgets.QPushButton(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_mod_pos.sizePolicy().hasHeightForWidth())
        self.btn_mod_pos.setSizePolicy(sizePolicy)
        self.btn_mod_pos.setObjectName("btn_mod_pos")
        self.lyt_op_posiciones.addWidget(self.btn_mod_pos)
        self.btn_remover = QtWidgets.QPushButton(parent=Buscador)
        self.btn_remover.setObjectName("btn_remover")
        self.lyt_op_posiciones.addWidget(self.btn_remover)
        self.lyt_up_pos.addLayout(self.lyt_op_posiciones)
        self.lyt_pos_info = QtWidgets.QVBoxLayout()
        self.lyt_pos_info.setContentsMargins(5, -1, 5, -1)
        self.lyt_pos_info.setObjectName("lyt_pos_info")
        self.lyt_nombre = QtWidgets.QHBoxLayout()
        self.lyt_nombre.setObjectName("lyt_nombre")
        self.lbl_nombre = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_nombre.sizePolicy().hasHeightForWidth())
        self.lbl_nombre.setSizePolicy(sizePolicy)
        self.lbl_nombre.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_nombre.setObjectName("lbl_nombre")
        self.lyt_nombre.addWidget(self.lbl_nombre)
        self.txt_nombre = QtWidgets.QLineEdit(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_nombre.sizePolicy().hasHeightForWidth())
        self.txt_nombre.setSizePolicy(sizePolicy)
        self.txt_nombre.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.txt_nombre.setObjectName("txt_nombre")
        self.lyt_nombre.addWidget(self.txt_nombre)
        self.lyt_pos_info.addLayout(self.lyt_nombre)
        self.lyt_pos_inicial = QtWidgets.QHBoxLayout()
        self.lyt_pos_inicial.setObjectName("lyt_pos_inicial")
        self.lbl_top_left_inicial = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_top_left_inicial.sizePolicy().hasHeightForWidth())
        self.lbl_top_left_inicial.setSizePolicy(sizePolicy)
        self.lbl_top_left_inicial.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_top_left_inicial.setObjectName("lbl_top_left_inicial")
        self.lyt_pos_inicial.addWidget(self.lbl_top_left_inicial)
        
        self.btn_inicial = QtWidgets.QPushButton(parent=Buscador)
        self.btn_inicial.setText("")
        self.btn_inicial.setObjectName("btn_inicial")
        self.btn_inicial.setIcon(QIcon("crosshair.png"))
        self.lyt_pos_inicial.addWidget(self.btn_inicial)
        self.lbl_top_leftx = QtWidgets.QLabel(parent=Buscador)
        
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_top_leftx.sizePolicy().hasHeightForWidth())
        self.lbl_top_leftx.setSizePolicy(sizePolicy)
        self.lbl_top_leftx.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_top_leftx.setObjectName("lbl_top_leftx")
        self.lyt_pos_inicial.addWidget(self.lbl_top_leftx)
        self.txt_top_left_x = QtWidgets.QLineEdit(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_top_left_x.sizePolicy().hasHeightForWidth())
        self.txt_top_left_x.setSizePolicy(sizePolicy)
        self.txt_top_left_x.setInputMask("")
        self.txt_top_left_x.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.txt_top_left_x.setObjectName("txt_top_left_x")
        self.txt_top_left_x.setValidator(QIntValidator(0,9999))
        self.lyt_pos_inicial.addWidget(self.txt_top_left_x)
        self.lbl_top_lefty = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_top_lefty.sizePolicy().hasHeightForWidth())
        self.lbl_top_lefty.setSizePolicy(sizePolicy)
        self.lbl_top_lefty.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_top_lefty.setObjectName("lbl_top_lefty")
        self.lyt_pos_inicial.addWidget(self.lbl_top_lefty)
        self.txt_top_left_y = QtWidgets.QLineEdit(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_top_left_y.sizePolicy().hasHeightForWidth())
        self.txt_top_left_y.setSizePolicy(sizePolicy)
        self.txt_top_left_y.setInputMask("")
        self.txt_top_left_y.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.txt_top_left_y.setObjectName("txt_top_left_y")
        self.txt_top_left_y.setValidator(QIntValidator(0,9999))
        self.lyt_pos_inicial.addWidget(self.txt_top_left_y)
        self.lyt_pos_info.addLayout(self.lyt_pos_inicial)
        self.lyt_pos_final = QtWidgets.QHBoxLayout()
        self.lyt_pos_final.setObjectName("lyt_pos_final")
        self.lbl_bot_right_final = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_bot_right_final.sizePolicy().hasHeightForWidth())
        self.lbl_bot_right_final.setSizePolicy(sizePolicy)
        self.lbl_bot_right_final.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_bot_right_final.setObjectName("lbl_bot_right_final")
        self.lyt_pos_final.addWidget(self.lbl_bot_right_final)
        self.lbl_bot_rightx = QtWidgets.QLabel(parent=Buscador)
        
        self.btn_final = QtWidgets.QPushButton(parent=Buscador)
        self.btn_final.setText("")
        self.btn_final.setObjectName("btn_final")
        self.btn_final.setIcon(QIcon("crosshair.png"))

        self.lyt_pos_final.addWidget(self.btn_final)
        
        
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_bot_rightx.sizePolicy().hasHeightForWidth())
        self.lbl_bot_rightx.setSizePolicy(sizePolicy)
        self.lbl_bot_rightx.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_bot_rightx.setObjectName("lbl_bot_rightx")
        self.lyt_pos_final.addWidget(self.lbl_bot_rightx)
        self.txt_bot_right_x = QtWidgets.QLineEdit(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_bot_right_x.sizePolicy().hasHeightForWidth())
        self.txt_bot_right_x.setSizePolicy(sizePolicy)
        self.txt_bot_right_x.setInputMask("")
        self.txt_bot_right_x.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.txt_bot_right_x.setObjectName("txt_bot_right_x")
        self.txt_bot_right_x.setValidator(QIntValidator(0,9999))
        self.lyt_pos_final.addWidget(self.txt_bot_right_x)
        self.lbl_bot_righty = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_bot_righty.sizePolicy().hasHeightForWidth())
        self.lbl_bot_righty.setSizePolicy(sizePolicy)
        self.lbl_bot_righty.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_bot_righty.setObjectName("lbl_bot_righty")
        self.lyt_pos_final.addWidget(self.lbl_bot_righty)
        self.txt_bot_right_y = QtWidgets.QLineEdit(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_bot_right_y.sizePolicy().hasHeightForWidth())
        self.txt_bot_right_y.setSizePolicy(sizePolicy)
        self.txt_bot_right_y.setInputMask("")
        self.txt_bot_right_y.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.txt_bot_right_y.setObjectName("txt_bot_right_y")
        self.txt_bot_right_y.setValidator(QIntValidator(0,9999))
        self.lyt_pos_final.addWidget(self.txt_bot_right_y)
        
        
        self.lyt_pos_info.addLayout(self.lyt_pos_final)
        self.lyt_confidence = QtWidgets.QHBoxLayout()
        self.lyt_confidence.setObjectName("lyt_confidence")
        self.lbl_confidence = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_confidence.sizePolicy().hasHeightForWidth())
        self.lbl_confidence.setSizePolicy(sizePolicy)
        self.lbl_confidence.setObjectName("lbl_confidence")
        self.lyt_confidence.addWidget(self.lbl_confidence)
        self.txt_confidence = QtWidgets.QLineEdit(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txt_confidence.sizePolicy().hasHeightForWidth())
        self.txt_confidence.setSizePolicy(sizePolicy)
        self.txt_confidence.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.txt_top_left_x.setValidator(QIntValidator(0,999999))


        self.txt_confidence.setMaxLength(9)
        
        
        self.lyt_confidence.addWidget(self.txt_confidence)
        self.lyt_pos_info.addLayout(self.lyt_confidence)
        
        
        
        self.lyt_up_pos.addLayout(self.lyt_pos_info)
        self.lyt_main.addLayout(self.lyt_up_pos)
        self.lyt_imagenes = QtWidgets.QHBoxLayout()
        self.lyt_imagenes.setObjectName("lyt_imagenes")
        self.lyt_img_buscar = QtWidgets.QVBoxLayout()
        self.lyt_img_buscar.setObjectName("lyt_img_buscar")
        self.lbl_img_buscar = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_img_buscar.sizePolicy().hasHeightForWidth())
        self.lbl_img_buscar.setSizePolicy(sizePolicy)
        self.lbl_img_buscar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_img_buscar.setObjectName("lbl_img_buscar")
        self.lyt_img_buscar.addWidget(self.lbl_img_buscar)
        self.lw_img_buscar = QtWidgets.QListWidget(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lw_img_buscar.sizePolicy().hasHeightForWidth())
        self.lw_img_buscar.setSizePolicy(sizePolicy)
        self.lw_img_buscar.setObjectName("lw_img_buscar")
        self.lyt_img_buscar.addWidget(self.lw_img_buscar)
        self.lyt_imagenes.addLayout(self.lyt_img_buscar)
        self.lyt_op_img = QtWidgets.QVBoxLayout()
        self.lyt_op_img.setContentsMargins(5, 0, 5, 0)
        self.lyt_op_img.setObjectName("lyt_op_img")
        self.btn_agregar_imagen = QtWidgets.QPushButton(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_agregar_imagen.sizePolicy().hasHeightForWidth())
        self.btn_agregar_imagen.setSizePolicy(sizePolicy)
        self.btn_agregar_imagen.setObjectName("btn_agregar_imagen")
        self.lyt_op_img.addWidget(self.btn_agregar_imagen)
        self.btn_remover_imagen = QtWidgets.QPushButton(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_remover_imagen.sizePolicy().hasHeightForWidth())
        self.btn_remover_imagen.setSizePolicy(sizePolicy)
        self.btn_remover_imagen.setObjectName("btn_remover_imagen")
        self.lyt_op_img.addWidget(self.btn_remover_imagen)
        self.rb_activado = QtWidgets.QRadioButton(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.rb_activado.sizePolicy().hasHeightForWidth())
        self.rb_activado.setSizePolicy(sizePolicy)
        self.rb_activado.setObjectName("rb_activado")
        self.rb_activado.setEnabled(False)
        self.lyt_op_img.addWidget(self.rb_activado)
        self.Subir_imagen = QtWidgets.QPushButton(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.Subir_imagen.sizePolicy().hasHeightForWidth())
        self.Subir_imagen.setSizePolicy(sizePolicy)
        self.Subir_imagen.setObjectName("Subir_imagen")
        self.lyt_op_img.addWidget(self.Subir_imagen)
        self.btn_cambiar_nombre = QtWidgets.QPushButton(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btn_cambiar_nombre.sizePolicy().hasHeightForWidth())
        self.btn_cambiar_nombre.setSizePolicy(sizePolicy)
        self.btn_cambiar_nombre.setObjectName("btn_cambiar_nombre")
        self.lyt_op_img.addWidget(self.btn_cambiar_nombre)
        self.btn_stop_all = QtWidgets.QPushButton(parent=Buscador)
        self.btn_stop_all.setObjectName("btn_stop_all")
        self.lyt_op_img.addWidget(self.btn_stop_all)
        self.lyt_imagenes.addLayout(self.lyt_op_img)
        self.lyt_img_guardadas = QtWidgets.QVBoxLayout()
        self.lyt_img_guardadas.setObjectName("lyt_img_guardadas")
        self.lbl_img_guardadas = QtWidgets.QLabel(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lbl_img_guardadas.sizePolicy().hasHeightForWidth())
        self.lbl_img_guardadas.setSizePolicy(sizePolicy)
        self.lbl_img_guardadas.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lbl_img_guardadas.setObjectName("lbl_img_guardadas")
        self.lyt_img_guardadas.addWidget(self.lbl_img_guardadas)
        self.lw_img_guardadas = QtWidgets.QListWidget(parent=Buscador)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lw_img_guardadas.sizePolicy().hasHeightForWidth())
        self.lw_img_guardadas.setSizePolicy(sizePolicy)
        self.lw_img_guardadas.setObjectName("lw_img_guardadas")
        # Set up a QFileSystemWatcher to monitor the folder
        self.watcher = QFileSystemWatcher(Buscador)
        self.watcher.directoryChanged.connect(self.cambios_carpeta_imagen)
        self.watcher.addPath(img_path) 
        self.lw_img_guardadas.clear()
        self.lw_img_guardadas.addItems(file_names)  

        self.lyt_img_guardadas.addWidget(self.lw_img_guardadas)
        
        #self.lw_img_guardadas.setModel(self.img_saved_model)

        self.lyt_imagenes.addLayout(self.lyt_img_guardadas)
        self.lyt_main.addLayout(self.lyt_imagenes)
        self.gridLayout.addLayout(self.lyt_main, 0, 0, 1, 1)
        self.lbl_nombre.setBuddy(self.txt_nombre)
        self.lbl_top_left_inicial.setBuddy(self.txt_top_left_x)
        self.lbl_top_leftx.setBuddy(self.txt_top_left_x)
        self.lbl_top_lefty.setBuddy(self.txt_top_left_y)
        self.lbl_bot_right_final.setBuddy(self.txt_bot_right_x)
        self.lbl_bot_rightx.setBuddy(self.txt_bot_right_x)
        self.lbl_bot_righty.setBuddy(self.txt_bot_right_y)

        self.retranslateUi(Buscador)
        self.btn_add_pos.clicked.connect(self.add_pos) # type: ignore
        self.btn_mod_pos.clicked.connect(self.mod_pos) # type: ignore
        self.btn_agregar_imagen.clicked.connect(self.add_img) # type: ignore
        self.btn_remover_imagen.clicked.connect(self.rem_img) # type: ignore
        self.Subir_imagen.clicked.connect(self.subir_img) # type: ignore
        self.btn_cambiar_nombre.clicked.connect(self.mod_img_nombre) # type: ignore
        self.cb_posicion.currentIndexChanged['int'].connect(self.cambio_espacio) # type: ignore
        #self.lw_img_buscar.addItem("asd")
        self.rb_activado.clicked.connect(self.activar) # type: ignore
        self.btn_stop_all.clicked.connect(self.stop_all) # type: ignore
        self.btn_remover.clicked.connect(self.remover) # type: ignore
        self.btn_inicial.clicked.connect(lambda: self.mouse_store_start(0)) # type: ignore
        self.btn_final.clicked.connect(lambda: self.mouse_store_start(1)) # type: ignore
        self.txt_top_left_x.textChanged.connect(self.check_txt_empty)
        self.txt_top_left_y.textChanged.connect(self.check_txt_empty)
        self.txt_bot_right_x.textChanged.connect(self.check_txt_empty)
        self.txt_bot_right_y.textChanged.connect(self.check_txt_empty)
        self.txt_confidence.textChanged.connect(self.check_txt_empty)
        QtCore.QMetaObject.connectSlotsByName(Buscador)
        Buscador.setTabOrder(self.txt_nombre, self.txt_top_left_x)
        Buscador.setTabOrder(self.txt_top_left_x, self.txt_bot_right_x)
        Buscador.setTabOrder(self.txt_bot_right_x, self.txt_top_left_y)
        Buscador.setTabOrder(self.txt_top_left_y, self.txt_bot_right_y)
        Buscador.setTabOrder(self.txt_bot_right_y, self.btn_add_pos)
        Buscador.setTabOrder(self.btn_add_pos, self.btn_mod_pos)
        Buscador.setTabOrder(self.btn_mod_pos, self.btn_remover)
        Buscador.setTabOrder(self.btn_remover, self.cb_posicion)
        Buscador.setTabOrder(self.cb_posicion, self.btn_agregar_imagen)
        Buscador.setTabOrder(self.btn_agregar_imagen, self.btn_remover_imagen)
        Buscador.setTabOrder(self.btn_remover_imagen, self.rb_activado)
        Buscador.setTabOrder(self.rb_activado, self.Subir_imagen)
        Buscador.setTabOrder(self.Subir_imagen, self.btn_cambiar_nombre)
        Buscador.setTabOrder(self.btn_cambiar_nombre, self.btn_stop_all)
        Buscador.setTabOrder(self.btn_stop_all, self.lw_img_buscar)
        Buscador.setTabOrder(self.lw_img_buscar, self.lw_img_guardadas)
        Buscador.setTabOrder(self.lw_img_guardadas, self.txtno_top_left_x)
        Buscador.setTabOrder(self.txtno_top_left_x, self.txtno_top_left_y)
        Buscador.setTabOrder(self.txtno_top_left_y, self.txtno_bot_right_x)
        Buscador.setTabOrder(self.txtno_bot_right_x, self.txtno_bot_right_y)
        Buscador.setTabOrder(self.txtno_bot_right_y, self.btn_inicial)
        Buscador.setTabOrder(self.btn_inicial, self.btn_final)
        Buscador.setTabOrder(self.btn_final, self.txt_confidence)
    
    def retranslateUi(self, Buscador):
    
        _translate = QtCore.QCoreApplication.translate
        Buscador.setWindowTitle(_translate("Buscador", "Buscador Imagenes - Lucas Silva"))
        self.cb_posicion.setCurrentText(_translate("Buscador", "Inicial"))
        self.cb_posicion.setItemText(0, _translate("Buscador", "Inicial"))
        self.cb_posicion.setItemText(self.cb_posicion.currentIndex(),self.lista_nombres[self.cb_index]+"     "+str(self.lista_posiciones[self.cb_index][0])+" "+str(self.lista_posiciones[self.cb_index][1])+" "+str(self.lista_posiciones[self.cb_index][2])+" "+str(self.lista_posiciones[self.cb_index][3]))

        self.lblno_top_left_inicial.setText(_translate("Buscador", "Inicial"))
        self.lblno_top_leftx.setText(_translate("Buscador", "x"))
        self.txtno_top_left_x.setText(_translate("Buscador", "0"))
        self.lblno_top_lefty.setText(_translate("Buscador", "y"))
        self.txtno_top_left_y.setText(_translate("Buscador", "0"))
        self.lblno_bot_right_final.setText(_translate("Buscador", "Final  "))
        self.lblno_bot_rightx.setText(_translate("Buscador", "x"))
        self.txtno_bot_right_x.setText(_translate("Buscador", "1366"))
        self.lblno_bot_righty.setText(_translate("Buscador", "y"))
        self.txtno_bot_right_y.setText(_translate("Buscador", "768"))
        self.btn_add_pos.setText(_translate("Buscador", "Añadir espacio"))
        self.btn_mod_pos.setText(_translate("Buscador", "Modificar"))
        self.btn_remover.setText(_translate("Buscador", "Remover"))
        self.lbl_nombre.setText(_translate("Buscador", "Nombre"))
        self.lbl_top_left_inicial.setText(_translate("Buscador", "Inicial"))
        self.lbl_top_leftx.setText(_translate("Buscador", "x"))
        self.txt_top_left_x.setText(_translate("Buscador", "0"))
        self.lbl_top_lefty.setText(_translate("Buscador", "y"))
        self.txt_top_left_y.setText(_translate("Buscador", "0"))
        self.lbl_bot_right_final.setText(_translate("Buscador", "Final  "))
        self.lbl_bot_rightx.setText(_translate("Buscador", "x"))
        self.txt_bot_right_x.setText(_translate("Buscador", "1366"))
        self.lbl_bot_righty.setText(_translate("Buscador", "y"))
        self.txt_bot_right_y.setText(_translate("Buscador", "768"))
        self.lbl_img_buscar.setText(_translate("Buscador", "Imagenes a buscar"))
        self.btn_agregar_imagen.setText(_translate("Buscador", "Agregar +"))
        self.btn_remover_imagen.setText(_translate("Buscador", "Remover -"))
        self.rb_activado.setText(_translate("Buscador", "Activado"))
        self.Subir_imagen.setText(_translate("Buscador", "Subir imagen"))
        self.btn_cambiar_nombre.setText(_translate("Buscador", "Cambiar nombre"))
        self.btn_stop_all.setText(_translate("Buscador", "Parar Todo"))
        self.lbl_img_guardadas.setText(_translate("Buscador", "Imagenes guardadas"))
        self.lbl_confidence.setText(_translate("Buscador", "Similitud (0.0 - 1.0)"))
        self.txt_confidence.setText(_translate("Buscador", "0.9"))
        self.lblno_confidence.setText(_translate("Buscador", "Similitud (0.0 - 1.0)"))
        self.txtno_confidence.setText(_translate("Buscador", "0.9"))

    def check_txt_empty(self,text):
        if not text: #se fija si esta vacio
            sender = self.sender()    #obtiene el objeto que llamo a esta funcion
            sender.setText('0')       #cambia el text a 0  
        
    def add_pos(self):
        #print(self.cb_posicion.count())
        #print(self.cb_posicion.currentIndex())

        self.cb_posicion.addItem(self.txt_nombre.text()+"     "+self.txt_top_left_x.text()+" "+self.txt_top_left_y.text()+" "+self.txt_bot_right_x.text()+" "+self.txt_bot_right_y.text())       

        self.txtno_top_left_x.setText(self.txt_top_left_x.text())
        self.txtno_top_left_y.setText(self.txt_top_left_y.text())
        self.txtno_bot_right_x.setText(self.txt_bot_right_x.text())
        self.txtno_bot_right_y.setText(self.txt_bot_right_y.text())
        try:
            if float(self.txt_confidence.text())<0 or float(self.txt_confidence.text())>1:
                self.txt_confidence.setText("0.9")
        except:
            self.txt_confidence.setText("0.9")
            
        self.txtno_confidence.setText(self.txt_confidence.text())

        #guarda imagen y posicion
        self.lista_nombres.append(self.txt_nombre.text())
        self.lista_img_buscar.append([])
        self.lista_img.append([])
        self.lista_activado.append(False)
        self.lista_posiciones.append([int(self.txt_top_left_x.text()), int(self.txt_top_left_y.text()), int(self.txt_bot_right_x.text()), int(self.txt_bot_right_y.text())])
        self.lista_confidence.append(self.txt_confidence.text())
        self.cb_posicion.setCurrentIndex(self.cb_posicion.count()-1)
        self.rb_activado.setChecked(False)
        self.rb_activado.setEnabled(False)
        self.cambiar_si_inicial_mayor_final()

        # count empieza en 1, currentIndex en 0
    
    def mod_pos(self):  

        self.cb_posicion.setItemText(self.cb_posicion.currentIndex(),self.txt_nombre.text()+"     "+self.txt_top_left_x.text()+" "+self.txt_top_left_y.text()+" "+self.txt_bot_right_x.text()+" "+self.txt_bot_right_y.text())
                
        self.lista_posiciones[self.cb_index][0]=int(self.txt_top_left_x.text())
        self.lista_posiciones[self.cb_index][1]=int(self.txt_top_left_y.text())
        self.lista_posiciones[self.cb_index][2]=int(self.txt_bot_right_x.text())
        self.lista_posiciones[self.cb_index][3]=int(self.txt_bot_right_y.text())
        if float(self.txt_confidence.text())<0.0 or float(self.txt_confidence.text())>1.0:
            self.txt_confidence.setText("0.9")
        self.lista_confidence[self.cb_index]=self.txt_confidence.text()
        self.lista_nombres[self.cb_index]=self.txt_nombre.text()
        
        self.txtno_top_left_x.setText(self.txt_top_left_x.text())
        self.txtno_top_left_y.setText(self.txt_top_left_y.text())
        self.txtno_bot_right_x.setText(self.txt_bot_right_x.text())
        self.txtno_bot_right_y.setText(self.txt_bot_right_y.text())
        self.txtno_confidence.setText(self.txt_confidence.text())
        self.cambiar_si_inicial_mayor_final()
 
    def remover(self):
        index = self.cb_posicion.currentIndex()
        self.cb_posicion.removeItem(index)

        if len(self.lista_img_buscar)>1:
            self.lista_img_buscar.pop(index)
            self.lista_img.pop(index)
            self.lista_posiciones.pop(index)
            self.lista_activado.pop(index)
            self.lista_confidence.pop(index)

    def add_img(self):
        if (self.lw_img_guardadas.currentItem()!=None):
            selected_item = self.lw_img_guardadas.currentItem()
            text=selected_item.text()
            existe=False
            for item in self.lista_img_buscar[self.cb_index]:
                if text==item:
                    existe=True
            if existe==False:
                self.lw_img_buscar.addItem(text)
                self.lista_img_buscar[self.cb_index].append(selected_item.text())
                self.lista_img[self.cb_index].append(cv2.imread(img_path+selected_item.text()))
                self.rb_activado.setEnabled(True)

    def rem_img(self):

        if (self.lw_img_buscar.currentItem()!=None):
            selected_item = self.lw_img_buscar.currentItem()
            item_row=self.lw_img_buscar.currentRow()
            self.lista_img_buscar[self.cb_index].pop(item_row)
            self.lista_img[self.cb_index].pop(item_row)
            self.lw_img_buscar.takeItem(self.lw_img_buscar.row(selected_item))
            if len(self.lista_img_buscar[self.cb_index])<=0:
                self.rb_activado.setChecked(False)
                self.rb_activado.setEnabled(False)
                self.lista_activado[self.cb_index]=False
        
    def activar(self,checked):
        if checked:
            if self.lista_activado[self.cb_index]==False:
                self.lista_activado[self.cb_index]=True

                if len(self.lista_img[self.cb_index])>0: #se fija si hay imagenes
                    thread = Thread(target=self.detectar_imagenes, args=(self.cb_index,), daemon=True)
                    self.lista_threads.append(thread)
                    thread.start()                    
        else:
            self.lista_activado[self.cb_index]=False

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

        self.lw_img_guardadas.clear()
        self.lw_img_guardadas.addItems(file_names)  
        
    def mod_img_nombre(self):
        if (self.lw_img_buscar.currentItem()!=None):
            selected_item = self.lw_img_buscar.currentItem()
            new_text, ok = QInputDialog.getText(self.lw_img_buscar.parent(), 'Modificar nombre', 'Introduzca el nuevo nombre:', text=selected_item.text())
            if ok:
                os.rename(img_path+selected_item.text(),img_path+new_text)
                selected_item.setText(new_text)
        
    def stop_all(self):
        self.lista_activado=[False] * len(self.lista_activado)
        self.rb_activado.setChecked(False)
    
    def cambio_espacio(self):
        self.lw_img_buscar.clear()
        self.cb_index=self.cb_posicion.currentIndex()
        for item in self.lista_img_buscar[self.cb_index]:
            self.lw_img_buscar.addItem(item)
        self.txtno_top_left_x.setText(str(self.lista_posiciones[self.cb_index][0])) 
        self.txtno_top_left_y.setText(str(self.lista_posiciones[self.cb_index][1])) 
        self.txtno_bot_right_x.setText(str(self.lista_posiciones[self.cb_index][2])) 
        self.txtno_bot_right_y.setText(str(self.lista_posiciones[self.cb_index][3])) 
        self.rb_activado.setChecked(self.lista_activado[self.cb_index]) 
        if len(self.lista_img_buscar[self.cb_index])>0:
            self.rb_activado.setEnabled(True)
        else:
            self.rb_activado.setEnabled(False)



if __name__ == "__main__":
    pausa = mp.Value('b', False)
    salir = mp.Value('b', False)
    point = POINT()
    
    user32 = ctypes.windll.user32
    user32.GetCursorPos(ctypes.byref(point))
    app = QtWidgets.QApplication(sys.argv)
    Buscador = QtWidgets.QWidget()
    ui = Ui_Buscador()
    ui.setupUi(Buscador)
    Buscador.show()
    sys.exit(app.exec())