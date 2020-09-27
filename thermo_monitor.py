import time
import logging
from resources import settings
import RPi.GPIO as GPIO

def left(s, amount):
    return s[:amount]

def right(s, amount):
    return s[-amount:]

def mid(s, offset, amount):
    return s[offset:offset+amount]

class ThermoMonitor():
    cool_chan_list = []
    def __init__(self,init_setpoint):
        logging.info('MONITOR started')
        self.chan_list = [12,16,32,36]
        self.cool_chan_list = [12,16]
        self.heat_chan_list = [12,16,32]
        self.reason = ""
        self.state = "OFF"
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings = False
        GPIO.setup(self.chan_list,GPIO.OUT)
        GPIO.output(self.chan_list,GPIO.LOW)

        self.curr_setpoint = 70
        self.curr_temp = None
        self.TC_temp = None
        self.curr_hum = None
        self.sleeve = []
        self.turn_off()


    def change_set(self,new_set):
        self.curr_setpoint = new_set
    
    def get_set(self):
        return self.curr_setpoint

    def set_current_temp(self,temp_info,mode):

        def Average(lst): 
            return sum(lst) / len(lst) 

        self.sleeve.append(temp_info.curr_temp)
        
        #print(temp_info.adj_temp)
        if len(self.sleeve) == 2:
            avg_3 = Average(self.sleeve)
            self.curr_temp = avg_3
            self.curr_hum = temp_info.adj_hum/100
            self.sleeve = []
            if mode == 'cool':
                self.evaluate_temp_cool(avg_3,self.curr_hum)
            else:
                self.evaluate_temp_heat(avg_3,self.curr_hum)
            time.sleep(3)
            print(mode)
            #evaluate conditions


        return self.state

    def start_cooling(self, style):
        self.state = "COOLING-MAINT-" + style
        logging.info("MONITOR: " + self.state + ": " + self.reason + "( Temp - " + str(self.curr_temp) +"/"+ str(self.TC_temp) + ", Set - " + str(self.curr_setpoint) + ", Hum:" + str(self.curr_hum) + ")")
        GPIO.output(self.cool_chan_list,GPIO.HIGH)

    def start_heating(self, style):
        self.state = "HEATING-MAINT-" + style
        logging.info("MONITOR: " + self.state + ": " + self.reason + "( Temp - " + str(self.curr_temp) +"/"+ str(self.TC_temp) + ", Set - " + str(self.curr_setpoint) + ", Hum:" + str(self.curr_hum) + ")")
        GPIO.output(self.heat_chan_list,GPIO.HIGH)

    def turn_off(self):
        #default turn off, shut all down.
        self.state = "OFF"
        logging.info('MONITOR: Turning ' + self.state + ": " + self.reason + "( Temp - " + str(self.curr_temp) +"/"+ str(self.TC_temp) + ", Set - " + str(self.curr_setpoint) + ", Hum:" + str(self.curr_hum) + ")")
        GPIO.output(self.heat_chan_list,GPIO.LOW)

    def turn_off_cool(self):
        #shut off as SOON as you hit the lower offset
        self.state = "OFF"
        logging.info('MONITOR: Turning ' + self.state + ": " + self.reason + "( Temp - " + str(self.curr_temp) +"/"+ str(self.TC_temp) + ", Set - " + str(self.curr_setpoint) + ", Hum:" + str(self.curr_hum) + ")")
        GPIO.output(self.cool_chan_list,GPIO.LOW)

    def turn_off_heat(self):
        #shut off as SOON as you hit the lower offset
        self.state = "OFF"
        logging.info('MONITOR: Turning ' + self.state + ": " + self.reason + "( Temp - " + str(self.curr_temp) +"/"+ str(self.TC_temp) + ", Set - " + str(self.curr_setpoint) + ", Hum:" + str(self.curr_hum) + ")")
        GPIO.output(self.heat_chan_list,GPIO.LOW)

    def column(self, matrix):
        return [measure.curr_temp for measure in matrix]

    def evaluate_temp_cool(self,curr_temp,curr_hum):

        #margins
        low_margin = settings['setpoints'][self.curr_setpoint]["cool_low_margin"]
        high_margin = settings['setpoints'][self.curr_setpoint]['cool_high_margin']
        max_hum = settings['max_humidity']
        ideal_hum = settings['ideal_humidity']

        if self.state == "OFF":
            #it's too hot.
            if (curr_temp >= (self.curr_setpoint+high_margin)):

                self.reason = "Set point exceeded"
                self.start_cooling("TEMP")
            elif (curr_hum>=max_hum):

                self.reason = "Hum Max Exceeded"
                self.start_cooling("HUM")

        if left(self.state,7) == "COOLING":
            current_task = right(self.state,len(self.state)-8)

             
            if current_task == "MAINT-TEMP":
                #TC temp needs rounding
                if curr_temp<=(self.curr_setpoint-low_margin):
                    #maybe redundant for now
                    self.turn_off_cool()
                    self.reason = "Temp within cool margin."
                    #check humidity before you turn off
                    curr_task = "MAINT-HUM"

            #why are you cooling, has ideal humidity been reached?        
            if current_task == "MAINT-HUM":
                if curr_hum<=(ideal_hum):

                    self.reason = "Ideal humidity reached, temp OK."
                    self.turn_off_cool()
                else:
                    self.reason = "Temp ok, humidity not right."
                    self.state = "COOLING-MAINT-HUM"
                    self.start_cooling("HUM")

    def evaluate_temp_heat(self,curr_temp,curr_hum):

        #margins
        low_margin = settings['setpoints'][self.curr_setpoint]["cool_low_margin"]
        high_margin = settings['setpoints'][self.curr_setpoint]['cool_high_margin']
        max_hum = settings['max_humidity']
        ideal_hum = settings['ideal_humidity']

        if self.state == "OFF":
            #it's too cold.
            if (curr_temp <= (self.curr_setpoint+high_margin)):

                self.reason = "Set point exceeded"
                self.start_heating("TEMP")
            elif (curr_hum>=max_hum):

                self.reason = "Hum Max Exceeded"
                self.start_heating("HUM")

        if left(self.state,7) == "HEATING":
            current_task = right(self.state,len(self.state)-8)

             
            if current_task == "MAINT-TEMP":
                #TC temp needs rounding
                if curr_temp>=(self.curr_setpoint-low_margin):
                    #maybe redundant for now
                    self.turn_off_heat()
                    self.reason = "Temp within heat margin."
                    #check humidity before you turn off
                    curr_task = "MAINT-HUM"

            #why are you cooling, has ideal humidity been reached?        
            if current_task == "MAINT-HUM":
                if curr_hum<=(ideal_hum):

                    self.reason = "Ideal humidity reached, temp OK."
                    self.turn_off()
                else:
                    self.reason = "Temp ok, humidity not right."
                    self.state = "COOLING-MAINT-HUM"
                    self.start_cooling("HUM")

