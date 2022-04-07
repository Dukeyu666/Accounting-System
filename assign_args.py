from flask import request
from handle_json import ActJSON

def find_assistants():
    editJS=ActJSON()
    employees=editJS.load_json(editJS.employee_file)
    for name in employees['Assistants'] :   
        find_args(name)

def find_args(arg):
    
    for i in request.form:
        if arg in i:
            if request.form[arg] == '':
                return 'null'
            else:
                return request.form[arg]
    else:
        return 'null'

def rebate_deposit(money):
    from configparser import ConfigParser
    config=ConfigParser()
    config.read('config.ini')
    condition=config.get('DepositArgs','condition')
    rebate=config.get('DepositArgs','rebate')
    count=0
    total=money
    while True:
        total=total-int(condition)
        if total >= 0 :
            count+=1
        else:
            break
    money= money + (int(rebate) * count)
    return money