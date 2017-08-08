#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 1 nov. 2016

@author: Rafa Leon
'''

from openpyxl import load_workbook
from datetime import datetime, timedelta, date
import os
import math
from clickatell.rest import Rest
from subprocess import call
from SendSMS import *
import SendSMS
import urllib
import urllib.request


CONCEPT_COLUMN = 'A'
PHONE_COLUMN = 'B'
CLAIM_DATE_COLUMN = 'C'
ACCIDENT_DATE_COLUMN = 'D'
PAY_DATE_COLUMN = 'E'
COMPANY_AMOUNT_COLUMN = 'J'
FINISHED_COLUMN = 'N'

DAYS_PER_MONTH = 30
CLAIM_DATE_ALARM = 3*DAYS_PER_MONTH # 3 months
ACCIDENT_DATE_ALARM = 1*DAYS_PER_MONTH # 1 months

DEBUG_MAIL_RECEIPT = 'rafaleon157@gmail.com'
DEBUG_MAIL_SUBJECT_OK = "Tatiana CustomerControl OK"
DEBUG_MAIL_BODY_OK = "Todo OK"

DEBUG_MAIL_SUBJECT_NOK = "Tatiana CustomerControl FALLÓ!!!!"
DEBUG_MAIL_BODY_NOK = "FALLÓ!!!!"

###################

MAIL_RECEIPT = 'tatiraverg@gmail.com'
MAIL_SUBJECT_CLAIM_ALARM = "Alerta de Reclamacion: {}"
MAIL_BODY_CLAIM_ALARM = "Han pasado {} meses desde la fecha de reclamacion para: \n" \
                        "Fila: {}\n" \
                        "Concepto: {}\n" \
                        "Fecha de reclamacion: {}"
MAIL_SUBJECT_ACCIDENT_ALARM = "Alerta de Prescripcion de Siniestro: {}"
MAIL_BODY_ACCIDENT_ALARM = "Faltan {} meses para la fecha de prescripcion del siniestro para: \n" \
                           "Fila: {}\n" \
                           "Concepto: {}\n" \
                           "Fecha de prescripcion de siniestro: {}"
                    
SMS_BODY = "Temboury Abogados\n" \
           "Tiene pendiente pasar por nuestras oficinas para efectuar el pago de {}€"

MENSATEK_USERNAME = "rafaleon15@hotmail.com"
MENSATEK_PASSWORD = "###XXX"
error_count = 0

#Sends a mail with the passed information
def sendNormalMail(receipt, subject, body, os_name):
    mail = 'echo "' + body + '" | mail -a "Content-Type: text/plain; charset=UTF-8" -s "' + \
            subject + '" ' + receipt
    if (os_name != "nt"):
        os.system(mail)

#Sends a mail with the passed information
def sendMail(subject, body, row, concept, date, passed_months, os_name):
    mail = 'echo "' + body.format(passed_months, row, concept, date) + '" | mail -a "Content-Type: text/plain; charset=UTF-8" -s "' + \
            subject.format(concept) + '" ' + MAIL_RECEIPT
    if (os_name != "nt"):
        os.system(mail)   

#Sends an alarm email if the date passed from the current date is higher than date_alarm
def processAlarmPastDate(current_date, check_date, date_alarm, mail_subject, mail_body, row, concept, os_name):
    try:
        if (check_date != None and isinstance(check_date, date)):
            diff_date = current_date - check_date
            if (diff_date > timedelta(days = date_alarm)):            
                print(str(math.floor(diff_date.days/DAYS_PER_MONTH)) + ' months')
                print(mail_subject)            
                sendMail(mail_subject, mail_body, str(row), concept, str(check_date.strftime('%d, %b %Y')), str(math.floor(diff_date.days/DAYS_PER_MONTH)), os_name)
    except ValueError:
        global error_count
        error_count = error_count + 1        

#Sends an alarm email if the date passed from the current date is higher than date_alarm
def processAlarmFutureDate(current_date, check_date, date_alarm, mail_subject, mail_body, row, concept, os_name):
    try:
        if (check_date != None and isinstance(check_date, date)):
            diff_date = check_date - current_date
            if (diff_date < timedelta(days = date_alarm)):            
                print(str(math.floor(diff_date.days/DAYS_PER_MONTH)) + ' months')
                print(mail_subject)            
                sendMail(mail_subject, mail_body, str(row), concept, str(check_date.strftime('%d, %b %Y')), str(math.floor(diff_date.days/DAYS_PER_MONTH)), os_name)
    except ValueError:
        global error_count
        error_count = error_count + 1        

#Sends SMS using Mensatek service
def sendSMSMensatek(phone, body, company_amount):
    url = 'http://api.mensatek.com/sms/v5/enviar.php'
    values = {'Correo' : MENSATEK_USERNAME,
              'Passwd' : MENSATEK_PASSWORD,
              'Remitente' : 'Temboury',
              'Destinatarios' : '34' + str(phone),
              'Mensaje' : body.format(str(round(company_amount, 2))),
              'Resp' : 'JSON' }     
    data = urllib.parse.urlencode(values)
    req = urllib.request.Request(url, data.encode('ascii'))
    response = urllib.request.urlopen(req)
    print(response.geturl())
    print(response.info())
    respuesta = response.read()
    print(respuesta)
    
    
MBLOX_USERNAME = "customerfu13"
MBLOX_PASSWORD = "t86Bojie"
def sendSMSMblox(phone, body, company_amount):
    url = 'https://sms1.mblox.com:9444/HTTPSMS'
    values = {'UN' : MBLOX_USERNAME,
              'P' : MBLOX_PASSWORD,
              'sa' : 'Temboury',
              'da' : '34' + phone,
              'm' : body.format(str(round(company_amount, 2))),
              'ur' : 'AF31C0D',
              'dr' : '1' }
    data = urllib.parse.urlencode(values)
    req = urllib.request.Request(url, data.encode('ascii'))
    response = urllib.request.urlopen(req)
    print(response.geturl())
    print(response.info())
    respuesta = response.read()
    print(respuesta)
    
    
sms = 1

def sendSMSMblox2(phone, body, company_amount):
    global sms
    
    if (sms == 1):        
        try:
            SendSMS.init(MBLOX_USERNAME, MBLOX_PASSWORD)
            sms = SMS({ 'da': phone, 'sa': "Temboury", 'm': body.format(str(round(company_amount, 2))) })
            # Set the user reference, and set delivery receipts to 1
            sms.setOptional( { 'dc': '1' } )
            responses = sendSMS({ 'SMS': sms });
            print("SMS Response:")
            for response in responses:
                print(response)
        except Exception as inst:
            print("Could not send MBlox SMS, " + str(inst))
        sms = 0


#Process the SMS alarm and sends a SMS to the customer 
def processPaymentSMS(pay_date, company_amount, phone, os_name):   
    try: 
        if (pay_date is None) and (company_amount is not None) and (company_amount > 0) and (phone is not None):
            print("Alarma de SMS!!")
            if (os_name != "nt"):
                #sendSMSClickatell('34679269491', SMS_BODY, company_amount) 
                #sendSMSMblox1('679269491', SMS_BODY, company_amount)
                sendSMSMensatek(phone, SMS_BODY, company_amount)               
            #else:            
            #    sendSMSMblox2('34679269491', SMS_BODY, company_amount)
    except ValueError:
        error_count = error_count + 1
        sendNormalMail(DEBUG_MAIL_RECEIPT, DEBUG_MAIL_SUBJECT_NOK, DEBUG_MAIL_BODY_NOK, os_name)
    
    

#####################################################################################
#                MAIN
#####################################################################################


filepath = "Facturacion.xlsx"
if (os.name != "nt"):
    filepath = "/bin/tatiana/Facturacion.xlsx"

wb = load_workbook(filename = filepath, data_only=True)
master = wb['Cobros']
current_date = datetime.now()

i = 2;
try: 
    while (master[CONCEPT_COLUMN + str(i)].value != None):
        concept = master[CONCEPT_COLUMN + str(i)].value
        phone = master[PHONE_COLUMN + str(i)].value
        claim_date = master[CLAIM_DATE_COLUMN + str(i)].value
        accident_date = master[ACCIDENT_DATE_COLUMN + str(i)].value
        pay_date = master[PAY_DATE_COLUMN + str(i)].value
        company_amount = master[COMPANY_AMOUNT_COLUMN + str(i)].value
        finished = master[FINISHED_COLUMN + str(i)].value
        print('Concept: ' + concept + ', Phone: ' + str(phone) + ', Claim Date: ' + str(claim_date) + ', Prescription date: ' + str(accident_date) + 
              ', Pay date: ' + str(pay_date) + ', Company amount: ' + str(company_amount) + ', Finished: ' + str(finished))
        if (finished is not None and finished.upper() != 'SI'):
            #Process claim date alarm
            processAlarmPastDate(current_date, claim_date, CLAIM_DATE_ALARM, MAIL_SUBJECT_CLAIM_ALARM, MAIL_BODY_CLAIM_ALARM, i, concept, os.name)
            #Process accident date alarm    
            processAlarmFutureDate(current_date, accident_date, ACCIDENT_DATE_ALARM, MAIL_SUBJECT_ACCIDENT_ALARM, MAIL_BODY_ACCIDENT_ALARM, i, concept, os.name)
            #Process SMS remainder for payment
            processPaymentSMS(pay_date, company_amount, phone, os.name)
        i = i + 1
    
    if error_count == 0:
        sendNormalMail(DEBUG_MAIL_RECEIPT, DEBUG_MAIL_SUBJECT_OK, DEBUG_MAIL_BODY_OK, os.name)
        print("Finished OK")
    else: 
        sendNormalMail(DEBUG_MAIL_RECEIPT, DEBUG_MAIL_SUBJECT_NOK, DEBUG_MAIL_BODY_NOK, os.name)
        print("Finished NOK!!!!!!")
except ValueError:
    sendNormalMail(DEBUG_MAIL_RECEIPT, DEBUG_MAIL_SUBJECT_NOK, DEBUG_MAIL_BODY_NOK, os.name)
    print("Finished NOK at line " + i + "!!!!!!")
    
    
    

#################################################################################
### Other vendors SMS
#################################################################################

CLICKATELL_TOKEN = "oWlwla05NDXa013K9rU7ns4hw4k2MCDk7hmZvnkR8N4bOw0XTSr8QlvN1WIpBxw4L4"
MBLOX_TOKEN = "02a633c74ee042cf8d525a28d8bf0046"
MBLOX_REST_USERNAME = "customerfu12"           
SMS_MBLOX_REQUEST = "-X POST " \
                    "-H \"Authorization: Bearer {}\" " \
                    "-H \"Content-Type: application/json\"  -d '" \
                    "{{ \"from\": \"12345\"," \
                    "  \"to\": [\"{}\"]," \
                    "  \"body\": \"{}\" }}' " \
                    "https://api.mblox.com/xms/v1/{}/batches"



def sendSMSClickatell(phone, body, company_amount):
    clickatell = Rest(CLICKATELL_TOKEN);
    response = clickatell.sendMessage([phone], body.format(str(round(company_amount, 2))))    
     
    for entry in response: 
        print(entry['error']) 
        #print(entry['errorCode']) 
        # entry['id'] 
        # entry['destination'] 
        # entry['error'] 
        # entry['errorCode']

def sendSMSMblox1(phone, body, company_amount):
    try:
        request = SMS_MBLOX_REQUEST.format(MBLOX_TOKEN, phone, body.format(str(round(company_amount, 2))), MBLOX_REST_USERNAME)
        print(request)
        call(["curl", request])
    except Exception as inst:
        print("Could not send MBlox SMS, " + str(inst))
        



    
