import logging

class ThermoMonitor():

    def __init__(self,init_setpoint):
        logging.info('Monitor started')
        self.curr_setpoint = init_setpoint
        self.curr_temp = None
        self.sleeve = []

    def set_current_temp(self,temp_info):

        def Average(lst): 
            return sum(lst) / len(lst) 

        self.sleeve.append(temp_info)
        
        print(temp_info.adj_temp)
        if len(self.sleeve) == 5:

            self.sleeve = []
            

    def start_cooling():
        print("Cooling")

    def turn_off():
        #shut off as SOON as you hit the lower offset
        print('Turned Off')

    def column(self, matrix):
        return [measure.curr_temp for measure in matrix]