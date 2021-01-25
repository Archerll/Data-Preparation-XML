# -*- coding: utf-8 -*-

__author__ = 'Archer'
import pandas as pd
import hashlib
import xml.etree.ElementTree as ET
import os
import re
import tkinter as tk
import uuid

from tkinter import messagebox
from xml.dom.minidom import Document
from datetime import datetime as dt
# 注册命名空间
ET.register_namespace('sfa', 'urn:oecd:ties:stffatcatypes:v2')
ET.register_namespace('ftc', 'urn:oecd:ties:fatca:v2')
sfa = {'sfa': 'urn:oecd:ties:stffatcatypes:v2'}
ftc = {'ftc': 'urn:oecd:ties:fatca:v2'}
# Example ID
tin = ''
FATCAEntitySenderId = ''


# 格式化32字字符串
def sta_str(strs):
    return strs[:8]+'-'+strs[8:12]+'-'+strs[12:16]+'-'+strs[16:20]+'-'+strs[20:]


# 检测数据字段格式是否合规
def check_string(strs):
    string = str(strs)
    if re.search('[<>\*\&\'\"\#/]', string) or re.search('\-\-', string):
        print('数据格式异常！')
        return False
    return True


# 检测金额数据是否合规
def check_curr(currCode, balance, payment):
    if currCode == 'JPY':
        if float(balance) == int(float(balance)):
            balance = str(int(float(balance)))
        if payment != 'nan':
            if float(payment) == int(float(payment)):
                payment = str(int(float(payment)))
        if re.search('\.', balance) or re.search('\.', payment):
            print('日元数值异常！')
            # print(re.search('\.', balance), balance)
            # print(re.search('\.', payment))
            return 1
    else:
        if re.search('\.[0-9]{2}', balance) and (re.search('\.[0-9]{2}', payment) or payment == 'nan'):
            return 0
        else:
            print('金额数据异常！')
            return 1
    return 0


# 检查数据是否为Nan
def check_nan(data):
    if data =='nan':
        return True


# 获取md5
def get_md5str(string):
    md = hashlib.md5()
    md.update(str(string).encode('utf-8'))
    strs = md.hexdigest()
    time_md5 = sta_str(strs)
    return time_md5


def type_indic(lastFile, upTest = False):
    if lastFile and upTest:
        typeIndic = 'FATCA14'
    elif not lastFile and upTest:
        typeIndic = 'FATCA11'
    elif lastFile and not upTest:
        typeIndic = 'FATCA4'
    else:
        typeIndic = 'FATCA1'
    return typeIndic


def get_Id():
    tree = ET.parse('FATCA.xml')
    root = tree.getroot()
    # 设置传输信息的唯一ID
    # print(root[0][4].tag+':'+root[0][4].text)
    global tin
    global FATCAEntitySenderId
    tin = root[1][0].find('sfa:TIN', sfa).text
    FATCAEntitySenderId = root[0].find('sfa:SendingCompanyIN', sfa).text


# 为xml设置传输日期和唯一标识
def set_xml(datetime,lastfile, dic):
    tree = ET.parse('FATCA.xml')
    root = tree.getroot()
    if lastfile:
        element1 = ET.Element('sfa:CorrMessageRefId')
        element1.text = dic['MessageRefId']
        element2 = ET.Element('ftc:CorrDocRefId')
        element2.text = dic['FI_DocRefId']
        element3 = ET.Element('ftc:CorrMessageRefId')
        element3.text = dic['MessageRefId']
        root[0].insert(5, element1)
        root[1][0][4].append(element3)
        root[1][0][4].append(element2)

    MessageRefId = root[0].find('sfa:MessageRefId', sfa)
    MessageRefId.text = str(uuid.uuid4())
    ReportingPeriod = root[0].find('sfa:ReportingPeriod', sfa)
    ReportingPeriod.text = '{0}-12-31'.format(datetime.year-1)
    Timestamp = root[0].find('sfa:Timestamp', sfa)
    Timestamp.text = datetime.strftime('%Y-%m-%dT%H:%M:%S')
    DocRefId = root[1][0][4].find('ftc:DocRefId', ftc)
    DocRefId.text = tin+'.'+str(uuid.uuid4())
    # print(root[0][5].tag + ':' + root[0][5].text)
    # print(root[0][6].tag + ':' + root[0][6].text)
    tree.write('FATCA2.xml')


# 将生成的xml中间文件数据读取
def insert_info(file, file_name):
    with open("datas\\{0}.xml".format(file_name), 'r', encoding='UTF8') as cell:
        lines = cell.readlines()[1:]
        print('open {0}.xml success'.format(file_name))
        # print(lines)
        count = 0
        for line in lines:
            file.insert(31 + count, '\t\t' + line)
            count += 1
    return file


