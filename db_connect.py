class DB_Object:
    
    def __init__(self):
        from configparser import ConfigParser
        config=ConfigParser()
        config.read('config.ini')
        self.server=config.get('DATABASE','server')
        self.database=config.get('DATABASE','database')
        self.username=config.get('DATABASE','username')
        self.password=config.get('DATABASE','password')
    def db_connection(self): 
        import pyodbc 
        cnxn = pyodbc.connect(\
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+self.server+';DATABASE=' +self.database+\
        ';UID='+self.username+';PWD='+ self.password)
        return cnxn

    def update_sales(self,orderNo,sales,seller,pd_total,payment,phone,date,designer):
        string="exec update_sales "+orderNo+","+sales+",'"+seller+"',"+\
                pd_total+",'"+payment+"','"+phone+"','"+\
                date+"','"+designer+"';"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            connection.cursor().execute(string)
            connection.commit()
            connection.close()
        except Exception as e:       
            return e.args[1]    


    def query_client(self,phone):
        string='''select name,birthday,balance.phone,deposit 
               from customer inner join balance 
               on customer.phone=balance.phone '''+"where balance.phone='"+phone+"'" 
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            result=connection.cursor().execute(string).fetchone()
            connection.close()
        except Exception as e:
            return e.args[1]
        return result
    def insert_customer(self,name,phone,date):
        string="exec add_customer"+"'"+name+"'"+","+"'"+phone+"'"+","+"'"+date+"'"+";"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            connection.cursor().execute(string)
            connection.commit()
            connection.close()
        except Exception as e:       
            return e.args[1]
    def add_deposit(self,phone,money,rebate):
        string="exec add_deposit "+"'"+phone+"',"+"'"+money+"',"+rebate+";"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            connection.cursor().execute(string)
            connection.commit()
            connection.close()
        except Exception as e:       
            return e.args[1]
    
    def sales_insert(self,order,designer,total,product_total,seller,payment,phone):
        string="exec insert_sales "+"'"+order+"'"+","+"'"+designer+"'"+","+"'"+total+"'"+","+\
                                    "'"+product_total+"'"+","+"'"+seller+"'"+","+\
                                    "'"+payment+"'"+","+"'"+phone+"';"+\
                "exec insert_goods"+\
                "'"+order+"','"+seller+"','"+product_total+"';"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            connection.cursor().execute(string)
            connection.commit()
            connection.close()
        except Exception as e:       
            return e.args[1]
    def points_insert(self,order,assistant,point):
        string="exec insert_points "+"'"+order+"'"+","+"'"+assistant+"'"+","+"'"+point+"';"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            connection.cursor().execute(string)
            connection.commit()
            connection.close()
        except Exception as e:       
            return e.args[1]
    def update_customer(self,name,old_phone,phone,birthday,money):
        string="exec modify_customer @name='"+name+"',"+\
                                    "@old_phone='"+old_phone+"',"+\
                                    "@phone='"+phone+"',"+\
                                    "@birthday='"+birthday+"',"+\
                                    "@deposit='"+money+"';"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            connection.cursor().execute(string)
            connection.commit()
            connection.close()
        except Exception as e:       
            return e.args[1]
    def update_deposit(self,phone,deposit):
        string="exec deposit_update '"+phone+"','"+deposit+"';"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            connection.cursor().execute(string)
            connection.commit()
            connection.close()
        except Exception as e:       
            return e.args[1]
    def query_point(self,assistant,date1,date2):
        string="select assistant,sum(point) from points where InsertTime between "+\
                "'"+date1 +"' and " +\
                "'"+date2 +"' and assistant='"+\
                assistant +"' group by assistant;"
        string2="select orderNo,point,InsertTime from points where InsertTime between "+\
                "'"+date1 +"' and " +\
                "'"+date2 +"' and assistant='"+\
                assistant +"' order by orderNo;"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            result=connection.cursor().execute(string).fetchone()
            result2=connection.cursor().execute(string2).fetchall()
            connection.close()
        except Exception as e:
            return e.args[1]
        return [result,result2]

    def query_orderNo(self,order):
        string="select*from sales where orderNo='"+order+"' and InsertTime=CONVERT(date,GETDATE(),110);"
        string2="select max(orderNo)as orderNo from sales where InsertTime=CONVERT(date,GETDATE(),110);"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            result=connection.cursor().execute(string).fetchone()
            connection.close()
        except Exception as e:       
            return e.args[1]
        if result != None :
            connection=self.db_connection()
            result=connection.cursor().execute(string2).fetchone()
            #result=result[0].split('#')[0]+'#'+str(int(result[0].split('#')[1])+1)
            result=int(result[0])+1
            connection.close()    
        return result
    def update_points(self,point,date,orderNo,assistant):
        string="update points set point="+point+" where "+\
                "InsertTime='"+date+"' and orderNo="+orderNo+" and assistant='"+assistant+"';"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            connection.cursor().execute(string)
            connection.commit()
            connection.close()
        except Exception as e:       
            return e.args[1]
    def reset_all(self):
        string="exec reset_all;"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            connection.cursor().execute(string)
            connection.commit()
            connection.close()
        except Exception as e:       
            return e.args[1]        

