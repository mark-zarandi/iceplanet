import pandas as pd
import matplotlib.pyplot as plt
from sklearn import linear_model
import numpy as np
import sys
df = pd.read_excel('ratio.xlsx',sheet_name='Sheet1')

#plt.scatter(excel_data['Temp'],excel_data['Adj_Temp'],color='red')
#plt.title('Stock Index Price Vs Interest Rate', fontsize=14)
#plt.xlabel('Interest Rate', fontsize=14)
#plt.ylabel('Stock Index Price', fontsize=14)
#plt.grid(True)
#plt.show()

x = df[['Temp','RH']]
y = df['Adj_Temp']

user_input = (sys.argv[1]).split(",")
print(user_input)
abs_temp = float(user_input[0])
humidity = float(user_input[1])
print(humidity)
regr = linear_model.LinearRegression()
regr.fit(x,y)
print(regr.predict([[abs_temp,humidity]]))



