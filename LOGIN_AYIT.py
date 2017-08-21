# _*_encoding:utf-8 _*_
"""
@Software: PyCharm
@Python: 3.X   X==5
@抓包：fiddler
@Time: 2017.8.15
@Contact:520@skyne.cn
@Author: SKYNE
@友情提醒：各教务网大同小异，最重要的是模拟登录思想，
只要我们能完全模仿出正常浏览器对教务网服务器的请求方式，
所携带的请求头，cookies，那么服务器就会返回给我们想要的信息。
@杂谈: 本来是准备自己实现验证码的识别的，在参阅了好多文章后。
在GitHub上找到了一个相对较好的。自己能看得懂，自己修改后测试。
结果，相当惨，识别率只有30%左右。不得以，用了付费API。不得不说，
识别率真是没得说。
"""
"""
###下面是测试过的各基本的URL地址以及请求方法###

home_page = http://jwgl.ayit.edu.cn/        method=GET    # 教务网主页
login_url = http://jwgl.ayit.edu.cn/_data/login.aspx，   method=POST    # 教务网post登陆地址
Vcode_url = http://jwgl.ayit.edu.cn/sys/ValidateCode.aspx，   method=GET   # 获取验证码验证码地址
Basic_info_url = http://jwgl.ayit.edu.cn/xsxj/Stu_MyInfo_RPT.aspx,  method=GET  # 基本信息获取地址
name_code_url = http://jwgl.ayit.edu.cn/xscj/private/list_xhxm.aspx, method=GET  # 姓名，学号获取地址
your_image = http://jwgl.ayit.edu.cn/_photo/student/20150000331008nBNWLMbf.JPG,  method=GET  # 顾名思义
score_url = http://jwgl.ayit.edu.cn/xscj/Stu_cjfb_rpt.aspx,      method=POST  # 成绩信息获取地址，需要post提交数据
###http://jwgl.ayit.edu.cn/xscj/Stu_MyScore_rpt.aspx###该地址也是成绩地址，但返回的是图片，不是文本。难以提取其中信息。
"""
"""下述是本脚本所需要的库"""
import requests
import hashlib
import re
import base64
import time
from lxml import html
from urllib.parse import urljoin

"""下面的类主要是构建Header请求头和POST数据以及加密密码(PWD)与验证码(Vcode)，叫什么名字呢，就叫HPPV吧"""


