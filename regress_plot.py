import pandas as pd
import matplotlib.pyplot as plt
from sklearn import linear_model
import numpy as np
from numpy import array
import sys
from sklearn.preprocessing import PolynomialFeatures
df = pd.read_excel('observations.xlsx',sheet_name='Sheet1')



x = df[['abs_hum']]
y = df['variance']

regr = linear_model.LinearRegression()
regr.fit(x,y)
print(regr.predict([[52.42]]))
print('Intercept: \n', regr.intercept_)
print('Coefficients: \n', regr.coef_)
plt.scatter(df['abs_hum'],df[['variance']],color='red')
plt.plot(x, regr.predict(x), color='blue')
plt.title('Stock Index Price Vs Interest Rate', fontsize=14)
plt.xlabel('Interest Rate', fontsize=14)
plt.ylabel('Stock Index Price', fontsize=14)
plt.grid(True)
plt.show()

#predict is an independent variable for which we'd like to predict the value



