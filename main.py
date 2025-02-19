from sumolib import *
import time

# Inicjalizacja komponentów
start1 = Start1()
led1, led2 = Led1(), Led2()
ledRgb1 = LedRgb1()
grds = grds_init()
dists = dists_init()
motor1, motor2 = motors_init()

# Stałe progowe z histerezą
GRD_THRESHOLD = 0.7
GRD_HYSTERESIS = 0.1
DIST_THRESHOLD = 0.5
DIST_HYSTERESIS = 0.15

# Poziomy mocy zależne od stanu
SEARCH_POWER = 0.55
ATTACK_POWER = 0.95
TURN_POWER = 0.75
ESCAPE_POWER = 1.0
CALIBRATION_SAMPLES = 50

# Stany maszyny stanów
STATE_SEARCH = 0
STATE_ATTACK = 1
STATE_ESCAPE = 2
current_state = STATE_SEARCH

# Kalibracja czujników podłoża
def calibrate_grds():
    avg = [0.0]*4
    for _ in range(CALIBRATION_SAMPLES):
        for i in range(4):
            avg[i] += grds[i].value
    for i in range(4):
        avg[i] /= CALIBRATION_SAMPLES
    return avg

grds_calibration = calibrate_grds()

# Funkcje sterujące ruchem
def move(left_power, right_power, color):
    motor1.power = min(abs(left_power), 1.0)
    motor2.power = min(abs(right_power), 1.0)
    motor1.forward() if left_power >= 0 else motor1.backward()
    motor2.forward() if right_power >= 0 else motor2.backward()
    ledRgb1.value = color

def stop():
    motor1.stop()
    motor2.stop()
    ledRgb1.value = Color.GREEN

def countdown():
    for i in range(5, 0, -1):
        print(f'{i}...')
        ledRgb1.value = (255, i * 40, 0)
        time.sleep(0.9)
        ledRgb1.value = (0, 0, 0)
        time.sleep(0.1)
    print("START!")

# Zaawansowana logika unikania krawędzi
def handle_edge(g):
    # Priorytet dla przednich czujników
    if g[0] or g[1]:
        move(-ESCAPE_POWER, -ESCAPE_POWER, Color.RED)
        time.sleep(0.3)
        move(ESCAPE_POWER, -ESCAPE_POWER, Color.YELLOW)
        time.sleep(0.4)
    elif g[2]:
        move(ESCAPE_POWER * 1.2, -ESCAPE_POWER, Color.YELLOW)
    elif g[3]:
        move(-ESCAPE_POWER, ESCAPE_POWER * 1.2, Color.YELLOW)
    return True

# Agresywna strategia ataku
def handle_attack(d):
    global current_state
    if d[0] and d[1]:
        move(ATTACK_POWER, ATTACK_POWER, Color.WHITE)
    elif d[0]:
        move(ATTACK_POWER * 0.9, ATTACK_POWER * 1.1, Color.WHITE)
    elif d[1]:
        move(ATTACK_POWER * 1.1, ATTACK_POWER * 0.9, Color.WHITE)
    else:
        current_state = STATE_SEARCH

# Inteligentne przeszukiwanie
search_direction = 1
def handle_search():
    global search_direction, current_state
    # Zmiana kierunku co 3 sekundy
    if time.monotonic() % 6 < 0.1:
        search_direction *= -1
        
    move(SEARCH_POWER, SEARCH_POWER * 0.4 * search_direction, Color.CYAN)
    
    # Skanowanie pionowe
    if time.monotonic() % 2 < 0.1:
        move(SEARCH_POWER * 0.7, -SEARCH_POWER * 0.7, Color.BLUE)
        time.sleep(0.2)

# Główna decyzja
def decide():
    global current_state
    
    # Odczyt z kalibracją
    g = [grds[i].value < (grds_calibration[i] - GRD_THRESHOLD) for i in range(4)]
    d = [dists[i].value > DIST_THRESHOLD for i in range(4)]
    
    # Aktualizacja diod krawędzi
    led1.value, led2.value = g[0], g[1]

    # Maszyna stanów
    if any(g):
        current_state = STATE_ESCAPE
    elif any(d[:2]):  # Tylko przednie czujniki
        current_state = STATE_ATTACK
    else:
        current_state = STATE_SEARCH

    # Obsługa stanów
    if current_state == STATE_ESCAPE:
        if handle_edge(g):
            return
    elif current_state == STATE_ATTACK:
        handle_attack(d)
    else:
        handle_search()

# Start programu
print("Kalibracja...")
grds_calibration = calibrate_grds()
print("Oczekiwanie na start...")
ledRgb1.value = Color.PURPLE
start1.waitFor()
countdown()

# Główna pętla
last_battery_check = time.monotonic()
while True:
    # Kontrola baterii co 10s
    if time.monotonic() - last_battery_check > 10:
        if VBat().value < 6.5:
            SEARCH_POWER *= 0.8
            ATTACK_POWER *= 0.9
        last_battery_check = time.monotonic()
    
    decide()
    time.sleep(0.01)