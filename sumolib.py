import board
import digitalio
import analogio
import pwmio
import neopixel_write
import time

class Color:
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 150, 0)
    CYAN = (0, 255, 255)
    PURPLE = (180, 0, 255)
    WHITE = (255, 255, 255)

class Operation:
    STOP = 'Stop'
    FORWARD = 'Fw'
    BACKWARD = 'Bw'
    BREAK = 'Break'


class Led:
    "Nadklasa dla diod LED1 i LED2"
    
    def __init__(self, pin):
        self._led = digitalio.DigitalInOut(pin)
        self._led.direction = digitalio.Direction.OUTPUT
        
    @property    
    def value(self):
        return self._led.value
    
    @value.setter
    def value(self, val):
        self._led.value = val
        
    def __str__(self):
        return str(self.value)
    
    def __repr__(self):
        return str(self)

class LedRgb:
    "Nadklasa dla diod WS2812B"
    
    def __init__(self, pin):
        self._led = digitalio.DigitalInOut(pin)
        self._led.direction = digitalio.Direction.OUTPUT
        self._brightness = 0.3
    
    def _set_brightness(self, c):
        return int(c * self._brightness)
    
    def _prepare_pixel(self, c):
        if len(c) != 3:
            raise ValueError("Nieprawidlowy format koloru, powinno byc (R, G, B)")
        if c[0] < 0 or c[0] > 255 or c[0] < 0 or c[0] > 255 or c[0] < 0 or c[0] > 255:
            raise ValueError("Nieprawidlowy wartosc koloru, powinno byc 0-255")
        return [self._set_brightness(c[1]), self._set_brightness(c[0]), self._set_brightness(c[2])]
    
    def _set_colors(self, colors):
        arr = []
        for c in colors:
            arr += self._prepare_pixel(c)
        neopixel_write.neopixel_write(self._led, bytearray(arr)) 
    
    @property    
    def brightness(self):
        return self._brightness
    
    @brightness.setter
    def brightness(self, val):
        if val < 0.0 or val > 1.0:
            raise ValueError("Nieprawidlowa wrtosc jasnosci, powinno byc 0.0 - 1.0")
        self._brightness = val
    
    @property    
    def value(self):
        return None
    
    @value.setter
    def value(self, val):
        self._set_colors([val])
        
    @property    
    def values(self):
        return None
    
    @value.setter
    def values(self, val):
        self._set_colors(val)
        

class Button:
    "Nadklasa dla przyciskow START1 i BOOT1"
    
    def __init__(self, pin):
        self._butt = digitalio.DigitalInOut(pin)
        self._butt.direction = digitalio.Direction.INPUT
        self._butt.pull = digitalio.Pull.UP
    
    def waitFor(self):
        while not self.value:
            time.sleep(0.01)
        
    @property    
    def value(self):
        return not self._butt.value
    
    def __str__(self):
        return str(self.value)
    
    def __repr__(self):
        return str(self)


class VBat:
    "Klasa pomiaru napiecia zasilania"
    
    def __init__(self):
        self._adc = analogio.AnalogIn(board.IO1)
        
    @property    
    def value(self):
        return (self._adc.value / 65535 * self._adc.reference_voltage) * ((23.2+2.2) / 2.2)
    
    def __str__(self):
        return str(self.value)
    
    def __repr__(self):
        return str(self)


class Grd:
    "Nadklasa czujnikow podloza"
    
    def __init__(self, pin):
        self._adc = analogio.AnalogIn(pin)
        
    @property    
    def value(self):
        return (self._adc.value / 65535 * self._adc.reference_voltage)
    
    def __str__(self):
        return str(self.value)
    
    def __repr__(self):
        return str(self)
    
    
class Dist:
    "Nadklasa czujnikow odleglosci"
    
    def __init__(self, pin):
        self._adc = analogio.AnalogIn(pin)
        
    @property    
    def value(self):
        return (self._adc.value / 65535 * self._adc.reference_voltage) * 2
    
    def __str__(self):
        return str(self.value)
    
    def __repr__(self):
        return str(self)
    

