#wireless
import machine, network, urequests
#
from machine import Pin
from DHT22 import PicoDHT22
from dht import DHT11
from time import sleep


#dht_sensor=DHT22(Pin(15),dht11=True) // mal
dht_sensor=PicoDHT22(Pin(15,Pin.IN,Pin.PULL_UP),dht11=True)

# datos de red
ssid = 'NETAAE'
password = '1709495699.'

def connect():
    #Connect to WLAN
    red = network.WLAN(network.STA_IF)
    red.active(True)
    red.connect(ssid, password)
    while red.isconnected() == False:
        print('Esperando conexión ...')
        sleep(1)
    print(red.ifconfig())
    print('Conexión correcta - '+ ssid)

try:
    connect()
except KeyboardInterrupt:
    machine.reset()

ultima_peticion = 0
intervalo_peticiones = 30



while True:

    T, H = dht_sensor.read()

    if T is None:
        print("¡Error en el sensor!")
    else:
        print("{}'C  {}%".format(T,H))

    sleep(1)