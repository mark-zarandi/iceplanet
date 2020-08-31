settings = {
	 
'setpoints':{
73:{"temp_offset":-.2,
        "hum_offset":4,
        "cool_low_margin":1.2,
#between 1 and 1.4
        "cool_high_margin":2},
72:{
        "temp_offset":-.2,
        "hum_offset":4,
        "cool_low_margin":1.2,
#between 1 and 1.4
        "cool_high_margin":1},
        70:{
	"temp_offset":-.5,
	"hum_offset":4,
	"cool_low_margin":1.2,
#between 1 and 1.4 
	"cool_high_margin":.7},
68:{
        "temp_offset":-.2,
        "hum_offset":4,
        "cool_low_margin":1.5,
#between 1 and 1.4
        "cool_high_margin":.5}},

#careful, i think margin scales.
#"margins":{68:{},70:{}}
#between 1.5 and 1.8, some times 2 degree at setpoint over 70
"max_humidity":.70,
"ideal_humidity":.6

}
