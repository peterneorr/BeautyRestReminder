import RPi.GPIO as GPIO
import sys,time
from datetime import datetime,timedelta 
import json



GPIO.setwarnings(False)

#byte patterns for 7segment led digits 0-F
digits = [0x3f, 0x06, 0x5b, 0x4f, 0x66, 0x6d, 0x7d, 0x07, 0x7f, 0x6f, 0x77, 0x7c, 0x39, 0x5e, 0x79, 0x71 ]

#byte pattern for a decimal point
DECIMAL = 0x80

#wait this long after digit led updates
delay =.005

TIME="TIME"
SLEEP="SLEEP"
WAKE="WAKE"

modes=[TIME,SLEEP,WAKE]
currentMode = TIME

#returns ms since the epoch
def millis():
        return time.time() * 1000

#voodoo magic
# find the diff between last wake up time, and now.
# add that diff to 24 ours from right now, and this is the next wakeup time.
def next_wake_time():
    now = datetime.now()
    waketime =  now + (timedelta(hours=24) - 
        (now - now.replace(hour=wake_hour, minute=wake_min, second=0, microsecond=0)))
    return waketime


def is_time_to_cycle(now_ms,last_ms):
    if config:
        return False
    if (now_ms-last_ms>5000):
        return True
    return False

def cycle_mode(ms_now):
    global currentMode
    global lastcycle
    lastcycle=ms_now
    if config or is_button_down():
        return    
    if currentMode==TIME:
        currentMode=SLEEP        
    elif currentMode==SLEEP: 
        currentMode=WAKE
    elif currentMode==WAKE: 
        currentMode=TIME
    #print(currentMode)    

# the "go to next function" button
    #press to go to next mode
    #hold to enter set mode.

a_down_at = False
b_down_at = False

def buttonA_callback(channel):    
    global a_down_at    
    if GPIO.input(channel):        
        a_down_at = millis()
    else:         
        if (config and a_down_at ):
            hour_up()
        else:            
            cycle_mode(millis())

def hour_up():
    global wake_hour
    if (not config):
        return
    wake_hour +=1
    if wake_hour>23:
        wake_hour=0

def min_up():
    global wake_min
    if (not config):
        return
    wake_min +=1
    if wake_min >59:
        wake_min = 0

def is_button_down():
    return GPIO.input(PIN_BUTTONA) or  GPIO.input(PIN_BUTTONB)

config = False
def checkForLongPress():
    global a_down_at
    global b_down_at
    global config
    
    if not (a_down_at or b_down_at):
        return
    
    now = millis()    
    if (config or currentMode==WAKE and a_down_at):
        if GPIO.input(PIN_BUTTONA) and (now - a_down_at) > 2000 :        
            config = not config
            if not config:
                save_data()
            #print('config mode is now {}'.format(config))        
            a_down_at = False
    if (b_down_at and not config):
        if GPIO.input(PIN_BUTTONB) and (now - b_down_at) > 2000 :                    
            b_down_at = False
            easter_egg()

# the other button.
# adjust the minute... or hold for a suprise
def buttonB_callback(channel):
    global b_down_at
    #print("Button B !")  
    if GPIO.input(channel):        
        b_down_at = millis()
    else: 
        #button up
        if (config):
            min_up()
        else:
            b_down_at=False
    
def easter_egg():
    #print("suprise!")
    for y in [1,2,3,4]:        
        select_digit(y)
        for x in [1,2,4,8,16,32]:                       
            shift_out(x)                        
            time.sleep(.100)
            
        

GPIO.setmode(GPIO.BCM)
PIN_BLUE = 11
PIN_GREEN = 9
PIN_RED = 10

PIN_LED_TIME  = 4
PIN_LED_SLEEP  = 3
PIN_LED_WAKE  = 2
GPIO.setup(PIN_LED_TIME,  GPIO.OUT)
GPIO.setup(PIN_LED_SLEEP,  GPIO.OUT)
GPIO.setup(PIN_LED_WAKE,  GPIO.OUT)
GPIO.setup(PIN_RED,  GPIO.OUT)
GPIO.setup(PIN_GREEN,  GPIO.OUT)
GPIO.setup(PIN_BLUE,  GPIO.OUT)