class hppv:
    def __init__(self, Basic_info):
        self.school_code = Basic_info[ "school_code" ]
        self.user_id = Basic_info[ "user_id" ]
        self.pwd = Basic_info[ "pwd" ]
        self.home_url = Basic_info[ "home_url" ]
        self.login_url = urljoin ( self.home_url, '_data/login.aspx' )
        self.vcode_url = urljoin ( self.home_url, '/sys/ValidateCode.aspx' )
        self.ses = requests.session ()

    def Header(self, If):
        Basic_Header = {
            "Connection": "keep-alive",
            "Cache-Control": "max-age=0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
        }
        ### Basic_Header["Host"] = self.home_url  添加该行后，会返回400错误。
        Basic_Header[ "Origin" ] = self.home_url
        if If == 'home':
            Basic_Header[ "Referer" ] = self.home_url
            return Basic_Header
        elif If == 'login':
            Basic_Header[ "Referer" ] = self.login_url
            return Basic_Header

    def Post_data(self):
        post_data = {
            "Sel_Type": "STU",
            "typeName": u"学生".encode ( 'gb2312' ),
            "txt_asmcdefsddsd": "",  # 学号，暂时置空
            "dsdsdsdsdxcxdfgfg": "",  # 密码，暂时置空
            "fgfggfdgtyuuyyuuckjg": "",  # 验证码 暂时置空
            "txt_pewerwedsdfsdff": "",  # 未发现实际意义
            "txt_sdertfgsadscxcadsads": "",  # 未发现实际意义
            "pcInfo": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36undefined5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36 SN:NULL",
        }
        # re = self.ses.get(url=self.home_url,headers=self.Header(If='home'))         ###直接访问login_url会发生错误，故先访问home_page
        response = self.ses.get ( url=self.login_url, headers=self.Header ( If='login' ) )  ###此处注意，url位于login_url
        if response.status_code == 200:
            selector = html.fromstring ( response.text )
            post_data[ "__VIEWSTATE" ] = selector.xpath ( "//*[@id='Logon']/input[1]/@value" )[ 0 ]
            post_data[ "__VIEWSTATEGENERATOR" ] = selector.xpath ( "//*[@id='Logon']/input[2]/@value" )[ 0 ]
            post_data[ "txt_asmcdefsddsd" ] = self.user_id
            post_data[ "dsdsdsdsdxcxdfgfg" ] = self.Pwd_encrypt ()
            post_data[ "fgfggfdgtyuuyyuuckjg" ] = self.Vcode_encrypt ()
            return post_data
        else:
            print ( "Sorry A {} Error Occurred\n!".format ( response.status_code ) )

    def Md5_sum(self, obj):
        """这个是根据加密机制，反过来推出的，首先计算密码的16进制的哈希值，取前30位，并大写。然后再与学号，学校代码相加，
        再重复上一步骤，最终获得加密后的密码。验证码则不需要加学号。"""
        md5 = hashlib.md5 ( obj.encode ( 'gb2312' ) ).hexdigest ()[ 0:30 ].upper ()
        return md5

    def Pwd_encrypt(self):
        pwd = self.Md5_sum ( self.user_id + self.Md5_sum ( self.pwd ) + self.school_code )
        return pwd

    def Get_vcode(self):
        self.ses.get ( url=self.home_url, headers=self.Header ( If='home' ) )
        self.ses.get ( url=self.login_url, headers=self.Header ( If='login' ) )
        response = self.ses.get ( url=self.vcode_url, headers=self.Header ( If='login' ) )
        Vcode_Str = Vcode_dome ( Vcode=response ).Dome ()
        return Vcode_Str
        ###with open('vcode.jpg','wb') as f:
        ###f.write(response.content)

    def Vcode_encrypt(self):
        vcode = self.Get_vcode ()
        try:
            vcode_encrypt = self.Md5_sum ( self.Md5_sum ( vcode.upper () ) + self.school_code )
            return vcode_encrypt
        except AttributeError as e:
            print("Sorry, Verification Code Failed! Try Again! Please Wait A Moment!\n")
            self.Try_login()



    def Get_All(self):
        res_name = self.ses.get ( url=urljoin ( self.home_url, 'xscj/private/list_xhxm.aspx' ),
                                  headers=self.Header ( If='login' ) )
        res_score = self.ses.post ( url=urljoin ( self.home_url, 'xscj/Stu_cjfb_rpt.aspx' ),
                                    data=self.Postdata_score (), headers=self.Header ( If='login' ) )
        self.Get_Basic_info ()
        with open ( 'Your_Score.docx', 'ab' ) as f:
            f.write ( res_name.content )
            f.write ( res_score.content )
            print ( "All Infomation Saved,Please Check!\n" )

    def Get_Basic_info(self):
        info_num = input ( "Do You Have Access To Your Personal Information?\nTips:YES->1 OR NO->任意键:" )
        print('\n')
        if info_num == '1':
            Basic_info = self.ses.get ( url=urljoin ( self.home_url, 'xsxj/Stu_MyInfo_RPT.aspx' ),
                                        headers=self.Header ( If='login' ) )
            if Basic_info.status_code == 200:
                with open ( 'Basic_info.docx', 'wb' ) as f:
                    f.write ( Basic_info.content )
            selector = html.fromstring ( Basic_info.text )
            photo_url = selector.xpath ( "//img/@src" )
            Your_photo = self.ses.get ( url=urljoin ( self.home_url, photo_url[ 0 ] ),
                                        headers=self.Header ( If='login' ) )
            if Your_photo.status_code == 200:
                with open ( 'Your_photo.jpg', 'wb' ) as f:
                    f.write ( Your_photo.content )

    def Postdata_score(self):
        postdata_score = {
            "sel_xq": "",  ### 学期，0代表第一学期，1代表第二学期
            "SelXNXQ": "",  ### 学期，学年。0==入学以来，1==学年，2==学期
            "sel_xn": "",  ### 年份
            "submit": "检索".encode ( 'gb2312' ),

        }
        print("""
提示：很抱歉，由于教务网回传信息格式原因，下述所有成绩信息均以docx格式存至该软件同级目录。

也是相同原因，无法在控制台输出信息。后续有时间将会逐步解决！查询成绩很鸡肋，不是本软件目标所在。

等到教务网接口开放，将提供一键抢课，一键评教，想要更多实用功能！Please Email: 520@skyen.cn!

如遇BUG，也请Email Me。该软件由Python编写，如有兴趣，可在Github查看源码！github.com/skyne0
        """)
        XNXQ = input ( u"Please Choose The Way You Want To Query\nTips: 入学以来->0，学年->1，学期->2:" )
        print('\n')
        if XNXQ == '0':
            postdata_score[ "SelXNXQ" ] = '0'
            postdata_score.pop ( "sel_xq" )
            postdata_score.pop ( "SelXNXQ" )
            print("Just A Moment! Please!\n")
            return postdata_score
        elif XNXQ == '1':
            Year = int ( input ( "Please Enter The Year You Need Query:" ) )
            print('\n')
            sys_year = int ( time.strftime ( "%Y" ) )
            if Year <= sys_year and Year >= sys_year - 4:
                postdata_score[ "sel_xn" ] = str ( Year )
                postdata_score[ "SelXNXQ" ] = '1'
                postdata_score.pop ( "sel_xq" )
                print ( "Just A Moment! Please!\n" )
                return postdata_score
        elif XNXQ == '2':
            Year = int ( input ( "Please Enter The Year You Need Query:" ) )
            print('\n')
            sys_year = int ( time.strftime ( "%Y" ) )
            if Year <= sys_year and Year >= sys_year - 4:
                Term = input ( "Please Enter The Year You Need Query:" )
                print('\n')
                if Term in [ '1', '2' ]:
                    Term = str ( int ( Term ) - 1 )
                    postdata_score[ "sel_xn" ] = str ( Year )
                    postdata_score[ "sel_xq" ] = Term
                    postdata_score[ "SelXNXQ" ] = '2'
                    print ( "Just A Moment! Please!\n" )
                    return postdata_score
        else:
            print ( "Sorry Enter Error,Please Enter Again!\n" )
            self.Postdata_score ()

    def Try_login(self):
        response = self.ses.post ( url=self.login_url, data=self.Post_data (), headers=self.Header ( If='login' ) )
        if re.search ( u"正在加载权限", response.text ):
            print ( u"Login Successful,Please wait a monent\n" )
            self.Get_All ()
        elif re.search ( u"帐号或密码不正确", response.text ):
            print ( u"Sorry The Account Number Or Password Is Incorrect!，Please Try Again\n" )
        elif re.search ( u"验证码错误", response.text ):
            print ( u"Sorry Vcode(验证码) Error，Please Try Again\n" )
        else:
            print ( u"Sorry Login Error\n" )

            ###API_Url: http://ali-checkcode2.showapi.com/checkcode
            ###APPCODE: 6b591d5a635e49628f9e6c9b9e3bef1e
            ###下面是开发者文档的请求示例


