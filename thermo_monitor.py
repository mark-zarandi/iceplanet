import logging
from resources import settings

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
        self.turn_off()
        self.curr_setpoint = init_setpoint
        self.curr_temp = None
        self.curr_hum = None
        self.sleeve = []
        self.state = "OFF"
        self.reason = ""

    def set_current_temp(self,temp_info):

        def Average(lst): 
            return sum(lst) / len(lst) 

        self.sleeve.append(temp_info.TC_temp)
        
        #print(temp_info.adj_temp)
        if len(self.sleeve) == 3:
            avg_3 = Average(self.sleeve)
            self.curr_temp = avg_3
            self.curr_hum = temp_info.adj_hum/100
            self.sleeve = []
            self.evaluate_temp(avg_3,self.curr_hum)

            #evaluate conditions


        return self.state

    def start_cooling(self):
        logging.info("MONITOR: " + self.state + ": " + self.reason + "( Temp - " + str(self.curr_temp) + ", Set - " + str(self.curr_setpoint) + ", Hum:" + str(self.curr_hum) + ")")

    def turn_off(self):
        #shut off as SOON as you hit the lower offset
        logging.info('MONITOR: Turning Off')

    def column(self, matrix):
        return [measure.curr_temp for measure in matrix]

    def evaluate_temp(self,curr_temp,curr_hum):

        #margins
        low_margin = settings["cool_low_margin"]
        high_margin = settings['cool_high_margin']
        max_hum = settings['max_humidity']
        ideal_hum = settings['ideal_humidity']

        if self.state == "OFF":
            #it's too hot.
            if (curr_temp >= (self.curr_setpoint+high_margin)):
                self.state = "COOLING-MAINT-TEMP"
                self.reason = "Set point exceeded"
                self.start_cooling()
            else:
            #it's too humid
                if (curr_hum>=max_hum):
                    self.state = "COOLING-MAINT-HUM"
                    self.reason = "Hum Max Exceeded"
                    self.start_cooling()

        if left(self.state,7) == "COOLING":
            current_task = right(self.state,len(current_task)-8)

                #why are you cooling, has cooling margin been exceeded that you can stop?
            if current_task == "MAINT_TEMP":
                if curr_temp<=(self.curr_setpoint-low_margin):
                    self.state = "OFF"
                    self.reason = "Temp within cool margin."
                    #check humidity before you turn off
                    curr_task = "MAINT_HUM"

            #why are you cooling, has ideal humidity been reached?        
            if current_task == "MAINT_HUM":
                if curr_hum<=(ideal_hum):
                    self.state = "OFF"
                    self.reason = "Ideal humidity reached, temp OK."
                    self.turn_off()
                else:
                    self.reason = "Temp ok, humidity not right."
                    self.state = "COOLING-MAINT-HUM"
                    self.start_cooling()

