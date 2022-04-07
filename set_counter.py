from datetime import datetime,timedelta
Today=datetime.today().strftime("%Y%m%d")
counter=0
def set_counter():
    global counter
    global Today
    if Today == datetime.today().strftime("%Y%m%d"):
        counter+=1
        #return (Today+"#"+str(counter) )
        return (str(counter))
    else:
        counter=0
        counter+=1
        Today=datetime.today().strftime("%Y%m%d")
        #return (Today+"#"+str(counter) )
        return (str(counter))