"""   ###下面是开发者文档中的请求示例，基于python2
    import urllib, urllib2, sys
    import ssl
    host = 'https://ali-checkcode2.showapi.com'
    path = '/checkcode'
    method = 'POST'
    appcode = '你自己的AppCode'
    querys = ''
    bodys = {}
    url = host + path

    bodys['convert_to_jpg'] = '0'
    bodys['img_base64'] = '/9j/4AAQSkZJRgABAgAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAAYADwDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD35twU7QC2OATgE1xPiTx3Jp+r6fpmg6dLrOqT273T2kciRxJACQXeY/KhDKQOSOoPJU12kTO8SNImxyoLJnO09xnvXmXiHQ/EGj+MrzxN4c0641NtVjjiu9Pa4W3KOihUkEo/g2ggpuB3EMcjAW4LXUmUZPZnUeFvGDeIHudOv9Nm0XXrYM0un3R3Ex7ioljbAEsZIxuXjPHQqTHB43hbx+/hKa1KzrFkXAfKu+wPtC44Gwk5J6jHPWuCi8SaxpnxRv8AXfFOl2+nzw+Fi0VlDP5pA+0qqq7qCNzSZ5GQFZc8g1QufEuiWXg6yvrDV0l8U297/akxNrIpmlk/1sZYYCrggNtIDCPpzVwhfoc9erySVnbr6o9O8OeMrTxnYS3eizraiCXypYr2EM+SBtOFk4ByQCepB9Kj8UeMItChGkLJFdeI7pEFpaqjxLKZH2Kd2SFwc9XBO3qMg1yHw6sbbwtrem2KPvtfEmjRXJMxDsbpBvaMBfup5chPzDnjB7VzWpJrPirxvYazZi2kOoXsr6PJJJIoMVpkgYz8queSDg7gT8gOTbir2W39f8EmVSShdfE/6/yPVPAt9d3GmNbXuqR3Wo2dzPbXybB99HIBXheCCpJwc57HNbf/AAkWjrxLqVvbv3iuX8mRfqj4YevI6c1wfwytdWnutd/tKCx+zDUbjzijOZVugUzg5xtAJwfvA55559IMDgARyYUDHzlmP57qwbVy4TqygmieuR1vw34gutQSXQvG91pR8oJJBNaxXalVJ2lQ2Cp+ZgWJJb5cn5aKKm9jptcytN+G0Jna7udc1G+kvLmK51c3kO37a8Q+RApACRAk/JhhjAyNoI7LX7CXVfDmqadAyLNdWksCM5IUMyFQTjPGTRRTUnoJwim/M4SX4Y6g/gfTNKTVbWPU9PjuFinWBipWdCJIjluhLEb9uQAMKDnO7qHh2ePxb4Ml061xpmkR3UUh8wfulaFUjHzHc3THf3ooq/aye/n+JCpRW3l+Bp2j6L4fvr+13QWLXM325zLccTPJkM3zHg5Q8DgDHrgbRcA4Ib8FJoop1YqMYyXUzozbco9n/mf/2Q=='
    bodys['typeId'] = '34'
    post_data = urllib.urlencode(bodys)
    request = urllib2.Request(url, post_data)
    request.add_header('Authorization', 'APPCODE ' + appcode)
    //根据API的要求，定义相对应的Content-Type
    request.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    response = urllib2.urlopen(request, context=ctx)
    content = response.read()
    if (content):
        print(content)
    """


