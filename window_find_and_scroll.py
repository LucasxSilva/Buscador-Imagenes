import pygetwindow as gw
from time import sleep
import pyautogui

def scroll_window(nexusmod_window):
    contador=0
    scroll_cantidad = -350
    while nexusmod_window != []:
        try:
            nexusmod_window[0].activate()  # bring to the front
        except:
            break
        pyautogui.scroll(scroll_cantidad)
        contador+=1
        nexusmod_window = gw.getWindowsWithTitle("Browser Window")
        if contador == 9:      #cambia entre scroll hacia abajo o arriba
            scroll_cantidad*=-1
            contador=0
        sleep(1)


def buscar_window():
    try:
        nexusmod_window = []
        while nexusmod_window == []:    #busca ventana
            nexusmod_window = gw.getWindowsWithTitle("Browser Window")
            if nexusmod_window != []:

                mouse_position = (nexusmod_window[0].width/2, nexusmod_window[0].top + nexusmod_window[0].height /2)
                pyautogui.moveTo(*mouse_position)
                scroll_window(nexusmod_window)                  # Scroll the window by moving the mouse and scrolling
            
                sleep(7)        #minimo tiempo inactivo
    except KeyboardInterrupt:
        print("Execution interrupted by user ctrl+c.")

if __name__ == "__main__":
    while True:
        buscar_window()
        sleep(4)    #tiempo inactivo

            #print("hecho")
            #nexusmod_window[0].maximize()
            #nexusmod_window[0].restore()
            #nexusmod_window[0].move(0,+550)
            #nexusmod_window[0].resizeTo(800, 768)  