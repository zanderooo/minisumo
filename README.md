# minisumo
minisumo

pip install esptool

pip install mpy-cross

pip install rshell



esptool.py --port /dev/ttyUSB0 erase_flash

esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 firmware.bin



rshell --port /dev/ttyUSB0

cp sumolib.py /pyboard/
cp main.py /pyboard/


rshell --port /dev/ttyUSB0 repl