class Vcode_dome:
    def __init__(self, Vcode):
        self.API_Code = "6b591d5a635e49628f9e6c9b9e3bef1e"
        self.API_Url = "http://ali-checkcode2.showapi.com/checkcode"
        self.Vcode = Vcode

    def Dome(self):
        print ( "Verification Code Is Being Identified!\n" )
        Header = {'Authorization': 'APPCODE ' + self.API_Code,
                  'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        Post_data = {"convert_to_jpg": "0", "typeId": "34"}
        Post_data[ "img_base64" ] = base64.b64encode ( self.Vcode.content )
        response = requests.post ( url=self.API_Url, data=Post_data, headers=Header )
        result = eval ( response.text )
        if result[ "showapi_res_code" ] == result[ "showapi_res_body" ][ "ret_code" ]:
            return result[ 'showapi_res_body' ][ 'Result' ]
        else:
            print ( "Sorry, Result Error Returned,Please Try Again!\n" )


def Print():
    print (
        """
                  A               Y          Y            I I I              T T T T T T T 
                 A A                Y       Y               I                      T
                A   A                 Y   Y                 I                      T
               A     A                  Y                   I                      T
              A A A A A                 Y                   I                      T
             A         A                Y                   I                      T
            A           A               Y                   I                      T
           A             A              Y                 I I I                    T


                         An Educational Network Automatic Login Program


                                                                          ----By SKYNE----
        """
    )


def run():
    Print ()
    Basic_info = {  ###以下是个人信息，学校代码可登录教务网主页，翻看网页源代码得到###
        "school_code": "11330",  ###学校代码 ###
        "user_id": "",  ###学号###
        "pwd": "",  ###密码####
        "home_url": "http://jwgl.ayit.edu.cn/"  ###教务网主页 ###
    }
    Basic_info[ "user_id" ] = input ( "Please Enter Your Student ID: " )
    print('\n')
    Basic_info[ "pwd" ] = input ( "Please Enter Your Password: " )
    print('\n')
    print ( "Logging in, Please Wait A Moment!\n" )
    login = hppv ( Basic_info )
    login.Try_login ()
    flag = input("End Of Program! Is It Running Again!\nYES->1 OR 任意键->NO:")
    print('\n')
    if flag == '1':
        run()
    else:
        print("Thank You For Using! What Questions Can You Contact SKYNE\n@Email: 520@skyne.cn\n")
        input("Press Any Key To Exit!")

if __name__ == '__main__':
    run ()