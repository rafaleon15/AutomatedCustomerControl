"""This python module is designed to facilitate the construction of
   applications which communicate with HTTPSMS servers. The major
   function is sendSMS, which, when the module has been initialised,
   can be used to send SMS messages via an HTTPSMS server.

   This module should be imported in the usual way. Any misuse of its
   functions is likely to result in an SMSClientError, which should
   indicate the problem.

   Copyright (C) 2007 CardBoardFish http://www.cardboardfish.com/"""
import http.client

from urllib.parse import quote_plus as _quote
from time import time as _time
import sys
import re

__all__ = ("sendSMS","SMS","SMSClientError")

class SMSClientError(Exception):
   def __init__(self, message):
       self.message = message
   def __str__(self):
       message = self.message
       return message

class SMS:
    def __init__(self, params):
        """Creates SMS objects.

           params should always contain a dictionary with the
           following keys:

             da: a comma separated list of destinations
             sa: the source address
             m: the message text
             optional: a dictionary of optional parameters (optional)

           These inputs are validated by the mutators (set methods)."""
        self.setSA(params['sa'])
        self.setDA(params['da'])
        if 'm' in params:
            self.setMSG(params['m'])
        self.optional = {}
        if 'optional' in params:
            self.setOptional(params['optional'])

    def setSA(self, sa):
        """Set the source address for this message.

           This will usually be a company or service name (max 11 chars)
           or a telephone number (max 16 digits)."""
        valid = re.compile(r"^(\d{1,16}|.{1,11})$")
        if valid.match(sa): self.sa = sa
        else: raise SMSClientError('Source address not valid.')

    def setDA(self, da):
        """Set the destination addresses for this message.

           This should be a comma-separated list of phone numbers, in
           international format without the leading + character.
           Max 10 numbers. Use the dictionary parameter form of sendSMS
           to automatically deal with larger numbers of destinations."""
        dests = da.split(',')
        valid_dests = []
        for dest in dests:
            valid = re.compile(r"^(\+|00)?([1-9][0-9]{7,15})*$")
            m = valid.match(dest)
            if m:
                valid_dests.append(m.group(2))
            else:
                raise SMSClientError('One or more destinations invalid: ' + da)
        self.da = ','.join(valid_dests)

    def setMSG(self, msg):
        """Sets the content of the message.

           This should be pre-coded into the appropriate data coding
           scheme (see optional parameters.) and the value set. If
           left unset, normal encoding will be assumed, and the message
           will be converted to GSM before sending."""
        self.msg = msg

    def setOptional(self, options):
        """Sets the optional parameters. The following keys are currently
           recognised:

             'st': source type of number.

               Should be 0 for national numeric, 1 for international
               numeric, and 5 for alphanumeric.

             'dc': data coding scheme of message:

               0: Flash
               1: Normal
               2: Binary
               4: UCS2
               5: Flash UCS2
               6: Flash GSM
               7: Normal GSM

             'dr': delivery receipt request.

               0 for no, 1 for yes, 2 for record only

             'ur': user reference.

               This should be a unique reference (max 16 chars) supplied
               by the user to aid with matching delivery receipts.

             'ud': user data header.

               This, if given, should be in hexadecimal format.

             'vp': validity period.

               Specifies the number of minutes to attempt delivery for
               until the message expires. Max 10080, default 1440.

             'du': delay until.

               Do not attempt delivery of the message until this time,
               given as a 10 digit UCS timestamp. Applies relative
               to the local time of the computer running, unless
               overridden with the 'lt' key below.

             'lt': local time.

               Gives the local time of the sender, to be used when
               calculating the delay."""
        if 'ur' in options:
            if 1 < len(options['ur']) < 16:
                self.optional['ur'] = options['ur']
            else:
                raise SMSClientError('User reference must be between 1 and 16 characters.')
        if 'st' in options:
            st = options['st']
            if st == '0' or st == '1' or st == '5':
                self.optional['st'] = st
            else:
                raise SMSClientError('Source address type must be 0, 1 or 5.')
        if 'dc' in options:
            dc = options['dc']
            valid = re.compile(r"^[0-24-7]$")
            if valid.match(dc):
                self.optional['dc'] = dc
            else:
                raise SMSClientError('Data coding scheme must be between 0 and 7 excluding 3.')
        if 'dr' in options:
            dr = options['dr']
            valid = re.compile(r"^[0-2]$");
            if valid.match(dr):
                self.optional['dr'] = dr
            else:
                raise SMSClientError('Delivery receipt request must be 0-2.')
        if 'ud' in options:
            ud = options['ud']
            valid = re.compile(r"^[A-Fa-f0-9]{1,18}$")
            if valid.match(ud):
                self.optional['ud'] = ud
            else:
                raise SMSClientError('User data header must be less than 18 hex digits.')
        if 'vp' in options:
            vp = options['vp']
            if 0 < int(vp) <= 10080:
                self.optional['vp'] = vp
            else:
                raise SMSClientError('Validity period must be between 1 and 10080.')
        if 'du' in options:
            if not 'lt' in options:
                self.setOptional({'lt':str(int(_time()))})
            du = options['du']
            valid = re.compile(r"^\d{10}$")
            if valid.match(du):
                self.optional['du'] = du
            else:
                raise SMSClientError('"Delay until" must be a 10 digit UCS timestamp.')
        if 'lt' in options:
            lt = options['lt']
            valid = re.compile(r"^\d{10}$")
            if valid.match(lt):
                self.optional['lt'] = lt
            else:
                raise SMSClientError('Local time must be a 10 digit UCS timestamp.')

