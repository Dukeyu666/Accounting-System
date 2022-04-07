from flask import Flask,request,make_response,redirect,render_template,url_for,flash,session,abort
from flask_login import LoginManager,UserMixin,login_user,current_user,login_required,logout_user
from handle_json import ActJSON
from set_counter import set_counter
from db_connect import DB_Object,DB_Querys
from assign_args import find_args,rebate_deposit
from werkzeug.utils import secure_filename
from datetime import datetime,timedelta
import os,shutil,Keys,calendar,csv,glob
import logging
#from logging.config import fileConfig
#from logging.handlers import TimedRotatingFileHandler

app=Flask(__name__)

logging.basicConfig(filename='Logging\\{:%Y-%m-%d}.log'.format(datetime.now()),level=logging.DEBUG,\
format=f'[%(asctime)s] [%(levelname)s] %(name)s : %(message)s')

app.config['UPLOAD_FOLDER']=r'.\upload_files'
app.config['SESSION_TYPE'] = 'filesystem'
#app.config['SECRET_KEY']=Keys.SECRET_KEY
app.secret_key=Keys.SECRET_KEY
#Session
Querys=DB_Querys()
DB_obj=DB_Object()
editJS=ActJSON()

ALLOWED_EXTENSIONS = {'csv'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/',methods=['GET'])
def home():
    app.logger.info(' Return home page ')
    return render_template('index.html')

#------------------------ login --------------------------
login_manager=LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "basic"
login_manager.login_view='login'
login_manager.login_message = ''
users = {'admin': {'password': 'support'}}

class User(UserMixin):  
    pass  
  
@login_manager.user_loader
def user_loader(account):
    if account not in users:
        return
    user = User()
    user.id = account
    return user

@login_manager.request_loader
def request_loader(request):
    account = request.form.get('account')
    if account not in users:
        return

    user = User()
    user.id = account

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['password'] == users[account]['password']

    return user 
  
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    account = request.form['account']
    if request.form['password'] == users[account]['password']:
        user = User()
        user.id = account
        login_user(user)
        next=request.args.get('next')
        app.logger.info('%s logged in successfully', account)
        return redirect(next or url_for('home'))
    app.logger.warning('%s logged in failed', account)
    flash(' 不正確的帳號或密碼 ')
    return redirect(url_for('login'))
  
#@app.route('/protected')
#@login_required
#def protected():
#    return 'Logged in as: ' + current_user.id
 
  
@app.route('/logout')
@login_required 
def logout():  
    logout_user()
    app.logger.info('logged out successfully')
    return redirect(url_for('home'))

#------------------------- 業績處理--------------------------------------
@app.route('/new_sales')
def new_sales():
    employees=editJS.load_json(editJS.employee_file)
    return render_template('new_sales.html',designers=employees['Designers'],\
            assistants=employees['Assistants'])

@app.route('/sales',methods=['POST'])
def post_sales():
    employees=editJS.load_json(editJS.employee_file)
    #------- 單號處理
    order=set_counter()  
    order_result=DB_obj.query_orderNo(order)
    if order_result != None :
        order=order_result
    #-------
    if request.method == "POST":
        #print(request.form)
        designer=find_args('designer')
        customer_phone=find_args('phone')
        payment=find_args('payment')
        total=request.form['total_all'] if request.form['product_total'] !='' else '0'
        product_total=request.form['product_total'] if request.form['product_total'] !='' else '0'
        seller=request.form['seller']

        if payment == 'deposit':
            result=DB_obj.query_client(customer_phone)
            deposit=int(result[3])-(int(total)+int(product_total))
            
            if deposit >= 0 :
                # 1.寫入業績 2.扣掉儲值金
                result=DB_obj.sales_insert(str(order),designer,total,product_total,seller,payment,customer_phone)
                DB_obj.update_deposit(customer_phone,str(deposit))
                flash('新增完成。')
            else:
                flash('  餘額不足，請先儲值或選用其他付款方式  ')
                return redirect(url_for('new_sales')) 
        
        else:
            result=DB_obj.sales_insert(str(order),designer,total,product_total,seller,payment,customer_phone)

        for name in employees['Assistants']:
            if name in request.form :
                if request.form[name] != '':
                    point=request.form[name]
                    #print(order,name,request.form[name]) 
                    DB_obj.points_insert(str(order),name,point)
        if result != None:
            flash(result)
            return redirect(url_for('new_sales'))

    return redirect(url_for('new_sales'))

@app.route("/modify_sales",methods=['GET','POST'])
@login_required
def modify_sales():
    employee=editJS.load_json(editJS.employee_file)   
    maxday=datetime.today().strftime("%Y-%m-%d")
    minday=(datetime.today()+timedelta(-1)).strftime("%Y-%m-%d")
    if request.method == "GET":
        return render_template('modify_sales.html',maxday=maxday,minday=minday,\
                                designers=employee['Designers'],assistants=employee['Assistants'])
    else:
        #print(request.form)
        if 'query_submit' in request.form:
            #print(request.form)
            date=request.form['date']
            designer=request.form['designer']
            results=Querys.personal_sales(designer, date)
            #print(results)
            if [[]] == results:
                flash(" 無今日 "+designer+" 的業績" )
                return redirect(url_for('modify_sales'))
            elif 'ODBC' in results:
                flash(results)
                app.logger.error(' DATABASE connection fail ')
                return redirect(url_for('modify_sales'))
            else:
                return render_template('modify_sales.html',results=results,\
                                    maxday=maxday,minday=minday,\
                                designers=employee['Designers'],assistants=employee['Assistants'],date=date,designer=designer)
        if 'form_submit' in request.form:
            #print(request.form)
            orderNo=request.form['orderNo']
            sales=request.form['sales']
            seller=request.form['seller']
            pd_sales=request.form['pd_sales']
            payment=request.form['payment']
            phone=request.form['phone']
            date=request.form['date']
            designer=request.form['designer']
            
            result=DB_obj.query_client(phone)
            if result == None:
                flash(' 修改失敗，請檢查電話號碼是否正確。 ')
                return redirect(url_for('modify_sales'))
            elif 'ODBC' in result:
                flash(result)
                app.logger.error(' DATABASE connection fail ')
                return redirect(url_for('modify_sales'))
            else:
                if phone != 'None' and payment == 'deposit':
                    deposit=int(result[3])-(int(sales)+int(pd_sales))
                    if deposit >= 0 :
                        DB_obj.update_sales(orderNo,sales,seller,pd_sales,payment,phone,date,designer)
                        flash(' 修改完成，請再次確認 ')
                        return redirect(url_for('modify_sales'))
                    else:
                        flash('  餘額不足，無法修改。  ')
                        return redirect(url_for('modify_sales'))
                else:
                    DB_obj.update_sales(orderNo,sales,seller,pd_sales,payment,phone,date,designer)
                    flash(' 修改完成，請再次確認 ')
                    return redirect(url_for('modify_sales'))

        return redirect(url_for('modify_sales'))

#------------------------- 輸出業績 ------------------------------------
@app.route("/show_salesforday",methods=['GET','POST'])
#@login_required
def show_salesforday():
    employees=editJS.load_json(editJS.employee_file)
    if request.method == 'POST':
        
        date=request.form['date']
        #if session['_user_id'] == 'admin':
        results=Querys.query_sales(employees['Designers'],date)
        #else :
            #designer=[]
            #designer.append(session['_user_id'])
            #results=Querys.query_sales(designer,date)

        product_result=Querys.query_product_total(date)
        payment_result=Querys.query_payment(date)
        dataset=[]
        for result in results:
            if [] != result and 'ODBC' not in results:
                dataset.append(result)
        if [] == dataset and [] == product_result and [] == payment_result :
            flash(" 無今日業績 " )
            return redirect(url_for('show_salesforday'))
        elif 'ODBC' in results:
            flash(results)
            app.logger.error(' DATABASE connection fail ')
            return redirect(url_for('show_salesforday'))
        else:
            total=[]
            for data in dataset:
                sales=0
                for col in data:
                    sales=sales+col[2]
                total.append(int(sales))
            return render_template("show_salesforday.html",results=\
                                    dataset,date="日期 : "+\
                                    date,total=total,product_result=product_result,\
                                    payment_result=payment_result)
    return render_template("show_salesforday.html")

@app.route("/show_ForMonth",methods=['GET','POST'])
@login_required
def show_ForMonth():
    if request.method == 'POST':
        print(request.form)
        date=request.form['date']
        year=int(date.split('-')[0])
        month=int(date.split('-')[1])
        firstday=date+"-01"
        lastday=date+"-"+str(calendar.monthrange(year,month)[1])
        print(firstday,lastday)
        results=Querys.query_Month(firstday,lastday)
        result=results[0]
        product_result=results[1]
        payment_result=results[2]
        if [] == result and [] == product_result and [] == payment_result :
            flash(" 無 "+date+" 的業績 " )
            return redirect(url_for('show_ForMonth'))
        elif 'ODBC' in results:
            flash(results)
            app.logger.error(' DATABASE connection fail ')
            return redirect(url_for('show_ForMonth'))
        else:
            return render_template("show_ForMonth.html",date="日期 : "+date+"月",result=result,\
                            product_result=product_result,payment_result=payment_result)
    
    return render_template("show_ForMonth.html")
#----------------------- 員工資料處理-----------------------------------

@app.route('/staff_index')
def staff_index():
    return render_template('staff_index.html')

@app.route('/point_assistants',methods=['GET','POST'])
@login_required
def point_assistants():
    employees=editJS.load_json(editJS.employee_file)
    if request.method == 'POST':
        if 'query' in request.form:
            assistant=request.form['Assistant']
            date1=request.form['date1']
            date2=request.form['date2']
            result=DB_obj.query_point(assistant,date1,date2)
            session['assistant']=assistant
            print(result)
            if None in result:
                flash(' 查無 '+assistant+" 在 "+date1+" 至 "+date2+" 的資料 " )
                return redirect(url_for('point_assistants'))
            elif 'ODBC' in result:
                flash(result)
                app.logger.error(' DATABASE connection fail ')
                return redirect(url_for('point_assistants'))
            else:
                all_result=result[1]
                sum_assist="總計 : [ "+result[0][0]+" ] "+str(result[0][1])+" 點"

                return render_template('point_assistants.html',all_result=all_result,sum_assist=sum_assist,\
                                    assistants=employees['Assistants'],date1=date1,date2=date2)
        if 'form_submit' in request.form:
            assistant=session['assistant']
            date=request.form['orderNo'].split('#')[0]
            orderNo=request.form['orderNo'].split('#')[1]
            point=request.form['point']
            DB_obj.update_points(point,date,orderNo,assistant)
            #print(orderNo,point,date,session)
            flash(' 點數修改完成 ')
            return redirect(url_for('point_assistants'))           
    return render_template('point_assistants.html',assistants=employees['Assistants'])

@app.route('/edit')
def modify(designers=None,assistants=None):
    employees=editJS.load_json(editJS.employee_file)
    return render_template('edit.html', designers=employees['Designers'],assistants=employees['Assistants'])

@app.route('/employees',methods=['GET','POST'])
def post_employees():
    def post_json():
        if request.method == "POST":
            #print(request.form)
            form_post=request.form
            data=editJS.load_json(editJS.employee_file)
            if form_post['option'] == 'remove' :
                if form_post['employees'] in data['Designers'] :
                    employee=form_post['employees']
                    editJS.modify_employee(edit='remove',designer=employee)
                elif form_post['employees'] in data['Assistants'] :
                    employee=form_post['employees']
                    editJS.modify_employee(edit='remove',assistant=employee)
            elif form_post['option'] == 'add' :
                if form_post['add'] == "Designers" :
                    employee=form_post['Designers']
                    editJS.modify_employee(edit='add',designer=employee)
                else :
                    employee=form_post['Assistants']
                    editJS.modify_employee(edit='add',assistant=employee)
    post_json()
    return redirect(url_for('home'))

#------------- customer management section -----------------------
#************* 匯入檔名 待修改

@app.route('/clients_data')
def client_data():
    return render_template('clients_data.html')

@app.route("/query_client",methods=['GET','POST'])
def query_client():
    phone=''
    name=''
    birthday=''
    balance=''
    if request.method == "POST":
        args_phone=request.form['phone']
        result=DB_obj.query_client(args_phone)
        if result == None:
            name='查無此人'
            return render_template('query_client.html',name=name)
        elif 'ODBC' in result:
            flash(result)
            app.logger.error(' DATABASE connection fail ')
            return render_template('query_client.html')
        else:
            name=result[0]
            birthday=result[1] if result[1] != None else ''
            phone=result[2]
            balance="{:,}".format(int(result[3]) if result[3] != None else 0 )
            return render_template('query_client.html',name=name,birthday=birthday,phone=phone,balance=balance)
    return render_template('query_client.html',name=name,birthday=birthday,phone=phone,balance=balance)   

@app.route("/import_client",methods=['GET'])
def import_client():
    return render_template('import_client.html')

@app.route("/process_add_customer",methods=['POST'])
def process_add_customer():
    if request.method == 'POST':
        #print(request.form)
        name=request.form['name']
        phone=request.form['phone']
        date=request.form['date']
        result=DB_obj.query_client(phone)
        if result == None:
            DB_obj.insert_customer(name,phone,date)
            flash('  新增成功  ')
            return redirect(url_for('import_client'))
        elif 'ODBC' in result :
            flash(result)
            app.logger.error(' DATABASE connection fail ')
            return redirect(url_for('import_client'))
        else:
            flash('  無法新增已存在的號碼  ')
            return redirect(url_for('import_client'))        

@app.route('/process_upload_file',methods=['POST'])
def process_upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(url_for('import_client'))
        upload_file = request.files['file']

        if upload_file and allowed_file(upload_file.filename):
            filename=secure_filename(upload_file.filename)
            if '.csv' not in filename:
                flash(' 檔名不可為中文 ')
                app.logger.error(' File name allows english only. Import failed ')
                return redirect(url_for('import_client')) 
            upload_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            #-----------CSV handling---------------
            CsvFile=glob.glob(r'.\upload_files\*.csv')[0]    
            with open(CsvFile,'r',newline='') as f:
                data=csv.reader(f)
                for d in data: 
                    name=d[0]
                    phone=d[1]
                    birthday=d[2] if d[2] !='' else 'Null'
                    result=DB_obj.query_client(phone)
                    if result == None:
                        DB_obj.insert_customer(name,phone,birthday)
                    elif 'ODBC' in result :
                        flash(result)
                        app.logger.error(' DATABASE connection failed ')
                        return redirect(url_for('import_client'))
                    else:
                        flash(phone+" 此號碼已存在。")
                        return redirect(url_for('import_client'))
            shutil.copy(CsvFile,'.\\backup_csv',)
            os.remove(CsvFile)
            flash(' 匯入成功 ')
            return redirect(url_for('import_client'))    
    
    
    return redirect(url_for('import_client'))

@app.route('/deposit',methods=['GET','POST'])
def deposit():
    phone=''
    name=''
    balance=''
    if request.method == "POST":
        args_phone=request.form['phone']
        result=DB_obj.query_client(args_phone)
        if result == None:
            flash(' 無此顧客資料。 ')
            return redirect(url_for('deposit'))
        elif 'ODBC' in result:
            flash(result)
            app.logger.error(' DATABASE connection failed ')
            return redirect(url_for('deposit'))
        else:
            name=result[0]
            phone=result[2]
            balance="{:,}".format(int(result[3]) if result[3] != None else 0 )
            return render_template('deposit.html',name=name,phone=phone,balance=balance)
   
    return render_template('deposit.html')

@app.route('/process_deposit',methods=['POST'])
def process_deposit():
    if request.method == "POST":
        #print(request.form)
        phone=request.form['phone']
        deposit=request.form['money']
        rebate=str(rebate_deposit(int(deposit)))
        DB_obj.add_deposit(phone,deposit,rebate)
        flash('  加值完成 !  ')
        return redirect(url_for('deposit'))

@app.route("/topup_record",methods=['GET','POST'])
#@login_required
def topup_record():
    date=datetime.today().strftime("%Y-%m-%d")
    results=Querys.query_topup_forday(date)
    if results == [] :
        #balance=Querys.query_balance()
        #return render_template('topup_record.html',balance=balance)
        flash(' 無今日儲值紀錄。 ')
        return redirect(url_for('home'))
    elif 'ODBC' in results :
        flash(results)
        app.logger.error(' DATABASE connection failed ')
        return redirect(url_for('home'))
    else:
        #balance=Querys.query_balance()
        sum=0
        for result in results:
            sum=sum+result[1]
        return render_template("topup_record.html",results=results,sum=sum)

#------------送出修改資料需求-------------
@app.route('/modify_request',methods=['POST'])
def modify_client():
    print(request.form)
    if request.method == 'POST':
        name=find_args('name')
        old_phone=find_args('phone_old')
        phone=find_args('phone')
        birthday=find_args('birthday')
        balance=find_args('balance')
        #print(name,old_phone,phone,birthday,balance)
        DB_obj.update_customer(name,old_phone,phone,birthday,balance)
        flash('  修改完成  ')
        return redirect(url_for('query_client'))

@app.route('/setting')
def setting():
    return render_template('setting.html')

@app.route('/reset')
def reset():
    error=DB_obj.reset_all()
    if error == None or error == '':
        flash(' 所有資料已重置 ')
        app.logger.warning(' Data was reset all.')
    else:
        flash(' 無法連接資料庫。')
        app.logger.error(' DB can not connect. ')
    return redirect(url_for('setting'))


@app.errorhandler(404)
def error_404page(e):
    app.logger.error(' Page not found  - HTTP 404  ')
    return render_template('404.html'), 404
@app.errorhandler(500)
def error_500page(e):
    app.logger.error(' Internal server error  - HTTP 500  ')
    return render_template('500.html'), 500

app.run(host='localhost')


