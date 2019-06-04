#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import codecs
import csv
import os
import re
import requests
import sys
import traceback
import importlib

from datetime import datetime
from datetime import timedelta
from lxml import etree
from tqdm import tqdm


class Weibo:
    cookie = {"Cookie": "SCF=AvPT_wtMGGnRt6kL0U2aFYBKAaX3dJ4WUY3puCdharMpz6p_yYNyKL3fnwZXWLYOGr5XrfGxKqmrtmPnkLs90Sk.; MLOGIN=1; _T_WM=16227824449; XSRF-TOKEN=04bb02; WEIBOCN_FROM=1110006030; M_WEIBOCN_PARAMS=uicode%3D20000174; SUB=_2A25x6lZmDeRhGeVM61YQ9CbEzDiIHXVTFXourDV6PUJbkdAKLWGnkW1NTMajxphAhUSJm7MOBGgPbhV6CNj0STHD; SUHB=0WGc3APguUMWpO; SSOLoginState=1559111222"}  # 将your cookie替换成自己的cookie

    def __init__(self, user_id, filter=0):
        """Weibo类初始化"""
        self.user_id = user_id  # 用户id，即需要我们输入的数字，如昵称为“Dear-迪丽热巴”的id为1669879400
        self.filter = filter  # 取值范围为0、1，程序默认值为0，代表要爬取用户的全部微博，1代表只爬取用户的原创微博
        self.username = ''  # 用户名，如“Dear-迪丽热巴”
        self.weibo_num = 0  # 用户全部微博数
        self.weibo_num2 = 0  # 爬取到的微博数
        self.following = 0  # 用户关注数
        self.followers = 0  # 用户粉丝数
        self.weibo_content = []  # 微博内容
        self.weibo_place = []  # 微博位置
        self.publish_time = []  # 微博发布时间
        self.up_num = []  # 微博对应的点赞数
        self.retweet_num = []  # 微博对应的转发数
        self.comment_num = []  # 微博对应的评论数
        self.publish_tool = []  # 微博发布工具

    def deal_html(self, url):
        """处理html"""
        try:
            html = requests.get(url, cookies=self.cookie).content
            selector = etree.HTML(html)
            return selector
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def deal_garbled(self, info):
        """处理乱码"""
        try:
            info = info.xpath(
                "string(.)").replace(u"\u200b", "").encode(sys.stdout.encoding, "ignore").decode(
                sys.stdout.encoding)
            return info
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_username(self):
        """获取用户昵称"""
        try:
            url = "https://weibo.cn/%d/info" % (self.user_id)
            selector = self.deal_html(url)
            username = selector.xpath("//title/text()")[0]
            self.username = username[:-3]
            print(u"用户名: " + self.username)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_user_info(self):
        """获取用户微博数、关注数、粉丝数"""
        try:
            url = "https://weibo.cn/u/%d" % (self.user_id)
            selector = self.deal_html(url)
            weibo_footer = selector.xpath("//div[@class='tip2']/*/text()")

            # 微博数
            self.weibo_num = int(weibo_footer[0][3:-1])
            print(u"微博数: " + str(self.weibo_num))

            # 关注数
            self.following = int(weibo_footer[1][3:-1])
            print(u"关注数: " + str(self.following))

            # 粉丝数
            self.followers = int(weibo_footer[2][3:-1])
            print(u"粉丝数: " + str(self.followers))
            print(
                "===========================================================================")
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_long_weibo(self, weibo_link):
        """获取长原创微博"""
        try:
            selector = self.deal_html(weibo_link)
            info = selector.xpath("//div[@class='c']")[1]
            wb_content = self.deal_garbled(info)
            wb_time = info.xpath("//span[@class='ct']/text()")[0]
            wb_content = wb_content[wb_content.find(
                ":") + 1:wb_content.rfind(wb_time)]
            return wb_content
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_original_weibo(self, info):
        """获取原创微博"""
        try:
            weibo_content = self.deal_garbled(info)
            weibo_content = weibo_content[:weibo_content.rfind(u"赞")]
            a_text = info.xpath("div//a/text()")
            if u"全文" in a_text:
                weibo_id = info.xpath("@id")[0][2:]
                weibo_link = "https://weibo.cn/comment/" + weibo_id
                wb_content = self.get_long_weibo(weibo_link)
                if wb_content:
                    weibo_content = wb_content
            return weibo_content
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_long_retweet(self, weibo_link):
        """获取长转发微博"""
        try:
            wb_content = self.get_long_weibo(weibo_link)
            wb_content = wb_content[:wb_content.rfind(u"原文转发")]
            return wb_content
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_retweet(self, info):
        """获取转发微博"""
        try:
            original_user = info.xpath("div/span[@class='cmt']/a/text()")
            if not original_user:
                wb_content = u"转发微博已被删除"
                return wb_content
            else:
                original_user = original_user[0]
            wb_content = self.deal_garbled(info)
            wb_content = wb_content[wb_content.find(
                ":") + 1:wb_content.rfind(u"赞")]
            wb_content = wb_content[:wb_content.rfind(u"赞")]
            a_text = info.xpath("div//a/text()")
            if u"全文" in a_text:
                weibo_id = info.xpath("@id")[0][2:]
                weibo_link = "https://weibo.cn/comment/" + weibo_id
                wb_content = self.get_long_retweet(weibo_link)
                if wb_content:
                    weibo_content = wb_content
            retweet_reason = self.deal_garbled(info.xpath("div")[-1])
            retweet_reason = retweet_reason[:retweet_reason.rindex(u"赞")]
            wb_content = (retweet_reason + "\n" + u"原始用户: " +
                          original_user + "\n" + u"转发内容: " + wb_content)
            return wb_content
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_weibo_content(self, info):
        """获取微博内容"""
        try:
            is_retweet = info.xpath("div/span[@class='cmt']")
            if is_retweet:
                weibo_content = self.get_retweet(info)
            else:
                weibo_content = self.get_original_weibo(info)
            self.weibo_content.append(weibo_content)
            print(weibo_content)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_weibo_place(self, info):
        """获取微博发布位置"""
        try:
            div_first = info.xpath("div")[0]
            a_list = div_first.xpath("a")
            weibo_place = u"无"
            for a in a_list:
                if ("place.weibo.com" in a.xpath("@href")[0] and
                        a.xpath("text()")[0] == u"显示地图"):
                    weibo_a = div_first.xpath("span[@class='ctt']/a")
                    if len(weibo_a) >= 1:
                        weibo_place = weibo_a[-1]
                        if u"的秒拍视频" in div_first.xpath("span[@class='ctt']/a/text()")[-1]:
                            if len(weibo_a) >= 2:
                                weibo_place = weibo_a[-2]
                            else:
                                weibo_place = u"无"
                        weibo_place = self.deal_garbled(weibo_place)
                        break
            self.weibo_place.append(weibo_place)
            print(u"微博位置: " + weibo_place)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_publish_time(self, info):
        """获取微博发布时间"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = self.deal_garbled(str_time[0])
            publish_time = str_time.split(u'来自')[0]
            if u"刚刚" in publish_time:
                publish_time = datetime.now().strftime(
                    '%Y-%m-%d %H:%M')
            elif u"分钟" in publish_time:
                minute = publish_time[:publish_time.find(u"分钟")]
                minute = timedelta(minutes=int(minute))
                publish_time = (datetime.now() - minute).strftime(
                    "%Y-%m-%d %H:%M")
            elif u"今天" in publish_time:
                today = datetime.now().strftime("%Y-%m-%d")
                time = publish_time[3:]
                publish_time = today + " " + time
            elif u"月" in publish_time:
                year = datetime.now().strftime("%Y")
                month = publish_time[0:2]
                day = publish_time[3:5]
                time = publish_time[7:12]
                publish_time = (year + "-" + month + "-" + day + " " + time)
            else:
                publish_time = publish_time[:16]
            self.publish_time.append(publish_time)
            print(u"微博发布时间: " + publish_time)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_publish_tool(self, info):
        """获取微博发布工具"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = self.deal_garbled(str_time[0])
            if len(str_time.split(u'来自')) > 1:
                publish_tool = str_time.split(u'来自')[1]
            else:
                publish_tool = u"无"
            self.publish_tool.append(publish_tool)
            print(u"微博发布工具: " + publish_tool)
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_weibo_info(self):
        """获取用户微博信息"""
        try:
            url = "https://weibo.cn/u/%d?page=1" % (self.user_id)
            selector = self.deal_html(url)
            if selector.xpath("//input[@name='mp']") == []:
                page_num = 1
            else:
                page_num = (int)(selector.xpath(
                    "//input[@name='mp']")[0].attrib["value"])
                if page_num > 10:
                    page_num = 10
            pattern = r"\d+\.?\d*"
            for page in tqdm(range(1, page_num + 1), desc=u"进度"):
                url2 = "https://weibo.cn/u/%d?page=%d" % (self.user_id, page)
                selector2 = self.deal_html(url2)
                info = selector2.xpath("//div[@class='c']")
                is_empty = info[0].xpath("div/span[@class='ctt']")
                if is_empty:
                    for i in range(0, len(info) - 2):
                        is_retweet = info[i].xpath("div/span[@class='cmt']")
                        if (not self.filter) or (not is_retweet):

                            # 微博内容
                            self.get_weibo_content(info[i])

                            # 微博位置
                            self.get_weibo_place(info[i])

                            # 微博发布时间
                            self.get_publish_time(info[i])

                            # 微博发布工具
                            self.get_publish_tool(info[i])

                            str_footer = info[i].xpath("div")[-1]
                            str_footer = self.deal_garbled(str_footer)
                            str_footer = str_footer[str_footer.rfind(u'赞'):]
                            guid = re.findall(pattern, str_footer, re.M)

                            # 点赞数
                            up_num = int(guid[0])
                            self.up_num.append(up_num)
                            print(u"点赞数: " + str(up_num))

                            # 转发数
                            retweet_num = int(guid[1])
                            self.retweet_num.append(retweet_num)
                            print(u"转发数: " + str(retweet_num))

                            # 评论数
                            comment_num = int(guid[2])
                            self.comment_num.append(comment_num)
                            print(u"评论数: " + str(comment_num))

                            self.weibo_num2 += 1
                            print(
                                "===========================================================================")

            if not self.filter:
                print(u"共" + str(self.weibo_num2) + u"条微博")
            else:
                print(u"共" + str(self.weibo_num) + u"条微博，其中" +
                      str(self.weibo_num2) + u"条为原创微博"
                      )
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def get_filepath(self, type):
        """获取结果文件路径"""
        try:
            file_dir = os.path.split(os.path.realpath(__file__))[
                0] + os.sep + "weibo"
            if not os.path.isdir(file_dir):
                os.mkdir(file_dir)
            file_path = file_dir + os.sep + "%d" % self.user_id + "." + type
            return file_path
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def write_txt(self):
        """将爬取的信息写入txt文件"""
        try:
            if self.filter:
                result_header = u"\n\n原创微博内容: \n"
            else:
                result_header = u"\n\n微博内容: \n"
            temp_result = []
            temp_result.append(u"用户信息\n用户昵称：" + self.username +
                               u"\n用户id: " + str(self.user_id) +
                               u"\n微博数: " + str(self.weibo_num) +
                               u"\n关注数: " + str(self.following) +
                               u"\n粉丝数: " + str(self.followers) +
                               result_header
                               )
            for i in range(1, self.weibo_num2 + 1):
                temp_result.append(str(i) + ":" + self.weibo_content[i - 1] + "\n" +
                                   u"微博位置: " + self.weibo_place[i - 1] + "\n" +
                                   u"发布时间: " + self.publish_time[i - 1] + "\n" +
                                   u"点赞数: " + str(self.up_num[i - 1]) +
                                   u"   转发数: " + str(self.retweet_num[i - 1]) +
                                   u"   评论数: " + str(self.comment_num[i - 1]) + "\n" +
                                   u"发布工具: " +
                                   self.publish_tool[i - 1] + "\n\n"
                                   )
            result = ''.join(temp_result)
            with open(self.get_filepath("txt"), "wb") as f:
                f.write(result.encode(sys.stdout.encoding))
            print(u"微博写入txt文件完毕，保存路径:")
            print(self.get_filepath("txt"))
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def write_csv(self):
        """将爬取的信息写入csv文件"""
        try:
            result_headers = ["微博正文", "发布位置",
                              "发布时间", "发布工具", "点赞数", "转发数", "评论数"]
            result_data = zip(self.weibo_content, self.weibo_place, self.publish_time,
                              self.publish_tool, self.up_num, self.retweet_num, self.comment_num)
            if sys.version < '3':   # python2.x
                importlib.reload(sys)
                sys.setdefaultencoding('utf-8')
                with open(self.get_filepath("csv"), "wb") as f:
                    f.write(codecs.BOM_UTF8)
                    writer = csv.writer(f)
                    writer.writerows([result_headers])
                    writer.writerows(result_data)
            else:   # python3.x
                with open(self.get_filepath("csv"), "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerows([result_headers])
                    writer.writerows(result_data)
            print(u"微博写入csv文件完毕，保存路径:")
            print(self.get_filepath("csv"))
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()

    def start(self):
        """运行爬虫"""
        try:
            self.get_username()
            self.get_user_info()
            self.get_weibo_info()
            self.write_txt()
            self.write_csv()
            print(u"信息抓取完毕")
            print(
                "===========================================================================")
        except Exception as e:
            print("Error: ", e)
            traceback.print_exc()


def main():
    try:
        # 使用实例,输入一个用户id，所有信息都会存储在wb实例中
        user_id = 1638782947  # 可以改成任意合法的用户id（爬虫的微博id除外）
        filter = 1  # 值为0表示爬取全部微博（原创微博+转发微博），值为1表示只爬取原创微博
        wb = Weibo(user_id, filter)  # 调用Weibo类，创建微博实例wb
        wb.start()  # 爬取微博信息
        print(u"用户名: " + wb.username)
        print(u"全部微博数: " + str(wb.weibo_num))
        print(u"关注数: " + str(wb.following))
        print(u"粉丝数: " + str(wb.followers))
        if wb.weibo_content:
            print(u"最新/置顶 微博为: " + wb.weibo_content[0])
            print(u"最新/置顶 微博位置: " + wb.weibo_place[0])
            print(u"最新/置顶 微博发布时间: " + wb.publish_time[0])
            print(u"最新/置顶 微博获得赞数: " + str(wb.up_num[0]))
            print(u"最新/置顶 微博获得转发数: " + str(wb.retweet_num[0]))
            print(u"最新/置顶 微博获得评论数: " + str(wb.comment_num[0]))
            print(u"最新/置顶 微博发布工具: " + wb.publish_tool[0])
    except Exception as e:
        print("Error: ", e)
        traceback.print_exc()


if __name__ == "__main__":
    main()
