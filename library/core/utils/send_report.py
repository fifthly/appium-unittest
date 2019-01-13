# -*- coding: utf-8 -*-

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import Header
import smtplib
import traceback
import requests
import json
import os
import time
import settings

SUBJECT = u'【持续集成】和飞信[%s]集成报告'
HOST = 'smtp.139.com'
PORT = 25
FROM = 'rcsqa@139.com'
PASSWORD = 'yu123456'
# TO = ['13802889470@139.com', '13802883351@139.com', '13802887745@139.com', 'cclu@appstest.cn']
# TO = ['13802883079@139.com', '13802887425@139.com']
# UI_REPORT = os.path.abspath(os.path.abspath(__file__) + '/../../report/ui_automation_report.xlsx')
# 报告路径
UI_REPORT = settings.REPORT_HTML_PATH

FILES = [UI_REPORT]
SONAR_URL = """
http://10.1.0.101:9000/api/measures/component?\
additionalFields=metrics,periods&componentKey=andfetion_android&\
metricKeys=ncloc,bugs,vulnerabilities,code_smells,duplicated_lines_density
"""
PGYER_URL = 'https://www.pgyer.com/apiv2/app/builds'
PGYER_PAYLOAD = {
    '_api_key': '82fe733ec2739d270885b28d7239d185',
    'appKey': '296e3112fabb6768b8abbb0cd54ae6b1'
}
CURRENT_VERSION = u'未知版本'

CODE_CHECK = {
    'LINE': u'暂无数据',
    'BUG': u'暂无数据',
    'VUL': u'暂无数据',
    'SMELL': u'暂无数据',
    'DUP': u'暂无数据'
}

UNIT_TEST = {
    'COVER': u'暂无数据',
    'TOTAL': u'暂无数据',
    'SUCCESS': u'暂无数据',
    'FAIL': u'暂无数据',
    'RATE': u'暂无数据'
}

UI_AUTOMATION = {
    'TOTAL': u'暂无数据',
    'SUCCESS': u'暂无数据',
    'FAIL': u'暂无数据',
    'RATE': u'暂无数据'
}

API_AUTOMATION = {
    'TOTAL': u'暂无数据',
    'SUCCESS': u'暂无数据',
    'FAIL': u'暂无数据',
    'RATE': u'暂无数据'
}


def get_sonar_metric():
    """获取静态代码扫描结果"""
    response = requests.get(SONAR_URL)
    result = json.loads(response.text)
    measures = result['component']['measures']
    global CODE_CHECK
    for measure in measures:
        if measure['metric'] == 'ncloc':
            CODE_CHECK['LINE'] = measure['value']
        elif measure['metric'] == 'bugs':
            CODE_CHECK['BUG'] = measure['value']
        elif measure['metric'] == 'vulnerabilities':
            CODE_CHECK['VUL'] = measure['value']
        elif measure['metric'] == 'code_smells':
            CODE_CHECK['SMELL'] = measure['value']
        elif measure['metric'] == 'duplicated_lines_density':
            CODE_CHECK['DUP'] = measure['value'] + '%'


def get_ui_automation_metric(total, sucess, fail, rate):
    """获取UI自动化测试结果"""
    global UI_AUTOMATION
    UI_AUTOMATION['TOTAL'] = total
    UI_AUTOMATION['SUCCESS'] = sucess
    UI_AUTOMATION['FAIL'] = fail
    UI_AUTOMATION['RATE'] = rate


def get_current_version():
    """获取APP当前版本号"""
    global CURRENT_VERSION
    try:
        response = requests.post(url=PGYER_URL, data=PGYER_PAYLOAD)
        assert response.status_code == 200
        result = json.loads(response.text)
        CURRENT_VERSION = 'V' + result['data']['list'][0]['buildVersion']
    except:
        traceback.print_exc()


def send_mail(*to):
    get_sonar_metric()
    get_current_version()

    mail = MIMEMultipart()
    # 使用Header封装，139会报550错误：Mail rejected
    """
    mail['From'] = Header(u'品质管理部', 'utf-8')
    mail['To'] = Header(u'自研版和飞信', 'utf-8')
    mail['Subject'] = Header(SUBJECT % CURRENT_VERSION, 'utf-8')
    """
    mail['From'] = FROM
    mail['To'] = ','.join(to)
    mail['Subject'] = SUBJECT % CURRENT_VERSION

    # content = open('ci_report.html', 'r', encoding='utf-8').read()
    content = open(settings.EMAIL_REPORT_HTML_TPL, 'r', encoding='utf-8').read()
    content = content.format(
        CODE_CHECK['LINE'], CODE_CHECK['BUG'], CODE_CHECK['VUL'], CODE_CHECK['SMELL'], CODE_CHECK['DUP'],
        UI_AUTOMATION['TOTAL'], UI_AUTOMATION['SUCCESS'], UI_AUTOMATION['FAIL'], UI_AUTOMATION['RATE'],
        UNIT_TEST['COVER'], UNIT_TEST['TOTAL'], UNIT_TEST['SUCCESS'], UNIT_TEST['FAIL'], UNIT_TEST['RATE'],
        API_AUTOMATION['TOTAL'], API_AUTOMATION['SUCCESS'], API_AUTOMATION['FAIL'], API_AUTOMATION['RATE']
    )

    mail.attach(MIMEText(content, 'html', 'utf-8'))

    for FILE in FILES:
        attachment = MIMEApplication(open(FILE, 'rb').read())
        attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(FILE))
        mail.attach(attachment)

    retry = 3
    while True:
        if retry <= 0:
            print(u'发送邮件重试已达3次，不再重试')
            break
        try:
            smtp = smtplib.SMTP(host=HOST, port=PORT)
            smtp.login(user=FROM, password=PASSWORD)
            smtp.sendmail(from_addr=FROM, to_addrs=to, msg=mail.as_string())
            print(u'发送邮件成功')
            break
        except:
            print(u'发送邮件失败')
            traceback.print_exc()
            retry -= 1
            time.sleep(5)
    smtp.quit()


if __name__ == '__main__':
    send_mail()