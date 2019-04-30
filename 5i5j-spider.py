import requests
import time
import scrapy
from bs4 import BeautifulSoup
import pymysql
import datetime

def getYesterday():
    today=datetime.date.today()
    oneday=datetime.timedelta(days=1)
    yesterday=today-oneday
    return yesterday

def getToday():
    today=datetime.date.today()
    return today

class Spider:
    def __init__(self):
        self.header = {'accept-encoding': 'gzip, deflate, br',
                       'accept-language': 'zh-CN,zh;q=0.9',
                       'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                     'Chrome/67.0.3396.62 Safari/537.36',
                       'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                       'referer': 'https://bj.5i5j.com/zufang/',
                       'cookie': 'PHPSESSID=qnje456clu59eun22uh3g46sn0; yfx_c_g_u_id_10000001=_ck19012013553611905117267240053; _Jo0OQK=3B1FEEC04A9D3D5BD834889DA7062943EE03461FD4980E5AE1D41833FFAAD933D9FD6359682AE96BBAAE2EBD2197322A173470E7CF5FFFCA8E36822532992A286BDC57212F12283777C840763663251ADEB840763663251ADEBD1D1BDD8DB1AEE352350674422DE2517GJ1Z1fQ==; yfx_f_l_v_t_10000001=f_t_1547963736187__r_t_1547963736187__v_t_1547981919500__r_c_0; domain=bj'}
        self.url = 'https://bj.5i5j.com/zufang/'

    def __get_html(self, pageNumber):  # 返回html
        res = requests.get(self.url+ 'n' + str(pageNumber), headers=self.header, verify=False).text
        return res

    # 样例：'https://image16.5i5j.com/erp/house/4232/42328646/shinei/caokgjhbff5f2b01.jpg_P7.jpg'
    def find_img(self, soup):
        list_img = []
        for link in soup.find_all('img', class_='lazy'):
            list_img.append(link.get('src') or link.get('data-src'))
        #print(list_img)
        return list_img

    # 样例：'42328646', '方庄 芳城园新上三居 空房短租半年有钥匙随时看'
    def find_title(self, soup):
        list_title = []
        list_temp = []
        for link in soup.find_all('h3', class_='listTit'):
            str_temp = str(link.a.get('href'))  #   '/zufang/42256207.html'
            list_temp.append(str_temp[str_temp.find('/zufang/')+len('/zufang/'):str_temp.rfind('.'):1]) #    42256207
            list_temp.append(link.a.string)     #   '望京西园三区超便宜的一居室这样的好房 不多错过后悔！！！'
            list_temp1 = list_temp.copy()  # 样例  ['42256207', '望京西园三区超便宜的一居室这样的好房 不多错过后悔！！！']
            list_temp.clear()
            list_title.append(list_temp1)
        #print(list_title)
        return list_title

    # 样例：[['3室1厅', '78平米', '西南', '低楼层/27层', '简装'], '方庄,芳城园一区', ['0人关注', '近30天带看1次', '2019-01-16发布'], '3800元/月', '出租方式：整租']
    def find_content(self, soup):
        list_content = []
        list_temp = []
        for link in soup.find_all('div', class_='listX'):
            for link2 in link.find_all('i', class_='i_01'):
                str1 = str(link2.next_element)
                list1 = str1.replace(' ', '').split('·')
                list_temp.append(list1)
                list_temp.append(str(link2.find_next().a.string).replace(' ',','))
                str2 = str(link2.find_next().find_next_sibling().next_element.next_element)
                list2 = str2.replace(' ','').split('·')
                if '今天发布' in list2[2]:
                    list2[2] = str(getToday())+'发布'
                elif '昨天发布' in list2[2]:
                    list2[2] = str(getYesterday())+'发布'
                str2 = ','.join(list2)
                list_temp.append(str2)
                list_temp.append(str(link2.find_next(class_='redC').text).strip().replace('\n\t\t\t\t\t\t\t\t\t', ''))
                list_temp.append(link2.find_next(class_='redC').find_next_sibling().string)
                list_temp1 = list_temp.copy()
                list_temp.clear()
                list_content.append(list_temp1)
        #print(list_content)
        return list_content

    # 样例：'近地铁,随时看,可短租,集中供暖'
    def find_tag(self, soup):
        list_tag = []
        str_temp = ''
        for link in soup.find_all('div', class_='listTag'):
            for link2 in link.find_all('span'):
                if str_temp == '':
                    str_temp = link2.string
                else:
                    str_temp = str_temp + ',' + link2.string
            list_tag.append(str_temp)
            str_temp = ''
        #print(list_tag)
        return list_tag

    def htmlTolist(self, html_page):
        dict1 = {}
        datas = []
        soup = BeautifulSoup(html_page, 'lxml')
        if 'window.location.href=' in soup.script.string:   #如果返回的页面是403 Forbidden 会报错，因为此页面没有script，soup.script.string报错源
            str = soup.script.string
            temp_url = str[str.find('https'):str.rfind('\''):1]
            temp_html = requests.get(temp_url, headers=self.header, verify=False).text
            soup = BeautifulSoup(temp_html, 'lxml')
        list_img = self.find_img(soup)
        list_title = self.find_title(soup)
        list_content = self.find_content(soup)
        list_tag = self.find_tag(soup)
        if len(list_img) == 30:
            rangeNum = 30
        else:
            rangeNum = len(list_img)
        for i in range(0, rangeNum):
            dict1['img_url'] = list_img[i]
            dict1['room_id'] = list_title[i][0]
            dict1['title'] = list_title[i][1]
            dict1['house_type'] = list_content[i][0][0]
            dict1['acreage'] = list_content[i][0][1]
            dict1['chaoxiang'] = list_content[i][0][2]
            dict1['floor'] = list_content[i][0][3]
            dict1['degree'] = list_content[i][0][4]
            dict1['area'] = list_content[i][1]
            dict1['recent_browse'] = list_content[i][2]
            dict1['rent'] = list_content[i][3]
            dict1['lend_m'] = list_content[i][4]
            dict1['tag'] = list_tag[i]
            dict_temp = dict1.copy()
            datas.append(dict_temp)
        #print(datas)
        return datas

    def writeTosql(self, data):
        '''写入数据库'''
        woaiwojiaRoom = Operate_SQL()
        tableName = 'bj'
        #flag==1  表示表是否已经创建了 flag==0  表示表还没有创建,需要创建表
        flag = woaiwojiaRoom.checkTableIsExists(tableName)
        if flag == 0:
            woaiwojiaRoom.createTable(tableName)
            woaiwojiaRoom.add_data(data)
        elif flag == 1:
            woaiwojiaRoom.add_data(data)

    # print('   该页获取完成')

    def run(self):
        for i in range(1, 1317):
            print('正在打印第 %d 页' % (i))
            html = self.__get_html(i)
            datas = self.htmlTolist(html)
            for data in datas:
                self.writeTosql(data)
            time.sleep(1)