PIN_BUTTONA  = 7
PIN_BUTTONB  = 8
GPIO.setup(PIN_BUTTONA,  GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(PIN_BUTTONA,GPIO.BOTH,callback=buttonA_callback,bouncetime=20) # Setup event on pin rising edge
GPIO.setup(PIN_BUTTONB,  GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.add_event_detect(PIN_BUTTONB,GPIO.RISING,callback=buttonB_callback,bouncetime=20) # Setup event on pin rising edge

PIN_DATA  = 17
PIN_LATCH = 27
PIN_CLOCK = 22
PIN_D1 = 25
PIN_D2 = 24
PIN_D3 = 23
PIN_D4 = 18

GPIO.setup(PIN_D1,  GPIO.OUT)
GPIO.setup(PIN_D2,  GPIO.OUT)
GPIO.setup(PIN_D3,  GPIO.OUT)
GPIO.setup(PIN_D4,  GPIO.OUT)
GPIO.setup(PIN_DATA,  GPIO.OUT)
GPIO.setup(PIN_LATCH, GPIO.OUT)
GPIO.setup(PIN_CLOCK, GPIO.OUT)

wake_hour = 6
wake_min = 30

# write out a byte to the shift register
def shift_out(byte):  
  GPIO.output(PIN_LATCH, 0)
  for x in range(8):
    GPIO.output(PIN_DATA, (byte >> x) & 1)
    GPIO.output(PIN_CLOCK, 1)
    GPIO.output(PIN_CLOCK, 0)
  GPIO.output(PIN_LATCH, 1)

#turn "on" the digit at position pos 1-4
def select_digit(pos):
    if pos == 1:
        GPIO.output(PIN_D1, 0)
        GPIO.output(PIN_D2, 1)
        GPIO.output(PIN_D3, 1)
        GPIO.output(PIN_D4, 1)
    elif pos == 2:
        GPIO.output(PIN_D1, 1)
        GPIO.output(PIN_D2, 0)
        GPIO.output(PIN_D3, 1)
        GPIO.output(PIN_D4, 1)
    elif pos == 3:
        GPIO.output(PIN_D1, 1)
        GPIO.output(PIN_D2, 1)
        GPIO.output(PIN_D3, 0)
        GPIO.output(PIN_D4, 1)
    elif pos == 4:
        GPIO.output(PIN_D1, 1)
        GPIO.output(PIN_D2, 1)
        GPIO.output(PIN_D3, 1)
        GPIO.output(PIN_D4, 0)
    else: 
        return

#clear the LED digit at position pos 1-4
def clear_digit(pos):
    select_digit(pos)
    shift_out(0)

#write a hex digit 0-F to the given position 1-4
def write_digit(pos,n):
    if n < 0 or n > 15:
        return    
    write_byte(pos,digits[n])    
 
#write the given byte pattern to LED position pos 1-4
def write_byte(pos,byte):
    global config
    global blinkOn
    select_digit(pos)
    if (config and blinkOn):
        shift_out(0)
    else:
        shift_out(byte)
    time.sleep(delay)
    shift_out(0)

def show_time(t):
    hr = t.tm_hour    
    #if hr>12:
    #    hr = hr - 12        
    d1 = int(hr / 10)
    d2 = hr % 10        
    d3 = int(t.tm_min / 10)
    d4 = t.tm_min % 10    
    if d1==0:
        clear_digit(1)
    else:
        write_digit(1,d1)            
    write_byte(2, digits[d2] ^ DECIMAL)
    write_digit(3,d3)
    write_digit(4,d4)       

def show_time_mode(t):
    indicator(TIME)
    show_time(t.timetuple())

def show_wake_mode(t):
    indicator(WAKE)
    show_time(t.timetuple())

def show_sleep_mode(now,wake_time):
    indicator(SLEEP)
    
    secs = (wake_time - now).seconds
    hours = int(secs/3600)
    mins = int(secs%3600/60)
    #print('Estimated Sleep Time:{}:{}'.format(hours,mins))
    d1 = int(hours/10)
    d2 = hours%10
    d3 = int(mins/10)
    d4 = mins%10
    if d1 == 0:
        write_byte(1,0)
    else:
        write_digit(1,d1)
    write_byte(2,digits[d2]^DECIMAL)
    write_digit(3,d3)
    write_digit(4,d4)

def indicator(mode):
    if mode==SLEEP:
        GPIO.output(PIN_LED_TIME, 0)
        GPIO.output(PIN_LED_SLEEP, 1)
        GPIO.output(PIN_LED_WAKE, 0)   
    elif mode==WAKE:
        GPIO.output(PIN_LED_TIME, 0)
        GPIO.output(PIN_LED_SLEEP, 0)
        GPIO.output(PIN_LED_WAKE, 1)   
    elif mode==TIME:
        GPIO.output(PIN_LED_TIME, 1)
        GPIO.output(PIN_LED_SLEEP, 0)
        GPIO.output(PIN_LED_WAKE, 0)   

def alertLED(now,waketime):

    delta = waketime-now
    hours = int(delta.seconds/3600)
    mins =  int(delta.seconds%3600/60)    
    #print ('Estimated sleep duration {}-{}= {}:{}'.format(waketime,now,hours,mins))
    if hours >= 8:
        rgbAlert(0,1,0) #GREEN
    elif hours >= 6:
        rgbAlert(1,1,0) #YELLOW
    else:        
        msnow = millis()            
        try: 
            if msnow-alertLED.last > 500:
                alertLED.blinkOn = not alertLED.blinkOn
                alertLED.last = msnow
        except AttributeError:
            alertLED.last = msnow
            alertLED.blinkOn = True
        rgbAlert(int(alertLED.blinkOn),0,0) #RED

alertLED.blinkOn = True
alertLED.last = millis()

def rgbAlert(r,g,b):
    GPIO.output(PIN_RED, r)
    GPIO.output(PIN_GREEN, g)
    GPIO.output(PIN_BLUE, b)

def save_data():
    x= [wake_hour, wake_min]
    f = open("alarm_data.json", "w")
    json.dump(x,f)
    f.close()    

lastBlink = millis()
blinkOn = True
sleep_hours = 8
lastcycle=millis()
try:
    try:
        f = open("alarm_data.json", "r")
        data = json.load(f)
        f.close()
        wake_hour, wake_min = data

    except:
        wake_hour=8
        wake_min=0
    while True:
        msnow = millis()
        if (msnow-lastBlink>500):            
            blinkOn = not blinkOn
            lastBlink = msnow
        if is_time_to_cycle(msnow,lastcycle):
            cycle_mode(msnow)
        checkForLongPress()
        now = datetime.now()
        waketime = next_wake_time()  
          
        alertLED(now,waketime)        

        if currentMode == TIME:            
            show_time_mode(now)
        elif currentMode == SLEEP:
            show_sleep_mode(now,waketime)
        elif currentMode == WAKE:
            show_wake_mode(waketime)
            
except KeyboardInterrupt:
    #print('interrupted!')
    GPIO.cleanup()
    save_data()
    
sys.exit()    
  
    