# 对于没有数据的情况进行单独处理
def insert_nil_xml(dic, lastFile  = False, upTest = False):
    print("This is a empty excel")
    doc = Document()
    root = doc.createElement('ftc:ReportingGroup')
    doc.appendChild(root)
    cell_root = doc.createElement('ftc:NilReport')
    root.appendChild(cell_root)

    DocSpec = doc.createElement('ftc:DocSpec')
    DocTypeIndic = doc.createElement('ftc:DocTypeIndic')

    typeIndic = type_indic(lastFile, upTest)
    DocTypeIndic.appendChild(doc.createTextNode(typeIndic))
    DocRefId = doc.createElement('ftc:DocRefId')
    Id = tin + '.' + str(uuid.uuid4())
    DocRefId.appendChild(doc.createTextNode(Id))
    DocSpec.appendChild(DocTypeIndic)
    DocSpec.appendChild(DocRefId)
    if lastFile:
        CorrMessageRefId = doc.createElement('ftc:CorrMessageRefId')
        CorrMessageRefId.appendChild(doc.createTextNode(dic['MessageRefId']))
        CorrDocRefId = doc.createElement('ftc:CorrDocRefId')
        CorrDocRefId.appendChild(doc.createTextNode(dic['Nil_DocRefId']))
        DocSpec.appendChild(CorrMessageRefId)
        DocSpec.appendChild(CorrDocRefId)

    NoAccountToReport = doc.createElement('ftc:NoAccountToReport')
    NoAccountToReport.appendChild(doc.createTextNode('yes'))
    cell_root.appendChild(DocSpec)
    cell_root.appendChild(NoAccountToReport)

    root.appendChild(cell_root)
    path = "datas\\Nilreport.xml"
    if os.path.exists(path):
        os.remove(path)
    try:
        with open(path, 'x+', encoding='UTF8') as file:
            doc.writexml(file, addindent='\t', newl='\n', encoding='UTF-8')
            print('Nilreport data write successfully')
    except Exception as err:
        print('错误：{err}'.format(err=err))

    with open('FATCA.xml', 'r+', encoding='utf8') as temp_xml:
        file = temp_xml.readlines()
        print('open info.xml success')
        file.insert(0, '<?xml version="1.0" encoding="UTF-8"?>')
        # print(file)
        file = insert_info(file, 'Nilreport')
        path = 'final_file\\{0}.xml'.format(FATCAEntitySenderId)
        if os.path.exists(path):
            os.remove(path)
        with open(path, 'x', encoding='UTF8') as tag_file:
            for f in file:
                tag_file.write(f)
        print('End of data write')


# 将存储数据与传输信息生成xml文件
def insert_xml():
    with open('FATCA.xml', 'r+', encoding='utf8') as temp_xml:
        file = temp_xml.readlines()
        print('open info.xml success')
        file.insert(0, '<?xml version="1.0" encoding="UTF-8"?>')
        # print(file)
        file = insert_info(file, 'FATCA_主动非财务实体_(Active NFE)')
        file = insert_info(file, 'FATCA_控权人_(Controlling Persons)')
        path = 'final_file\\{0}.xml'.format(FATCAEntitySenderId)
        if os.path.exists(path):
            os.remove(path)
        with open(path, 'x', encoding='UTF8') as tag_file:
            for f in file:
                tag_file.write(f)
        print('End of data write')


def check_last_file(datetime):
    path = 'final_file\\{0}.xml'.format(FATCAEntitySenderId)
    lastfile = False
    dic = {}
    if os.path.exists(path):
        tree = ET.parse(path)
        root = tree.getroot()
        if root[0].find('sfa:ReportingPeriod', sfa).text == '{0}-12-31'.format(str(datetime.year-1)):
            lastfile = True
            dic['MessageRefId'] = root[0].find('sfa:MessageRefId', sfa).text
            dic['FI_DocRefId'] = root[1][0][4].find('ftc:DocRefId', ftc).text

            ReportingGroup = root[1].findall('ftc:ReportingGroup', ftc)
            for elemnts in ReportingGroup:
                if elemnts.find('ftc:NilReport', ftc):
                    dic['Nil_DocRefId'] = elemnts[0][0].find('ftc:DocRefId', ftc) .text
                else:
                    AccountReports = elemnts.findall('ftc:AccountReport', ftc)
                    for AccountReport in  AccountReports:
                        AccountNumber = AccountReport.find('ftc:AccountNumber', ftc).text
                        dic[AccountNumber] = AccountReport[0].find('ftc:DocRefId', ftc).text
            # print(dic)

    return lastfile, dic