class Operate_SQL():
    def __get_conn(self):
        '''连接数据库'''
        try:
            # 我用的的本地数据库，所以host是127.0.0.1
            self.conn = pymysql.connect(host='localhost', user='root', passwd='123456', port=3306, db='tla',
                                        charset='utf8mb4')
        except Exception as e:
            print(e, '数据库连接失败')

    def __close_conn(self):
        '''关闭数据库连接'''
        try:
            if self.conn:
                self.conn.close()
        except pymysql.Error as e:
            print(e, '关闭数据库失败')

    def checkTableIsExists(self, tableName):  # 检查表在数据库中是否存在
        sql = "SELECT * from `%s`" % tableName
        try:
            self.__get_conn()
            cursor = self.conn.cursor()
            cursor.execute(sql)
        except pymysql.Error as e:
            print(e, '该表名不存在，需要创建表')
            return 0
        else:
            return 1
        finally:
            self.__close_conn()

    def createTable(self, tableName):  # 创建表
        sql = "CREATE TABLE `%s` (`img_url` varchar(150),`room_id` varchar(10),`title` varchar(40),`house_type` varchar(8),`acreage` varchar(10),`chaoxiang` varchar(5),`floor` varchar(10),`degree` varchar(5),`area` varchar(30),`recent_browse` varchar(60),`rent` varchar(20),`lend_m` varchar(15),`tag` varchar(25),PRIMARY KEY ( `room_id` ))" % tableName
        try:
            self.__get_conn()
            cursor = self.conn.cursor()
            cursor.execute(sql)
            return 1
        except pymysql.Error as e:
            print(e, '创建表失败')
            return 0
        finally:
            self.__close_conn()

    def add_data(self, data):
        '''增加一条数据到数据库'''
        sql = "INSERT INTO bj VALUE(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        try:
            self.__get_conn()
            cursor = self.conn.cursor()
            cursor.execute(sql, [data['img_url'],data['room_id'],data['title'],data['house_type'],data['acreage'],data['chaoxiang'],data['floor'],data['degree'],data['area'],data['recent_browse'],data['rent'],data['lend_m'],data['tag']])
            self.conn.commit()
            return 1
        except AttributeError as e:
            print(e, '添加数据失败')
            # 添加失败就倒回数据
            self.conn.rollback()
            return 0
        except pymysql.DataError as e:
            print(e)
            self.conn.rollback()
            return 0
        except pymysql.err.IntegrityError as e:
            print(e,'主键冲突')
            self.conn.rollback()
        finally:
            if cursor:
                cursor.close()
            self.__close_conn()


def main():
    spider = Spider()
    spider.run()

if __name__ == '__main__':
    main()
