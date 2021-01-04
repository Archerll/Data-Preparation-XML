# -*- coding: utf-8 -*-

__author__ = 'Archer'
import pandas as pd
import hashlib
from xml.dom.minidom import Document
import xml.etree.ElementTree as ET
from datetime import datetime as dt

# 注册命名空间
ET.register_namespace('sfa', 'urn:oecd:ties:stffatcatypes:v2')
ET.register_namespace('fta', 'urn:oecd:ties:fatca:v2')
sfa = {'sfa': 'urn:oecd:ties:stffatcatypes:v2'}
fta = {'fta': 'urn:oecd:ties:fatca:v2'}
# Example ID
tin = '2IW3WK.00000.LE.152'
FATCAEntitySenderId = '000000.00000.TA.840'


# 格式化32字字符串
def sta_str(strs):
    return strs[:8]+'-'+strs[8:12]+'-'+strs[12:16]+'-'+strs[16:20]+'-'+strs[20:]


# 获取md5
def get_md5str(datetime):
    md = hashlib.md5()
    md.update(str(datetime).encode('utf-8'))
    strs = md.hexdigest()
    time_md5 = sta_str(strs)
    return time_md5


# 为xml设置传输日期和唯一标识
def set_xml(datetime):
    tree = ET.parse('FATCA.xml')
    root = tree.getroot()
    # 设置传输信息的唯一ID
    # print(root[0][4].tag+':'+root[0][4].text)
    ReportingPeriod = root[0].find('sfa:ReportingPeriod', sfa)
    ReportingPeriod.text = datetime.date().strftime('%Y-%m-%d')
    Timestamp = root[0].find('sfa:Timestamp', sfa)
    Timestamp.text = datetime.strftime('%Y-%m-%dT%H:%M:%S')
    DocRefId = root[1][0][4].find('fta:DocRefId', fta)
    DocRefId.text = tin+'.'+get_md5str(datetime)
    # print(root[0][5].tag + ':' + root[0][5].text)
    # print(root[0][6].tag + ':' + root[0][6].text)
    tree.write('FATCA.xml')


def insert_info(file, file_name):
    with open("datas\\{0}.xml".format(file_name), 'r', encoding='UTF8') as cell:
        lines = cell.readlines()[1:]
        print('open {0}.xml success'.format(file_name))
        # print(lines)
        count = 0
        for line in lines:
            file.insert(30 + count, '\t\t' + line)
            count += 1
    return file


# 将存储数据与传输信息生成xml文件
def insert_xml():
    with open('FATCA.xml', 'r+', encoding='utf8') as temp_xml:
        file = temp_xml.readlines()
        print('open info.xml success')
        # print(file)
        file = insert_info(file, 'FATCA_主动非财务实体_(Active NFE)')
        file = insert_info(file, 'FATCA_控权人_(Controlling Persons)')
        with open('final_file\\{0}.xml'.format(FATCAEntitySenderId), 'x', encoding='UTF8') as tag_file:
            for f in file:
                tag_file.write(f)
        print('End of data write')