class WriteXml(object):

    def __init__(self, file_name, datetime, lastfile, dic):
        self.file_name = file_name
        self.checkNan = False
        self.doc = Document()
        self.datetime = datetime
        self.lastfile = last_file
        self.dic = dic

        # 创建根节点
        self.root = self.doc.createElement('ftc:ReportingGroup')
        self.doc.appendChild(self.root)


    def check_numId(self,num):
        if self.dic.get(num) is None:
            return False
        return True

    # 读取excel数据
    def get_data_from_excel(self):
        try:
            sheet = pd.read_excel('{0}.xlsx'.format(self.file_name), index_col=None, skiprows=[i for i in range(3)], dtype=str)
            datas = sheet[0:-2]
            print('data read successfully')
            np_datas = datas.to_numpy(dtype=str)
            count = 0
            for datas in np_datas:
                for data in datas:
                    if check_string(data) is False:
                        count += 1
            if count != 0:
                messagebox.showinfo("警告！", "{0}数据中存在非法字符 --、/* 、 &、#、<、> ".format(self.file_name))
            #     print(str(data[5])[0:-2])
        except IOError as err:
            print('错误：{err}'.format(err=err))
        return np_datas
        # pass

    # 创建生成《FATCA_控权人_(Controlling Persons)》的AccountReport
    def create_control_xml(self, data):

        for i in [0, 2, 3, 4, 5, 6]:
            checknan = check_nan(str(data[i]))
            if checknan:
                self.checkNan = checknan

        if data[5] != 'JPY':
            if data[6] != 'nan' :
                data[6] = '{:.2f}'.format(float(data[6]))
            if data[7] != 'nan':
                data[7] = '{:.2f}'.format(float(data[7]))

        cell_root = self.doc.createElement('ftc:AccountReport')
        self.root.appendChild(cell_root)
        DocSpec = self.doc.createElement('ftc:DocSpec')
        DocTypeIndic = self.doc.createElement('ftc:DocTypeIndic')
        TypeIndic = type_indic(self.lastfile)
        DocTypeIndic.appendChild(self.doc.createTextNode(TypeIndic))
        DocRefId = self.doc.createElement('ftc:DocRefId')
        Id = tin + '.' + str(uuid.uuid4())
        DocRefId.appendChild(self.doc.createTextNode(Id))
        DocSpec.appendChild(DocTypeIndic)
        DocSpec.appendChild(DocRefId)
        if self.check_numId(data[0]):
            CorrMessageRefId = self.doc.createElement('ftc:CorrMessageRefId')
            CorrMessageRefId.appendChild(self.doc.createTextNode(dic['MessageRefId']))
            CorrDocRefId = self.doc.createElement('ftc:CorrDocRefId')
            CorrDocRefId.appendChild(self.doc.createTextNode(dic[data[0]]))
            DocSpec.appendChild(CorrMessageRefId)
            DocSpec.appendChild(CorrDocRefId)

        AccountNumber = self.doc.createElement('ftc:AccountNumber')
        AccountNumber.appendChild(self.doc.createTextNode(str(data[0])))
        if data[1] !='nan':
            AccountClosed = self.doc.createElement('ftc:AccountClosed')
            AccountClosed.appendChild(self.doc.createTextNode(str(data[1])))
        AccountHolder = self.doc.createElement('ftc:AccountHolder')
        Organisation = self.doc.createElement('ftc:Organisation')
        Name = self.doc.createElement('sfa:Name')
        Name.appendChild(self.doc.createTextNode(str(data[2])))

        # Address标签
        Address = self.doc.createElement('sfa:Address')
        CountryCode = self.doc.createElement('sfa:CountryCode')
        CountryCode.appendChild(self.doc.createTextNode('US'))
        AddressFree = self.doc.createElement('sfa:AddressFree')
        AddressFree.appendChild(self.doc.createTextNode(str(data[3])))
        Address.appendChild(CountryCode)
        Address.appendChild(AddressFree)

        Organisation.appendChild(Name)
        Organisation.appendChild(Address)
        AcctHolderType = self.doc.createElement('ftc:AcctHolderType')
        AcctHolderType.appendChild(self.doc.createTextNode(str(data[4])))
        AccountHolder.appendChild(Organisation)
        AccountHolder.appendChild(AcctHolderType)
        AccountBalance = self.doc.createElement('ftc:AccountBalance')
        # 检查金额格式 currCode , balance , payment
        signCurr = check_curr(str(data[5]), str(data[6]), str(data[7]))
        AccountBalance.appendChild(self.doc.createTextNode(str(data[6])))
        AccountBalance.setAttribute('currCode', str(data[5]))
        Payment = self.doc.createElement('ftc:Payment')
        Type = self.doc.createElement('ftc:Type')
        Type.appendChild(self.doc.createTextNode('FATCA502'))
        checkPay = False
        if str(data[7]) != 'nan':
            PaymentAmnt = self.doc.createElement('ftc:PaymentAmnt')
            PaymentAmnt.appendChild(self.doc.createTextNode(str(data[7])))
            PaymentAmnt.setAttribute('currCode', str(data[5]))
            Payment.appendChild(Type)
            Payment.appendChild(PaymentAmnt)
            checkPay = True
        cell_root.appendChild(DocSpec)
        cell_root.appendChild(AccountNumber)
        cell_root.appendChild(AccountHolder)

        count = 0
        for i in range(3):
            if str(data[8+i*3]) != 'nan':
                count += 1
            else:
                break
        for i in range(count):
            SubstantialOwner = self.doc.createElement('ftc:SubstantialOwner')
            Organisation = self.doc.createElement('ftc:Organisation')
            TIN = self.doc.createElement('sfa:TIN')
            TIN.appendChild(self.doc.createTextNode(str(data[10+i*3])))
            Sub_Name = self.doc.createElement('sfa:Name')
            Sub_Name.appendChild(self.doc.createTextNode(str(data[8+i*3])))
            Sub_Address = self.doc.createElement('sfa:Address')
            Sub_CountryCode = self.doc.createElement('sfa:CountryCode')
            Sub_CountryCode.appendChild(self.doc.createTextNode('US'))
            Sub_AddressFree = self.doc.createElement('sfa:AddressFree')
            Sub_AddressFree.appendChild(self.doc.createTextNode(str(data[9 + 3 * i])))
            Sub_Address.appendChild(Sub_CountryCode)
            Sub_Address.appendChild(Sub_AddressFree)

            Organisation.appendChild(TIN)
            Organisation.appendChild(Sub_Name)
            Organisation.appendChild(Sub_Address)
            SubstantialOwner.appendChild(Organisation)
            cell_root.appendChild(SubstantialOwner)
        cell_root.appendChild(AccountBalance)
        if checkPay:
            cell_root.appendChild(Payment)

        return signCurr

    # 创建生成《FATCA_主动非财务实体_(Active NFE)》的AccountReport
    def create_act_xml(self, data):

        for i in [0, 2, 3, 4, 5, 6, 7]:
            checknan = check_nan(str(data[i]))
            if checknan:
                self.checkNan = checknan

        if data[6] != 'JPY':
            if data[7] != 'nan' :
                data[7] = '{:.2f}'.format(float(data[7]))
            if data[8] != 'nan':
                data[8] = '{:.2f}'.format(float(data[8]))

        cell_root = self.doc.createElement('ftc:AccountReport')
        self.root.appendChild(cell_root)
        DocSpec = self.doc.createElement('ftc:DocSpec')
        DocTypeIndic = self.doc.createElement('ftc:DocTypeIndic')
        DocTypeIndic.appendChild(self.doc.createTextNode('FATCA11'))
        DocRefId = self.doc.createElement('ftc:DocRefId')
        Id = tin+'.'+str(uuid.uuid4())
        DocRefId.appendChild(self.doc.createTextNode(Id))
        DocSpec.appendChild(DocTypeIndic)
        DocSpec.appendChild(DocRefId)
        if self.check_numId(data[0]):
            CorrMessageRefId = self.doc.createElement('ftc:CorrMessageRefId')
            CorrMessageRefId.appendChild(self.doc.createTextNode(dic['MessageRefId']))
            CorrDocRefId = self.doc.createElement('ftc:CorrDocRefId')
            CorrDocRefId.appendChild(self.doc.createTextNode(dic[data[0]]))
            DocSpec.appendChild(CorrMessageRefId)
            DocSpec.appendChild(CorrDocRefId)

        AccountNumber = self.doc.createElement('ftc:AccountNumber')
        AccountNumber.appendChild(self.doc.createTextNode(str(data[0])))
        AccountHolder = self.doc.createElement('ftc:AccountHolder')
        Organisation = self.doc.createElement('ftc:Organisation')
        TIN = self.doc.createElement('sfa:TIN')
        TIN.appendChild(self.doc.createTextNode(str(data[5])[0:-2]))
        Name = self.doc.createElement('sfa:Name')
        Name.appendChild(self.doc.createTextNode(str(data[2])))

        Address = self.doc.createElement('sfa:Address')
        CountryCode = self.doc.createElement('sfa:CountryCode')
        CountryCode.appendChild(self.doc.createTextNode('US'))
        AddressFree = self.doc.createElement('sfa:AddressFree')
        AddressFree.appendChild(self.doc.createTextNode(str(data[3])))
        Address.appendChild(CountryCode)
        Address.appendChild(AddressFree)

        Organisation.appendChild(TIN)
        Organisation.appendChild(Name)
        Organisation.appendChild(Address)
        AcctHolderType = self.doc.createElement('ftc:AcctHolderType')
        AcctHolderType.appendChild(self.doc.createTextNode(str(data[4])))
        AccountHolder.appendChild(Organisation)
        AccountHolder.appendChild(AcctHolderType)
        signCurr = check_curr(str(data[6]), str(data[7]), str(data[8]))
        AccountBalance = self.doc.createElement('ftc:AccountBalance')
        AccountBalance.appendChild(self.doc.createTextNode(str(data[7])))
        AccountBalance.setAttribute('currCode', str(data[6]))
        Payment = self.doc.createElement('ftc:Payment')
        Type = self.doc.createElement('ftc:Type')
        Type.appendChild(self.doc.createTextNode('FATCA502'))
        checkPay = False
        if str(data[8]) != 'nan':
            PaymentAmnt = self.doc.createElement('ftc:PaymentAmnt')
            PaymentAmnt.appendChild(self.doc.createTextNode(str(data[8])))
            PaymentAmnt.setAttribute('currCode', str(data[6]))
            Payment.appendChild(Type)
            Payment.appendChild(PaymentAmnt)
            checkPay = True

        cell_root.appendChild(DocSpec)
        cell_root.appendChild(AccountNumber)
        cell_root.appendChild(AccountHolder)
        cell_root.appendChild(AccountBalance)
        if checkPay:
            cell_root.appendChild(Payment)

        return signCurr

        # 将生成的数据单独存放在一个xml文件中

    def xml_group(self):
        datas = self.get_data_from_excel()
        checkEmpty = True
        for data in datas[0]:
            if not check_nan(data):
                checkEmpty = False
        # 如果校验为空，则返回标志 2
        if checkEmpty is True:
            return 2

        count = 0  # count 数据行
        sign = 0  # sign 数据异常标记
        if self.file_name == 'FATCA_主动非财务实体_(Active NFE)':
            for data in datas:
                if sign == 0:
                    sign = self.create_act_xml(data, count)
                else:
                    self.create_act_xml(data, count)
                count += 1
        else:
            for data in datas:
                if sign == 0:
                    sign = self.create_control_xml(data, count)
                else:
                    self.create_control_xml(data, count)
                count += 1

        if self.checkNan:
            messagebox.showinfo("警告！", "{0}数据中的AccountNumber、Name、Address、Account Holder Type、币种、结余存在空值，需要校验后重新执行 ".format(self.file_name))
        if sign != 0:
            messagebox.showinfo("警告！", "{0}数据中的金额数值存在{1}个异常数据，需要校验后重新执行 ".format(self.file_name,sign))
        if self.checkNan or sign != 0:
            return 1
        path = "datas\\{0}.xml".format(self.file_name)
        if os.path.exists(path):
            os.remove(path)
        try:
            with open(path, 'x+', encoding='UTF8') as file:
                self.doc.writexml(file, addindent='\t', newl='\n', encoding='UTF-8')
                print('{0} data write successfully'.format(self.file_name))
        except Exception as err:
            print('错误：{err}'.format(err=err))
        return 0


if __name__ == '__main__':
    # 提示框设置
    tip = tk.Tk()
    tip.withdraw()
    get_Id()
    datetime = dt.now()

    # 检查是否已生成文件
    last_file, dic = check_last_file(datetime)

    # 配置FATCA.xml文件
    set_xml(datetime, last_file, dic)

    checkNonError1 = 0
    checkNonError2 = 0
    work1 = WriteXml('FATCA_主动非财务实体_(Active NFE)', datetime, last_file, dic)
    # work1.get_data_from_excel()
    work2 = WriteXml('FATCA_控权人_(Controlling Persons)', datetime, last_file, dic)
    checkNonError1 = work1.xml_group()
    checkNonError2 = work2.xml_group()
    if checkNonError1 == 0 and checkNonError2 == 0:
        insert_xml()
    elif checkNonError1 == 2 and checkNonError2 == 2:
        insert_nil_xml()