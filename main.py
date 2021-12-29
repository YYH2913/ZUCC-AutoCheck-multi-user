# -*- coding: utf-8 -*-
import json
import datetime
import  pandas  as pd
import requests
'''设置
'''
table = pd.read_excel('data.xls')

users=table.iloc[:,0]
pw=table.iloc[:,1]
LOCATION=table.iloc[:,2]
AUTO_POSITION=table.iloc[:,3]
SCKEY=table.iloc[:,4]
Vaccination_status=table.iloc[:,5]

def sign(school_id, password,vaccination_status, location='校内 校内 校内', auto_position='浙江省 杭州市'):
    # 获取 JSESSIONID
    #school_id = school_id.strip()
    #password = password.strip()
    #location = location.strip()
    for retryCnt in range(3):
        try:
            url = 'http://ca.zucc.edu.cn/cas/login'
            params = {'service': 'http://yqdj.zucc.edu.cn/feiyan_api/h5/html/daka/daka.html'}
            r = requests.get(url, params, timeout=30)
            cookies = r.cookies.get_dict()
            data = {
                'authType': '0',
                'username': school_id,
                'password': password,
                'lt': '',
                'execution': 'e1s1',
                '_eventId': 'submit',
                'submit': '',
                'randomStr': ''
            }
            url = 'http://ca.zucc.edu.cn/cas/login;jsessionid=' + cookies['JSESSIONID']
            r = requests.post(url, data=data, params=params, cookies=cookies, allow_redirects=False, timeout=30)
            url = r.headers['Location']
            r = requests.get(url, allow_redirects=False, timeout=30)
            cookies = r.cookies.get_dict()
            break
        except Exception as e:
            print(e.__class__.__name__, end='\t')
            if retryCnt < 2:
                print("JSESSIONID 获取失败，正在重试")
            else:
                return "无法获取 JSESSIONID，请检查账号和密码"


    for retryCnt in range(3):
        try:
            # 获取问卷
            url = 'http://yqdj.zucc.edu.cn/feiyan_api/examen/examenSchemeController/findExamenSchemeById.do'
            r = requests.post(url, cookies=cookies, data={'esId': 2}, timeout=30)
            questions = json.loads(r.json()['data']['examen']['scheme'])['questions']

            # 填写表单并提交
            with open("./form.json", "r", encoding='utf-8') as f:
                form = json.load(f)
                if form['questions'] != questions:
                    return "打卡表单已更新，当前版本不可用"

                answer = form['answer']
                answer["填报日期(Date)"] = str(
                    datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=8))).date())
                answer["自动定位(Automatic location)"] = auto_position
                answer["目前所在地"] = location
                answer["疫苗接种情况?(Vaccination status?)"] = vaccination_status
                data = json.dumps({"examenSchemeId": 2, "examenTitle": "师生报平安", "answer": answer})
                headers = {'Content-Type': 'application/json'}
                url = "http://yqdj.zucc.edu.cn/feiyan_api/examen/examenAnswerController/commitAnswer.do"
                r = requests.post(url, cookies=cookies, data=data, headers=headers, timeout=30)
                res = r.json()
                if res['code'] == 1000:
                    return '打卡成功'
                elif res['code'] == 14801:
                    return '今日已打卡'
                else:
                    return res['message']

        except Exception as e:
            print(e.__class__.__name__, end='\t')
            if retryCnt < 2:
                print("打卡失败，正在重试")
            else:
                return '打卡失败'


def wechatNotice(SCKey, message,note):
    print(message)
    url = 'https://sctapi.ftqq.com/{0}.send'.format(SCKey)
    print(url)
    data = {
        'title': message,
        'desp': note,
    }
    try:
        r = requests.post(url, data=data)
        if r.json()["data"]["error"] == 'SUCCESS':
            print("微信通知成功")
        else:
            print("微信通知失败")
    except Exception as e:
        print(e.__class__, "推送服务配置错误")


if __name__ == '__main__':
    a=len(users)
    fail="打卡失败:\n"
    succeed="\n打卡成功:\n"
    done="\n今日已打卡:\n" 
    for i in range(0,a):
        msg = sign(users[i], pw[i],Vaccination_status[i], LOCATION[i], AUTO_POSITION[i])
        print(msg)
        if msg=='打卡成功':
            succeed=succeed+str(users[i])+str(',')
        elif msg=='今日已打卡':
            done=done+str(users[i])+str(',')
        elif (msg=='打卡失败') or msg=='无法获取 JSESSIONID，请检查账号和密码':
            fail=fail+str(users[i])+str(',')
    b=len(SCKEY)
    note=succeed+fail+done
    for i in range(0,b):
        if SCKEY[i]!= '':
            wechatNotice(SCKEY[i], msg, note)