def init(un, p, s = 'H'):
    """Initialises the library.

       Given a username, password and optional client type identifier,
       this function sets up this module to interact with HTTPSMS
       servers."""
    global username, password, clientType
    type = re.compile('^(H|S|D|M)$')
    if type.match(s):
        username, password, clientType = un, p, s
    else:
        raise SMSClientError('Client type must be H, S, D, or M.')

def _includeif(sms, field, fieldname):
    if field in sms.optional:
        return '&' + fieldname + '=' + sms.optional[field]
    else:
        return ''

def _GSMEncode(to_encode):
    gsmchar = {
        '\x0A' : '\x0A',
        '\x0D' : '\x0D',

        '\x24' : '\x02',

        '\x40' : '\x00',

        '\x13' : '\x13',
        '\x10' : '\x10',
        '\x19' : '\x19',
        '\x14' : '\x14',
        '\x1A' : '\x1A',
        '\x16' : '\x16',
        '\x18' : '\x18',
        '\x12' : '\x12',
        '\x17' : '\x17',
        '\x15' : '\x15',

        '\x5B' : '\x1B\x3C',
        '\x5C' : '\x1B\x2F',
        '\x5D' : '\x1B\x3E',
        '\x5E' : '\x1B\x14',
        '\x5F' : '\x11',

        '\x7B' : '\x1B\x28',
        '\x7C' : '\x1B\x40',
        '\x7D' : '\x1B\x29',
        '\x7E' : '\x1B\x3D',

        '\x80' : '\x1B\x65',

        '\xA1' : '\x40',
        '\xA3' : '\x01',
        '\xA4' : '\x1B\x65',
        '\xA5' : '\x03',
        '\xA7' : '\x5F',

        '\xBF' : '\x60',

        '\xC0' : '\x41',
        '\xC1' : '\x41',
        '\xC2' : '\x41',
        '\xC3' : '\x41',
        '\xC4' : '\x5B',
        '\xC5' : '\x0E',
        '\xC6' : '\x1C',
        '\xC7' : '\x09',
        '\xC8' : '\x45',
        '\xC9' : '\x1F',
        '\xCA' : '\x45',
        '\xCB' : '\x45',
        '\xCC' : '\x49',
        '\xCD' : '\x49',
        '\xCE' : '\x49',
        '\xCF' : '\x49',

        '\xD0' : '\x44',
        '\xD1' : '\x5D',
        '\xD2' : '\x4F',
        '\xD3' : '\x4F',
        '\xD4' : '\x4F',
        '\xD5' : '\x4F',
        '\xD6' : '\x5C',
        '\xD8' : '\x0B',
        '\xD9' : '\x55',
        '\xDA' : '\x55',
        '\xDB' : '\x55',
        '\xDC' : '\x5E',
        '\xDD' : '\x59',
        '\xDF' : '\x1E',

        '\xE0' : '\x7F',
        '\xE1' : '\x61',
        '\xE2' : '\x61',
        '\xE3' : '\x61',
        '\xE4' : '\x7B',
        '\xE5' : '\x0F',
        '\xE6' : '\x1D',
        '\xE7' : '\x63',
        '\xE8' : '\x04',
        '\xE9' : '\x05',
        '\xEA' : '\x65',
        '\xEB' : '\x65',
        '\xEC' : '\x07',
        '\xED' : '\x69',
        '\xEE' : '\x69',
        '\xEF' : '\x69',

        '\xF0' : '\x64',
        '\xF1' : '\x7D',
        '\xF2' : '\x08',
        '\xF3' : '\x6F',
        '\xF4' : '\x6F',
        '\xF5' : '\x6F',
        '\xF6' : '\x7C',
        '\xF8' : '\x0C',
        '\xF9' : '\x06',
        '\xFA' : '\x75',
        '\xFB' : '\x75',
        '\xFC' : '\x7E',
        '\xFD' : '\x79'
    }
    to_return = []
    for char in to_encode:
        passthrough = re.compile(r"[A-Za-z0-9!\/#%&\"'=\-<>?()*+,.;:]")
        if passthrough.match(char):
            to_return.append(char)
        else:
            if char in gsmchar: to_return.append(gsmchar[char])
            else: to_return.append('\x20')
    return ''.join(to_return)