class WriteXml(object):

    def __init__(self, file_name, datetime):
        self.file_name = file_name
        self.doc = Document()
        self.datetime = datetime
        # 创建根节点
        self.root = self.doc.createElement('ReportingGroup')
        self.doc.appendChild(self.root)

    # 读取excel数据
    def get_data_from_excel(self):
        sheet = pd.read_excel('{0}.xlsx'.format(self.file_name), index_col=None, skiprows=[i for i in range(3)])
        datas = sheet[0:-2]
        print('data read successfully')
        np_datas = datas.to_numpy()
        # for data in np_datas:
        #     print(data)
        #     print(str(data[5])[0:-2])
        return np_datas
        # pass

    def create_control_xml(self, data):
        cell_root = self.doc.createElement('ftc:AccountReport')
        self.root.appendChild(cell_root)
        DocSpec = self.doc.createElement('ftc:DocSpec')
        DocTypeIndic = self.doc.createElement('ftc:DocTypeIndic')
        DocTypeIndic.appendChild(self.doc.createTextNode('FATCA11'))
        DocRefId = self.doc.createElement('ftc:DocRefId')
        DocRefId.appendChild(self.doc.createTextNode('1'))
        DocSpec.appendChild(DocTypeIndic)
        DocSpec.appendChild(DocRefId)
        AccountNumber = self.doc.createElement('ftc:AccountNumber')
        AccountNumber.appendChild(self.doc.createTextNode(str(data[0])))
        if data[1] is not None:
            AccountClosed = self.doc.createElement('ftc:AccountClosed')
            AccountClosed.appendChild(self.doc.createTextNode(str(data[1])))
        AccountHolder = self.doc.createElement('ftc:AccountHolder')
        Organisation = self.doc.createElement('ftc:Organisation')
        Name = self.doc.createElement('sfa:Name')
        Name.appendChild(self.doc.createTextNode(str(data[2])))
        Address = self.doc.createElement('sfa:Address')
        Address.appendChild(self.doc.createTextNode(str(data[3])))
        Organisation.appendChild(Name)
        Organisation.appendChild(Address)
        AcctHolderType = self.doc.createElement('ftc:AcctHolderType')
        AcctHolderType.appendChild(self.doc.createTextNode(str(data[4])))
        AccountHolder.appendChild(Organisation)
        AccountHolder.appendChild(AcctHolderType)
        AccountBalance = self.doc.createElement('ftc:AccountBalance')
        AccountBalance.appendChild(self.doc.createTextNode(str(data[6])))
        AccountBalance.setAttribute('currCode', str(data[5]))
        Payment = self.doc.createElement('ftc:Payment')
        Type = self.doc.createElement('ftc:Type')
        Type.appendChild(self.doc.createTextNode('FATCA502'))
        PaymentAmnt = self.doc.createElement('ftc:PaymentAmnt')
        PaymentAmnt.appendChild(self.doc.createTextNode(str(data[7])))
        PaymentAmnt.setAttribute('currCode', str(data[5]))
        Payment.appendChild(Type)
        Payment.appendChild(PaymentAmnt)
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
            SubstantialOwner = self.doc.createElement('SubstantialOwner')
            Individual = self.doc.createElement('Individual')
            TIN = self.doc.createElement('TIN')
            TIN.appendChild(self.doc.createTextNode(str(data[10+i*3])))
            Sub_Name = self.doc.createElement('Name')
            Sub_Name.appendChild(self.doc.createTextNode(str(data[8+i*3])))
            Sub_Address = self.doc.createElement('Address')
            Sub_Address.appendChild(self.doc.createTextNode(str(data[9+3*i])))
            Individual.appendChild(TIN)
            Individual.appendChild(Sub_Name)
            Individual.appendChild(Sub_Address)
            SubstantialOwner.appendChild(Individual)
            cell_root.appendChild(SubstantialOwner)
        cell_root.appendChild(AccountBalance)
        cell_root.appendChild(Payment)

    def create_act_xml(self, data):
        cell_root = self.doc.createElement('ftc:AccountReport')
        self.root.appendChild(cell_root)
        DocSpec = self.doc.createElement('ftc:DocSpec')
        DocTypeIndic = self.doc.createElement('ftc:DocTypeIndic')
        DocTypeIndic.appendChild(self.doc.createTextNode('FATCA11'))
        DocRefId = self.doc.createElement('ftc:DocRefId')
        DocRefId.appendChild(self.doc.createTextNode('1'))
        DocSpec.appendChild(DocTypeIndic)
        DocSpec.appendChild(DocRefId)
        AccountNumber = self.doc.createElement('ftc:AccountNumber')
        AccountNumber.appendChild(self.doc.createTextNode(str(data[0])))
        AccountHolder = self.doc.createElement('ftc:AccountHolder')
        Organisation = self.doc.createElement('ftc:Organisation')
        TIN = self.doc.createElement('sfa:TIN')
        TIN.appendChild(self.doc.createTextNode(str(data[5])[0:-2]))
        Name = self.doc.createElement('sfa:Name')
        Name.appendChild(self.doc.createTextNode(str(data[2])))
        Address = self.doc.createElement('sfa:Address')
        Address.appendChild(self.doc.createTextNode(str(data[3])))
        Organisation.appendChild(TIN)
        Organisation.appendChild(Name)
        Organisation.appendChild(Address)
        AcctHolderType = self.doc.createElement('ftc:AcctHolderType')
        AcctHolderType.appendChild(self.doc.createTextNode(str(data[4])))
        AccountHolder.appendChild(Organisation)
        AccountHolder.appendChild(AcctHolderType)
        AccountBalance = self.doc.createElement('ftc:AccountBalance')
        AccountBalance.appendChild(self.doc.createTextNode(str(data[7])))
        AccountBalance.setAttribute('currCode', str(data[6]))
        Payment = self.doc.createElement('ftc:Payment')
        Type = self.doc.createElement('ftc:Type')
        Type.appendChild(self.doc.createTextNode('FATCA502'))
        PaymentAmnt = self.doc.createElement('ftc:PaymentAmnt')
        PaymentAmnt.appendChild(self.doc.createTextNode(str(data[8])))
        PaymentAmnt.setAttribute('currCode', str(data[6]))
        Payment.appendChild(Type)
        Payment.appendChild(PaymentAmnt)

        cell_root.appendChild(DocSpec)
        cell_root.appendChild(AccountNumber)
        cell_root.appendChild(AccountHolder)
        cell_root.appendChild(AccountBalance)
        cell_root.appendChild(Payment)

        # 将生成的数据单独存放在一个xml文件中
    def xml_group(self):
        datas = self.get_data_from_excel()
        count = 0
        if self.file_name == 'FATCA_主动非财务实体_(Active NFE)':
            for data in datas:
                self.create_act_xml(data)
                count += 1
        else:
            for data in datas:
                self.create_control_xml(data)
                count += 1
        try:
            with open("datas\\{0}.xml".format(self.file_name), 'x+', encoding='UTF8') as file:
                self.doc.writexml(file, addindent='\t', newl='\n', encoding='UTF-8')
                print('data write successfully')
        except Exception as err:
            print('错误：{err}'.format(err=err))


if __name__ == '__main__':

    datetime = dt.now()
    set_xml(datetime)
    work1 = WriteXml('FATCA_主动非财务实体_(Active NFE)', datetime)
    work1.get_data_from_excel()
    work2 = WriteXml('FATCA_控权人_(Controlling Persons)', datetime)
    work1.xml_group()
    work2.xml_group()
    insert_xml()
