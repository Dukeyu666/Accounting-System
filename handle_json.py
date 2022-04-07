class ActJSON():
    """This is for JSON modification in use"""
    def __init__(self,employee_file=None,product_file=None):
        import os
        self.employee_file=os.getcwd()+r'\static\json\employees.json'
        self.services_file=os.getcwd()+r'\static\json\services.json'

    def load_json(self,source):
        import json
        with open(source,mode='r',encoding='utf-8') as file:
            data=json.load(file)
        return data

    def modify_employee(self,*,edit: 'str[add:remove]',designer=None,assistant=None):
        import json
        data=self.load_json(source=self.employee_file)
        if edit == 'remove':
            if designer != None :
                data['Designers'].remove(designer)
            if assistant != None:
                data['Assistants'].remove(assistant)
        if edit == 'add' :
            if designer != None :
                data['Designers'].append(designer)
            if assistant != None:
                data['Assistants'].append(assistant)
        with open(self.employee_file,mode='w',encoding='utf-8') as file:
            json.dump(data,file)
    def modify_product(self,*,edit: 'str[add:remove]',designer=None,assistant=None):
        import json
        #data=self.load_json(source=self.product_file)



"""    大於五位使用的

def modify_json(*,edit: 'str[add:remove]',designer=None,assistant=None):
    data=load_json()
    if len(data['Assistants']) > 5:
        if edit == 'remove':
            if designer != None :
                data['Designers'].remove(designer)
            if assistant != None:
                data['Assistants'].remove(assistant)
        if edit == 'add' :
            if designer != None :
                data['Designers'].append(designer)
    else:
        if edit == 'remove':
            if designer != None :
                data['Designers'].remove(designer)
            if assistant != None:
                data['Assistants'].remove(assistant)
        if edit == 'add' :
            if designer != None :
                data['Designers'].append(designer)
            if assistant != None:
                data['Assistants'].append(assistant)
    with open(json_file,mode='w',encoding='utf-8') as file:
        json.dump(data,file)
"""