class Motor:
    "Nadklasa dla sinlnikow DC MOTOR1 i MOTOR2"
    
    def __init__(self, pin_l1, pin_r1, pin_l2, pin_r2):
        self._l1 = pwmio.PWMOut(pin_l1, frequency=500, duty_cycle=65535)
        self._r1 = pwmio.PWMOut(pin_r1, frequency=500, duty_cycle=65535)
        self._l2 = digitalio.DigitalInOut(pin_l2)
        self._l2.direction = digitalio.Direction.OUTPUT
        self._l2.value = True
        self._r2 = digitalio.DigitalInOut(pin_r2)
        self._r2.direction = digitalio.Direction.OUTPUT
        self._r2.value = True
        self._power = 0.4
        self._operation = Operation.STOP
    
    def _do_stop(self):
        self._l1.duty_cycle = 65535
        self._r1.duty_cycle = 65535
        self._l2.value = True
        self._r2.value = True
        
    def _do_forward(self):
        self._l1.duty_cycle = 65535 - int(65535 * self._power)
        self._r1.duty_cycle = 65535
        self._l2.value = True
        self._r2.value = False
        
    def _do_backward(self):
        self._l1.duty_cycle = 65535
        self._r1.duty_cycle = 65535 - int(65535 * self._power)
        self._l2.value = False
        self._r2.value = True
        
    def _do_break(self):
        self._l1.duty_cycle = 65535
        self._r1.duty_cycle = 65535
        self._l2.value = False
        self._r2.value = False
    
    def _set_operation(self, operation):
        # zabezpieczenie przed zwarcie tranzystora
        if self._operation != operation:
            time.sleep(0.005)
        # wykonywanie operacji wlasciwej
        if operation == Operation.STOP:
            self._operation = operation
            self._do_stop()
        elif operation == Operation.FORWARD:
            self._operation = operation
            self._do_forward()
        elif operation == Operation.BACKWARD:
            self._operation = operation
            self._do_backward()
        elif operation == Operation.BREAK:
            self._operation = operation
            self._do_break()
        else:
            raise ValueError("Nieprawidlowa operacja")
    
    @property    
    def power(self):
        return self._power
    
    @power.setter
    def power(self, val):
        if val < 0.0 or val > 1.0:
            raise ValueError("Nieprawidlowa wrtosc mocy, powinno byc 0.0 - 1.0")
        self._power = val
        # aktualizacja
        if self._operation == Operation.FORWARD:
            self._do_forward()
        elif self._operation == Operation.BACKWARD:
            self._do_backward()
 
    @property    
    def operation(self):
        return self._operation
    
    @operation.setter
    def operation(self, val):
        self._set_operation(val)
        
    def stop(self):
        self.operation = Operation.STOP
        
    def forward(self):
        self.operation = Operation.FORWARD
        
    def backward(self):
        self.operation = Operation.BACKWARD
        
    def motorBreak(self):
        self.operation = Operation.BREAK
    
    def __str__(self):
        return self.operation
    
    def __repr__(self):
        return str(self)


class Led1(Led):
    "Dioda LED2"
    
    def __init__(self):
        Led.__init__(self, board.IO41)
    
class Led2(Led):
    "Dioda LED2"
    
    def __init__(self):
        Led.__init__(self, board.IO42)

class LedRgb1(LedRgb):
    "Dioda LED_RGB1"
    
    def __init__(self):
        LedRgb.__init__(self, board.IO21)
        

class Start1(Button):
    "Przycisk START1"
    
    def __init__(self):
        Button.__init__(self, board.IO45)
        
class Boot1(Button):
    "Przycisk BOOT1"
    
    def __init__(self):
        Button.__init__(self, board.IO0)


class Grd1(Grd):
    "Czujnik GRD1"
    
    def __init__(self):
        Grd.__init__(self, board.IO2)
        
class Grd2(Grd):
    "Czujnik GRD2"
    
    def __init__(self):
        Grd.__init__(self, board.IO3)
        
class Grd3(Grd):
    "Czujnik GRD1"
    
    def __init__(self):
        Grd.__init__(self, board.IO4)
        
class Grd4(Grd):
    "Czujnik GRD2"
    
    def __init__(self):
        Grd.__init__(self, board.IO5)
        

class Dist1(Dist):
    "Czujnik DIST1"
    
    def __init__(self):
        Dist.__init__(self, board.IO6)
        
class Dist2(Dist):
    "Czujnik DIST2"
    
    def __init__(self):
        Dist.__init__(self, board.IO7)
        
class Dist3(Dist):
    "Czujnik DIST1"
    
    def __init__(self):
        Dist.__init__(self, board.IO8)
        
class Dist4(Dist):
    "Czujnik DIST2"
    
    def __init__(self):
        Dist.__init__(self, board.IO9)


class Motor1(Motor):
    "Silnik MOTOR1"
    
    def __init__(self):
        Motor.__init__(self, board.IO33, board.IO35, board.IO34, board.IO36)
        
class Motor2(Motor):
    "Silnik MOTOR2"
    
    def __init__(self):
        Motor.__init__(self, board.IO37, board.IO39, board.IO38, board.IO40)
 

def leds_init():
    "Inicjalizuje diody LED1 i LED2"
    return Led1(), Led2()


def buttons_init():
    "Inicjalizuje przyciski START1 i BOOT1"
    return Start1(), Boot1()


def grds_init():
    "Inicjalizuje czujnikow podloza"
    return Grd1(), Grd2(), Grd3(), Grd4()


def dists_init():
    "Inicjalizuje czujnikow odleglosci"
    return Dist1(), Dist2(), Dist3(), Dist4()


def motors_init():
    "Inicjalizuje silniki MOTOR1 i MOTOR2"
    return Motor1(), Motor2()