def _normToGSM(sms):
    sms.msg = _GSMEncode(sms.msg)
    sms.optional['dc'] = '6'

def _flashToGSM(sms):
    sms.msg = _GSMEncode(sms.msg)
    sms.optional['dc'] = '7'

def sendSMS(params):
    """Can be called one of two ways; either with a dictionary of
       parameters, or with an SMS object.

       To call with parameters, use the following keys:

         da: a comma separated list of destinations
         sa: the source address
         m: the message text
         optional: a dictionary of optional parameters (optional)

       If included, optional should have any of the following keys:

         st: source type of number
         dc: data coding scheme
         dr: delivery receipt request
         ur: user reference
         ud: user data header
         vp: validity period
         du: delay until
         lt: local time

       Example:
         replies = sendSMS(
           { 'sa':'Cbf','da':'471234567890,449876543210',
           'm':'This is my test message.', 'optional':{'vp':'2000'}}
         )

       To call with an SMS object, call this function with a dictionary
       containing only the key 'SMS', associated to the object. For more
       details, see the SMS class.

       Example:
         try:
             sms = SMS()
             sendSMS(sms)
         except SMSClientError, e:
             print e

       If used in an incorrect way, an SMSClientError will be thrown.
       It is recommended you catch these and print the exception."""
    if 'SMS' in params:
        m = params['SMS']
        if 'dc'in m.optional:
             if m.optional['dc'] == '0': _flashToGSM(m)
             if m.optional['dc'] == '1': _normToGSM(m)
        else: _normToGSM(m)
        alpha = re.compile(r"[^0-9]");
        if not 'st' in m.optional:
            if alpha.match(m.sa):
                m.optional['st'] = "5"
        try:
            requeststring = '/HTTPSMS?S=' \
              + clientType + '&UN=' + username + '&P=' + password \
              + '&SA=' + _quote(m.sa) + '&DA=' +m.da +'&M='+ _quote(m.msg) \
              + _includeif(m, 'ur', 'UR') + _includeif(m,'ud', 'UD') \
              + _includeif(m, 'st', 'ST') + _includeif(m,'dc', 'DC') \
              + _includeif(m, 'dr', 'DR') + _includeif(m,'vp', 'V') \
              + _includeif(m, 'du', 'DU') + _includeif(m,'lt', 'LT')
        except NameError:
            raise SMSClientError('Module not initialised.')
        try: server = http.client.HTTPConnection('sms1.cardboardfish.com:9001')
        except IOError as e: raise SMSClientError(str(e))
        server.request('GET', requeststring)
        response = server.getresponse()
        code = response.status
        if code == 400: raise SMSClientError('Received "Bad Request" \
          response code from server.')
        elif code == 401: raise SMSClientError('Bad username / \
          password.')
        elif code == 402: raise SMSClientError('Credit too low, \
          payment is required.')
        elif code == 503: raise SMSClientError('Destination invalid.')
        elif code == 500:
            if not 'retry' in m.optional:
                m.optional['retry'] = 1
                return sendSMS({'SMS':m})
            else:
                raise SMSClientError('Internal server error; second attempt also failed.')
        elif code != 200: raise SMSClientError('Unhandled error: ' \
          + str(response.status) + ' ' + response.reason + ' ' \
          + response.read())
        responsestring = response.read()
        replies = _process(responsestring)
        return replies
    else:
        batchsize = 10
        try:
            das = params['da'].split(',')
        except AttributeError:
            raise SMSClientError("Invalid use of method sendSMS.")
        dests = len(das)
        if dests <= batchsize:
            sms = SMS(params)
            return sendSMS({'SMS':sms})
        else:
            batches, base, replies = dests / batchsize + 1, 0, []
            while batches > 0:
                if batches == 1: bsize = dests % batchsize
                else: bsize = batchsize
                top = base + bsize
                batch = das[base:top]
                batchda, newparams = ",".join(batch), params.copy()
                newparams['da'] = batchda
                sms = SMS(newparams)
                try:
                    batchreplies = sendSMS({'SMS':sms})
                except SMSClientError as e:
                    if str(e) == 'Destination invalid.':
                        batchreplies = []
                        for i in enumerate(batch):
                            batchreplies.append('-15')
                    else:
                        raise e
                if batchreplies.count('-20') > 0:
                    retrybatch, newerparams = [], newparams.copy()
                    for i, bda in enumerate(batch):
                        if batchreplies[i] == '-20': retrybatch.append(bda)
                    newerparams['da'] = ','.join(retrybatch)
                    sms2 = SMS(newerparams)
                    retryreplies = sendSMS({'SMS':sms2})
                    for i, br in enumerate(batchreplies):
                        if br == '-20': batchreplies[i] = retryreplies.pop(0)
                replies.extend(batchreplies)
                base, batches = base + batchsize, batches - 1
            return replies

def _process(input):
    responses = input.split()
    last = responses.pop()
    if not last.startswith('UR'):
        responses.append(last)
    responses.pop(0)
    return responses