class DB_Querys:
    
    def __init__(self):
        from configparser import ConfigParser
        config=ConfigParser()
        config.read('config.ini')
        self.server=config.get('DATABASE','server')
        self.database=config.get('DATABASE','database')
        self.username=config.get('DATABASE','username')
        self.password=config.get('DATABASE','password')
    def db_connection(self): 
        import pyodbc 
        cnxn = pyodbc.connect(\
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+self.server+';DATABASE=' +self.database+\
        ';UID='+self.username+';PWD='+ self.password)
        return cnxn

    def personal_sales(self,designer,date):
        dataset=[]
        string="select orderNo,total,seller,product_total,payment,customer_phone"+\
                " from sales where designer="+\
                 "'"+designer+"' and InsertTime='"+\
                date+"';"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            result=connection.cursor().execute(string).fetchall()
            connection.close()
            dataset.append(result)
        except Exception as e:
            return e.args[1]
        return dataset

    def query_sales(self,designers,date):
        dataset=[]
        for name in designers:
            string="select orderNo,designer,total from sales where designer="+\
                    "'"+name+"' and InsertTime='"+\
                        date+"';"
            try:
                connection=self.db_connection()
            except Exception as e:
                return e.args[1]
            try:
                result=connection.cursor().execute(string).fetchall()
                connection.close()
                dataset.append(result)
            except Exception as e:
                return e.args[1]
        return dataset

    def query_Month(self,firstday,lastday):
        dataset=[]
        #----------------月業績--------------
        string="select designer,sum(total) as total from sales where InsertTime between '"+\
                firstday+"' and '"+lastday+"' group by designer order by total desc;"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            result=connection.cursor().execute(string).fetchall()
            connection.close()
            dataset.append(result)
        except Exception as e:
            return e.args[1]
        #---------------月店販-----------------
        string="select seller,sum(product_total)as pd_total from sales "+\
                "where seller is not null and InsertTime between '"+\
                firstday+"' and '"+lastday+"' group by seller order by pd_total desc;"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            result=connection.cursor().execute(string).fetchall()
            connection.close()
            dataset.append(result)
        except Exception as e:
            return e.args[1]
        #---------------月結帳-----------------
        string="select sum(total+product_total)as total,payment from sales "+\
                "where InsertTime between '"+\
                firstday+"' and '"+lastday+"' group by payment order by total desc;"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            result=connection.cursor().execute(string).fetchall()
            connection.close()
            dataset.append(result)
        except Exception as e:
            return e.args[1]
        return dataset


    def query_product_total(self,date):
        string="select seller,sum(product_total)as total "+\
                "from sales where seller is not null and InsertTime='"+\
                date+"'"+" group by seller order by total desc"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            result=connection.cursor().execute(string).fetchall()
            connection.close()
        except Exception as e:
            return e.args[1]
        return result
    
    def query_payment(self,date):
        string="select sum(total+product_total) as total,payment "+\
                "from sales where InsertTime='"+date+"'group by payment order by total desc;"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            result=connection.cursor().execute(string).fetchall()
            connection.close()
        except Exception as e:
            return e.args[1]
        return result
    def query_topup_forday(self,date):
        string="select *from topup_record where InsertTime ='"+date+"';"
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            result=connection.cursor().execute(string).fetchall()
            connection.close()
        except Exception as e:
            return e.args[1]
        return result
    def query_balance(self):
        string="select sum(deposit) from balance "
        try:
            connection=self.db_connection()
        except Exception as e:
            return e.args[1]
        try:
            result=connection.cursor().execute(string).fetchone()
            connection.close()
        except Exception as e:
            return e.args[1]
        return result[0]
            
"""
    def db_cursor(self):
        import pyodbc  
        self.cnxn = pyodbc.connect(\
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+self.server+';DATABASE=' +self.database+\
        ';UID='+self.username+';PWD='+ self.password)
        self.cursor = cnxn.cursor()
        cnxn
        return self.cursor

def DB_query(phone):
   import pyodbc 

   server = 'DUKE'+'\\'+'SQLEXPRESS' 
   database = 'BELLEVIE' 
   username = 'sa' 
   password = 'test' 

   cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
   cursor = cnxn.cursor()  

   string='''select name,birthday,balance.phone,deposit 
               from customer inner join balance 
               on customer.phone=balance.phone '''+"where balance.phone='"+phone+"'" 
   
   result=cursor.execute(string).fetchone()
   
   return result
"""