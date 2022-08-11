import requests
from bs4 import BeautifulSoup
import time
import json
import pandas as pd
import csv
from datetime import datetime
from pytz import timezone
from tabulate import tabulate


#urls for scraping data:
url1='https://www.cmcmarketsstockbroking.com.au/'
url2="https://www.cmcmarketsstockbroking.com.au/ClientRequest/Endpoint?_app.id=CmcWeb&"


#function for displaying difference between lastPrice and Opening Price as units 
def amplify(x):
  x=round(x,4)
  return x*10**3

def steps(x,y):
  if x<0.1:
    result = (min(0.1,y)-x)/0.01
    if y>0.1:
      result += (y-max(0.1,x))/0.005
    return round(result,2)
  else:
    if y>0.1:
      result = (y-max(0.1,x))/0.005
      return round(result,2)
    return 0
  

#displaying percentage change between two columns
def percentage_change(col1,col2):
    return ((col2-col1)/col1)*100

with open('settings.json') as json_file:
  settings=json.load(json_file)

#formatting
pd.options.display.float_format = '{:.2f}'.format



login_payload = {
        'referer': 'https://www.cmcmarketsstockbroking.com.au/',
        'source': 'cmcpublic',
        'logonAccount': settings['username'],
        'logonPassword': settings['password']
    }

s=requests.Session()

#login
s.post(''.join(["https://www.cmcmarketsstockbroking.com.au/",
              "login.aspx?_app.id=CmcWeb"]), data=login_payload)


codes=settings['user_shares']
timing=settings['times']+settings['user_time']




dataCodes=[]


#main df for ind values
main_df=pd.DataFrame({
        'Stocks':codes,
})

#aux df for variation analysis


for code in codes:
  dataCodes.append('{"StockCode":"'+code+'"}')

payload={
      '_cmc.workload': ''.join(['{"Rs":[{"S":"QuoteBatchGet2","R":',
                            '{"Requests":[' + ','.join(dataCodes) + '],',
                                  '"IncludeCompanyInfo":true},"TId":12}]}'])
    }

# adding first column with predefined values to df

#creating df for stroing data:
data=pd.DataFrame({'User prices':settings['user_price']})

#df for storing ind variation and ind variability
data_aux=pd.DataFrame()

while True:
    #creating main_df
    main_df=pd.DataFrame({
        'Stocks':codes,
    })

    

    now=datetime.now().strftime("%H:%M:%S")
   
    
    values=[]
    
    if now in timing:
  
      #fetching data
      
      res_data=s.post(url2,data=payload)
      jsonData=json.loads(res_data.text)

      if jsonData==None:
        while jsonData:
            res_data=s.post(url2,data=payload)
            jsonData=json.loads(res_data.text)
            time.sleep(3)
            #fetching until it works

      
      for item in jsonData['Responses'][0]['Model']['Quotes']:
        values.append(item['IndicativePrice'])

      print(f"Last update:{now}")

      data[f"{str(now).replace(':','')}"] = values
      
      
      data_aux['Variability']=data.max(axis=1)-data.min(axis=1)
      data_aux['Variability']=data_aux['Variability'].apply(amplify)


      """
      >>> implementing var computation in units of 5
      """
      ind_5 = list(amplify(data.iloc[:,-1]-data.iloc[:,0]))
      ind_5 = [i//5 if i%5==0 else 0 for i in ind_5]

      
      data_aux['var (5)'] = ind_5

      """
      ind variation
      >>> output array for calculating new var (5)
      """
      output = []
      for i,j in zip(list(data.iloc[:,-1]),list(data.iloc[:,0])):
        output.append(steps(i,j))
      data_aux['Ind Variation']=output
      
    
      
      
      main_df=pd.concat([main_df,data,data_aux],axis=1)
      main_df=main_df.sort_values(by=['Ind Variation'],ascending=False)
      print(tabulate(main_df,headers='keys',tablefmt="pipe",showindex=False))
      
      #print(tabulate(main_df,headers="keys",tablefmt="pipe"))

        # removing current time in timing list just to scrape data once in that minute
      timing.remove(now)
      



  

      

