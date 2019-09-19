import json
import requests
import re
import time
import hashlib
import random
from requests.exceptions import RequestException
import logging
from bs4 import BeautifulSoup
import urllib
import os
import traceback
from heybox_static import *

'''
Python3实现的小黑盒客户端

本程序遵循GPLv3协议
开源地址:https://github.com/chr233/xhh_auto/

作者:Chr_
电邮:chr@chrxw.com
'''
#脚本版本
SCRIPT_VERSION = 'v0.3'

#小黑盒版本号,会自动设置为最新版
HEYBOX_VERSION = '1.2.80'

#调试模式开启
env_dist = os.environ

if env_dist.get('MODE') == 'DEBUG':
    LEVEL = logging.DEBUG
    DEBUG = True
else:
    LEVEL = logging.INFO
    Debug = False

#LOG_FORMAT =
#"[%(asctime)s][%(levelname)s][%(funcName)s][%(name)s]#%(message)s"
LOG_FORMAT = "[%(levelname)s][%(name)s]%(message)s"
logging.basicConfig(level=LEVEL,format=LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')

#Python版小黑盒客户端
class HeyboxClient():
    Session = requests.session()
    Session.headers = {}
    Session.headers = {}
    heybox_id = 0
    _headers = {}
    _cookies = {}
    _params = {}
    
    #3个参数抓包可以拿到,最后一个是标签
    def __init__(self, heybox_id:int=0,imei:str='',pkey:str='',tag:str='未指定'):
        super().__init__()
        self._headers = {
            'Referer': 'http://api.maxjia.com/',
            'User-Agent': 'Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36 ApiMaxJia/1.0',
            'Host': 'api.xiaoheihe.cn',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip'
        }
        self._cookies = {
            'pkey': pkey
        }
        self._params = {
            'heybox_id': heybox_id,
            'imei': imei,
            'os_type': 'Android',
            'os_version': '8.1.0',
            'version': HEYBOX_VERSION,
            '_time': '',
            'hkey': ''
        }
        self.heybox_id = heybox_id
        self.logger = logging.getLogger(str(tag))
        self.logger.debug(f'初始化完成{f" @ [{heybox_id}]" if heybox_id else ""}')

        #[自动]
        #def auto(self):#,viewcount,likecount,sharecount,followcount):
        #    self.get_ads_info()
        #    self.check_achieve_alert()
        #    self.sign()
        #    idlist = self.get_news_list(30)
        #    self.simu_view_news(idlist[0][0],idlist[0][1],0)
        #    self.share(idlist[0][1])

        #    self.simu_view_like_newses(idlist,10)

        #    self.auto_follow_followers(30)
        #    self.auto_like_follows(30)

    def sample_auto():
        '''
        简单的自动化执行示例
        '''
        pass

    #NT
    def batch_newslist_operate(self,idsetlist:list,operatetype:int=1,indexstart:int=1):
        '''
        批量操作文章列表
        参数:
            idsetlist:[(linkid,newsid),…]
            operatetype:操作码  操作码参见OperateType,1:浏览,2:浏览分享,3:浏览点赞,4:浏览点赞分享
            indexstart:初始索引
        成功返回:
            True
        失败返回:
            False
        '''
        if operatetype == OperateType.View:
            view,like,share = True,False,False
        elif operatetype == OperateType.ViewLike:
            view,like,share = True,True,False
        elif operatetype == OperateType.ViewShare:
            view,like,share = True,False,True
        elif operatetype == OperateType.ViewLikeShare:
            view,like,share = True,True,True
        else:
            self.logger.error(f'错误的操作码[{operatetype}],操作码参见OperateType类')
            return(False)
        if idsetlist:
            index = indexstart
            errorcount = 0
            operatecount = 0
            for idobj in idsetlist:
                try:
                    linkid,newsid = idobj
                    if view:
                        has_viedo,is_liked = self.get_news_links(linkid,newsid,index)
                        if not has_viedo:
                            self.get_news_body(newsid,index)
                        else:
                            self.get_video_title(linkid,newsid,index)
                    if like and not is_liked:
                        self.like_news(linkid,newsid,index)
                    if share:
                        self.share(newsid,index)
                    operatecount+=1
                except LikeLimitedError as e:
                    self.logger.debug(f'达到每日点赞上限,停止操作[{e}]')
                    return(False)
                except (ValueError,TypeError,ClientException) as e:
                    self.logger.debug(f'批量点赞遇到错误[{e}]')
                    errorcount+=1
                    if errorcount >= 5:
                        self.logger.error('批量点赞遇到大量错误,停止操作')
                        return(False)
                finally:
                    index+=1
            self.logger.debug(f'批量操作完成,执行了[{operatecount}]次操作')
            return(True)
        else:
            self.logger.error(f'参数错误[{idsetlist}]')
            return(False)  

    #NT
    def batch_like_followposts(self,idsetlist:list):
        '''
        批量点赞动态
        参数:
            idsetlist:[(linkid,type,已点赞?),…]
        成功返回:
            True
        失败返回:
            False
        '''
        if idsetlist:
            errorcount = 0
            operatecount = 0
            for idobj in idsetlist:
                try:
                    linkid,posttype,is_liked = idobj
                    if is_liked:
                        continue
                    self.like_follow_post(linkid,posttype)
                    operatecount+=1
                except LikeLimitedError as e:
                    self.logger.debug(f'达到每日点赞上限,停止操作[{e}]')
                    return(False)
                except (ValueError,TypeError,ClientException) as e:
                    self.logger.debug(f'批量点赞遇到错误[{e}]')
                    errorcount+=1
                    if errorcount >= 5:
                        self.logger.error('批量点赞遇到大量错误,停止操作')
                        return(False)
            self.logger.debug(f'批量操作完成,执行了[{operatecount}]次操作')
            return(True)
        else:
            self.logger.error(f'参数错误[{idsetlist}]')
            return(False)  

    #NT
    def batch_userlist_operate(self,useridlist:list,operatetype:int=1):
        '''
        批量关注/取关粉丝
        参数:
            useridlist:[用户id,……]
            operatetype:操作码,1:关注,2:取关  释义参见OperateType
        成功返回:
            True
        失败返回:
            False
        '''
        def follow_user(userid:int) -> bool:
            '''
            关注用户
            参数:
                userid:用户id
            成功返回:
                True
            '''
            if userid == self.heybox_id:
                self.logger.debug('不能粉自己哦')
                return(True)
            url = URLS.FOLLOW_USER
            headers = {
                **self._headers,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'following_id': userid,
            }
            self.__flush_params()
            resp = self.Session.post(url=url,data=data,params=self._params,headers=headers,cookies=self._cookies)
            jsondict = resp.json()
            self.__check_status(jsondict)
            self.logger.debug(f'关注用户[{userid}]成功')
            return(True)
        def unfollow_user(userid:int) -> bool:
            '''
            取关用户
            参数:
                userid:用户id
            成功返回:
                True
            '''
            if userid == self.heybox_id:
                self.logger.debug('不能取关自己哦')
                return(True)
            url = URLS.FOLLOW_USER_CANCEL
            headers = {
                **self._headers,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'following_id': userid,
            }
            self.__flush_params()
            resp = self.Session.post(url=url,data=data,params=self._params,headers=headers,cookies=self._cookies)
            jsondict = resp.json()
            self.__check_status(jsondict)
            self.logger.debug(f'取关用户[{userid}]成功')
            return(True)
        #========================================
        if operatetype == OperateType.FollowUser:
            operater = follow_user
        elif operatetype == OperateType.UnFollowUser:
            operater = unfollow_user
        else:
            self.logger.error(f'错误的操作码[{operatetype}],操作码参见OperateType类')
            return(False)
        
        if useridlist and type(useridlist) == list:
            if type(useridlist[0]) != int:
                useridlist = self.userlist_simplify(useridlist) #简化userlist
            errorcount = 0 #错误计数
            operatecount = 0 #操作计数
            for userobj in useridlist:
                try:
                    operater(userobj)
                    operatecount+=1
                except FollowLimitedError as e:
                    self.logger.error(f'达到每日关注上限，停止操作[{e}]')
                    return(False)
                except ClientException as e:
                    self.logger.debug(f'关注/取关用户出错[{e}]')
                    errorcount+=1
                    if errorcount >= 3:
                        self.logger.error(f'批量关注/取关用户遇到大量错误，停止操作')
                        return(False)                      
            self.logger.debug(f'成功关注/取关了[{operatecount}]个用户')
            return(True)
        else:
            self.logger.error(f'参数错误[{useridlist}]')
            return(False)

    #NT
    def get_news_list(self,value:int=30):
        '''
        拉取首页文章列表
        参数:
            value:要拉取的数量
        成功返回:
            newsidlist:[(linkid,newsid),……]
        '''        
        def _get_news_list(offset:int=0):
            '''     
            拉取首页文章列表
            参数:
                offset:偏移,以30为单位
            成功返回:
                newslist:[(linkid,newsid),……]
            '''
            url = URLS.GET_NEWS_LIST
            self.__flush_params()
            params = {
                'tag': -1,
                'offset': offset,
                'limit': 30,
                'rec_mark': 'timeline',
                **self._params
            }
            resp = self.Session.get(url=url,params=params,headers=self._headers,cookies=self._cookies)
            
            jsondict = resp.json()
            self.__check_status(jsondict)
            newslist = []
            for newsitem in jsondict['result']:
                news_type = newsitem['content_type']
                #过滤掉杂七杂八的新闻类型
                if news_type == NewsContentType.TextNews or news_type == NewsContentType.CommunityArticle:
                    try:
                        linkid = int(newsitem['linkid'])
                        newsid = int(newsitem['newsid'])
                        newslist.append((linkid,newsid)) 
                    except KeyError:
                        self.logger.debug(f'提取新闻列表出错[{newsitem}]')
                elif news_type == NewsContentType.MultipleNews:
                    continue
                else:
                    self.logger.debug(f'未知的文章类型[{news_type}]')
                    self.logger.debug(f'[{newsitem}]')
            self.logger.debug(f'拉取[{len(newslist)}]篇新闻')
            return(newslist)
        #==========================================
        newsidlist = []
        max = (value // 30) + 3 #最大拉取次数
        i = 0
        while True:
            try:
                templist = _get_news_list(i * 30)
            except ClientException as e:
                continue
            finally:
                i+=1

            if templist:
                self.logger.info(f'拉取第[{i}]批新闻')
                newsidlist.extend(templist)
                sortedlist = list(set(newsidlist))
                sortedlist.sort(key=newsidlist.index)
                newsidlist = sortedlist
            else:
                self.logger.debug('新闻列表为空，可能遇到错误')
                break

            if len(newsidlist) >= value or i >= max:#防止请求过多被屏蔽
                break
        
        if len(newsidlist) > value:
            newsidlist = newsidlist[:value]
        if len(newsidlist) > 0:
            self.logger.debug(f'操作完成，拉取了[{len(newsidlist)}]篇新闻')
        else:
            self.logger.debug('拉取完毕，新闻列表为空，可能遇到错误')
        return(newsidlist)
    
    #NT
    def get_follow_post(self,value:int=30,ignoreliked:bool=True):
        '''
        拉取动态列表
        参数:
            value:要拉取的数量
            ignoreliked:忽略已点赞的动态?
        成功返回:
            eventslist:[(linkid,posttype,已点赞?),……] posttype释义参见:FollowPostType
        '''
        def _get_follow_post(offset:int=0):
            '''     
            拉取动态列表
            参数:
                offset:偏移,以30为单位
            成功返回:
                postlist:[(linkid,posttype,已点赞?),……]  posttype释义参见FollowPostType
            '''
            url = URLS.GET_SUBSCRIBED_EVENTS
            self.__flush_params()
            params = {
                'offset': offset,
                'limit': 30,
                'filters': 'post_link|follow_game|game_purchase|game_achieve|game_comment|roll_room',
                **self._params
            }
            resp = self.Session.get(url=url,params=params,headers=self._headers,cookies=self._cookies)
            jsondict = resp.json()
            self.__check_status(jsondict)
            postlist = []
            for moments in jsondict['result']['moments']:
                try:
                    link = moments['link']
                    linkid = int(link['linkid'])
                    is_liked = BoolenString(link['is_award_link'] == 1)
                    userid = moments['user']['userid']
                    posttype = moments['content_type']
                    if posttype == 'post_link':#发帖
                        posttype = FollowPostType.PostLink
                    elif posttype == 'follow_game':#关注游戏
                        posttype = FollowPostType.FollowGame
                    elif posttype == 'game_purchase':#购买游戏
                        posttype = FollowPostType.PurchaseGame
                    elif posttype == 'game_achieve':#获得成就
                        posttype = FollowPostType.AchieveGame
                    elif posttype == 'game_comment':#评价游戏
                        posttype = FollowPostType.CommentGame
                    elif posttype == 'roll_room':#赠送游戏
                        posttype = FollowPostType.CreateRollRoom
                    else:
                        posttype = FollowPostType.UnknownType
                        
                    if posttype == FollowPostType.CommentGame and userid == self.heybox_id:#过滤自己的评测
                        continue
                    if is_liked == False or ignoreliked == False :#忽略已点赞的动态
                        postlist.append((linkid,posttype,is_liked))
                except KeyError:
                    self.logger.debug(f'提取动态列表出错[{moments}]')
                    continue
            self.logger.debug(f'拉取了[{len(postlist)}]条动态')
            return(postlist)
        #==========================================
        eventslist = []
        if ignoreliked:
            max = (value // 15) + 3 #拉取的最大批数
        else:
            max = (value // 30) + 3 #拉取的最大批数
        i = 0
        while True:
            try:
                templist = _get_follow_post(i * 30)
            except ClientException as e:
                continue
            finally:
                i+=1

            if templist:
                self.logger.debug(f'拉取第[{i}]批动态')
                eventslist.extend(templist)
                sortedlist = list(set(eventslist))
                sortedlist.sort(key=eventslist.index)
                eventslist = sortedlist
            else:
                self.logger.debug('动态列表为空，可能遇到错误')
                break

            if len(eventslist) >= value or i >= max:#防止请求过多被屏蔽
                break

        if len(eventslist) > value:
            eventslist = eventslist[:value]
        if len(eventslist) > 0:
            self.logger.debug(f'操作完成，拉取了[{len(eventslist)}]条动态')
        else:
            self.logger.debug('拉取完毕，动态列表为空，可能遇到错误')
        return(eventslist)
    
    #NT
    def get_news_links(self,linkid:int,newsid:int,index:int=1):
        '''   
        拉取文章附加信息
        参数:
            linkid:链接id
            newsid:新闻id
            index:索引
        成功返回:
            has_video:是视频?
            is_liked:已点赞?
        失败返回:    
            False
        '''
        url = URLS.GET_LINK_TREE
        self.__flush_params()
        params = {
            'h_src':'LTE=',
            'link_id':linkid,
            'page':1,
            'limit':30,
            'is_first':1,
            'owner_only':0,
            'newsid':newsid,
            'rec_mark':'timeline',
            'pos':index + 1,
            'index':index,
            'page_tab':1,
            'from_recommend_list':	9,
            **self._params
        }
        if index == 0:
            params['al'] = 'set_top'

        resp = self.Session.get(url=url,params=params,headers=self._headers,cookies=self._cookies)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)
            link = jsondict['result']['link']
            is_liked = BoolenString(link['is_award_link'] == 1)
            #is_favour = BoolenString(link['is_favour'] == 1)
            has_video = BoolenString(link['has_video'] == 1)
            self.logger.debug(f'点赞{is_liked} 视频{has_video}')
            return((has_video,is_liked))
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'拉取文章附加信息出错[{e}]')
            return(False)  
        
    #NT
    def get_news_links_ex(self,linkid:int,newsid:int,index:int=1):
        '''   
        拉取文章更多附加信息
        参数:
            linkid:链接id
            newsid:新闻id
            index:索引
        成功返回:
            title:标题
            (author_name,author_id,author_level):(作者,作者id,作者等级)
            (click,like_count,comment_count):(点击数,点赞数,评论数)
        失败返回:    
            False
        '''
        url = URLS.GET_LINK_TREE
        self.__flush_params()
        params = {
            'h_src':'LTE=',
            'link_id':linkid,
            'page':1,
            'limit':30,
            'is_first':1,
            'owner_only':0,
            'newsid':newsid,
            'rec_mark':'timeline',
            'pos':index + 1,
            'index':index,
            'page_tab':1,
            'from_recommend_list':	9,
            **self._params
        }
        if index == 0:
            params['al'] = 'set_top'

        resp = self.Session.get(url=url,params=params,headers=self._headers,cookies=self._cookies)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)
            link = jsondict['result']['link']
            title = link['title']
            click = link['click']
            comment_count = link['comment_num']
            like_count = link['link_award_num']
            author_name = link['user']['username']
            author_id = link['user']['userid']
            author_level = link['user']['level_info'].get('level',0)
            self.logger.info(f'标题[{title}] 作者[{author_name}] @{author_id} [{author_level}级]')
            self.logger.info(f'点击[{click}] 点赞[{like_count}] 评论[{comment_count}]')
            return((title,(author_name,author_id,author_level),(click,like_count,comment_count)))
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'拉取文章附加信息出错[{e}]')
            return(False) 
    
    #NT
    def get_active_roll_room(self,value:int=30):
        '''
        拉取可参与的ROLL房列表
        参数:
            value:要拉取的数量
        成功返回:
            rollroomlist:[(link_id,room_id,人数,价格),……]
        '''
        def _get_active_roll_room(offset=0):
            '''
            拉取可参与的ROLL房列表
            参数:
                offset:偏移,以30为单位
            成功返回:
                rollroomlist:[(link_id,room_id,人数,价格),……]
            '''
            url = URLS.GET_ACTIVE_ROLL_ROOM
            self.__flush_params()
            params = {
                'filter_passwd':'1',
                'sort_types':'price',
                'page_type':'home',
                'offset':offset,
                'limit':'30',
                **self._params
            }
            resp = self.Session.get(url=url,params=params,headers=self._headers,cookies=self._cookies)
            
            jsondict = resp.json()
            self.__check_status(jsondict)
            roomlist = []
            for room in jsondict['result']['rooms']:
                try:
                    link_id = room['link_id']
                    room_id = room['room_id']
                    people = room['people']
                    price = room['price']
                    #self.logger.debug(f'房号{room_id}|价格{price}|人数{people}')
                    if not 'over' in room:
                        roomlist.append((link_id,room_id,people,price))
                    else:
                        break
                except KeyError as e:
                    self.logger.debug(f'提取ROLL房出错[{room}]')
            self.logger.debug(f'拉取[{len(roomlist)}]个ROLL房')
            return(roomlist)
        #==========================================
        rollroomlist = []
        max = (value // 30) + 3 #最大拉取次数
        i = 0
        while True:
            try:
                templist = _get_active_roll_room(i * 30)
            except ClientException as e:
                continue
            finally:
                i+=1

            if templist:
                self.logger.debug(f'拉取第[{i}]批ROLL房列表')
                rollroomlist.extend(templist)
                rollroomlist = list(set(newsidlist))
                sortedlist.sort(key=rollroomlist.index)
                rollroomlist = sortedlist
            else:
                self.logger.debug('ROLL房列表为空，可能没有可参与的ROLL房，也可能遇到错误')
                break

            if len(rollroomlist) >= value or i >= max:
                break

        if len(rollroomlist) > value:
            rollroomlist = rollroomlist[:value]
        if len(rollroomlist) > 0:
            self.logger.debug(f'操作完成，拉取了[{len(rollroomlist)}]个ROLL房')
        else:
            self.logger.debug('拉取完毕，ROLL房列表为空，可能没有可参与的ROLL房')
        return(rollroomlist)

    #NT
    def get_recommend_follow_list(self,value:int=30):
        '''
        拉取推荐关注列表
        参数:
            value:要拉取的数量
        成功返回:
            recfollowlist:[(id,关系,类型)……] 关系释义参见:RelationType
        '''
        def _get_recommend_follow_list(offset:int=0):
            '''
            拉取推荐关注列表
            参数:
                offset:偏移,以30为单位
            成功返回:
                userlist:[(id,关系,类型)……] 关系释义参见:RelationType
            '''
            url = URLS.GET_RECOMMEND_FOLLOWING
            self.__flush_params()
            params = {
                'offset':offset,
                'limit':'30',
                **self._params
            }
            resp = self.Session.get(url=url,params=params,headers=self._headers,cookies=self._cookies)

            jsondict = resp.json()
            self.__check_status(jsondict)
            userlist = []
            for user in jsondict['result']['rec_users']:
                try:
                    userid = int(user['userid'])
                    is_follow = BoolenString(user['is_follow'] == 1)
                    rec_tag = user['rec_tag']
                    if(rec_tag == '您的Steam好友'):
                        rec_type = RecTagType.SteamFriend
                    elif(rec_tag[-5:] == '位共同好友'):
                        rec_type = RecTagType.HasFriend
                    elif(rec_tag[-2:] == '作者'):
                        rec_type = RecTagType.Author
                    else:
                        rec_type = RecTagType.UnknownType
                    #self.logger.debug(f'ID{userid}关系{is_follow}类型{rec_type}')
                    userlist.append((userid,is_follow,rec_type))
                except KeyError:
                    self.logger.debug(f'提取推荐关注列表出错[{user}]')
            self.logger.debug(f'拉取[{len(userlist)}]个用户')
            return(userlist)            
        #==========================================
        recfollowlist = []
        max = (value // 30) + 3 #最大拉取次数
        i = 0
        while True:
            try:
                templist = _get_recommend_follow_list(i * 30)
            except ClientException as e:
                continue
            finally:
                i+=1

            if templist:
                self.logger.debug(f'拉取第[{i}]批推荐关注列表')
                recfollowlist.extend(templist)
                sortedlist = list(set(recfollowlist))
                sortedlist.sort(key=recfollowlist.index)
                recfollowlist = sortedlist
            else:
                self.logger.debug('推荐关注列表为空，可能遇到错误')
                break

            if len(recfollowlist) >= value or i >= max:
                break

        if len(recfollowlist) > value:
            recfollowlist = recfollowlist[:value]
        if len(recfollowlist) > 0:
            self.logger.debug(f'操作完成，拉取了[{len(recfollowlist)}]个用户')
        else:
            self.logger.debug('拉取完毕，推荐关注列表为空，可能遇到错误')
        return(recfollowlist)

    #NT
    def get_follower_list(self,value:int=30):
        '''
        拉取粉丝列表
        参数:
            value:要拉取的数量
        成功返回:
            followerlist:[(id,关系)……] 关系释义参见:RelationType
            '''
        def _get_follower_list(offset:int=0):
            '''
            拉取粉丝列表
            参数:
                offset:偏移,以30为单位
            成功返回:
                userlist:[(id,关系)……] 关系释义参见:RelationType
            '''
            url = URLS.GET_FOLLOWER_LIST
            self.__flush_params()
            params = {
                'userid':self.heybox_id,
                'offset':offset,
                'limit':30,
                **self._params
            }
            resp = self.Session.get(url=url,params=params,headers=self._headers,cookies=self._cookies)
            
            jsondict = resp.json()
            self.__check_status(jsondict)
            userlist = []
            for user in jsondict['follow_list']:
                try:
                    userid = int(user['userid'])
                    is_follow = BoolenString(user['is_follow'] == 1)
                    #self.logger.debug(f'ID{userid}|关系{is_follow}')
                    userlist.append((userid,is_follow))
                except KeyError as e:
                    self.logger.debug(f'提取粉丝列表出错[{item}]')
            self.logger.debug(f'拉取[{len(userlist)}]个用户')
            return(userlist)
        #==========================================
        followerlist = []
        max = (value // 30) + 3 #最大拉取次数
        i = 0
        while True:
            try:
                templist = _get_follower_list(i * 30)
            except ClientException as e:
                continue
            finally:
                i+=1

            if templist:
                self.logger.debug(f'拉取第[{i}]批粉丝列表')
                followerlist.extend(templist)
                sortedlist = list(set(followerlist))
                sortedlist.sort(key=followerlist.index)
                followerlist = sortedlist
            else:
                self.logger.debug('粉丝列表为空，可能遇到错误')
                break

            if len(followerlist) >= value or i >= max:
                break

        if len(followerlist) > value:
            followerlist = followerlist[:value]
        if len(followerlist) > 0:
            self.logger.debug(f'操作完成，拉取了[{len(followerlist)}]个用户')
        else:
            self.logger.debug('拉取完毕，粉丝列表为空，可能遇到错误')
        return(followerlist)

    #NT
    #拉取关注列表(value=30),返回[(id,关系)……] 关系释义参见:RelationType
    def get_following_list(self,value:int=30):
        '''
        拉取关注列表
        参数:
            value:要拉取的数量
        成功返回:
            followinglist:[(id,关系)……] 关系释义参见:RelationType
            '''
        def _get_following_list(offset:int=0):
            '''
            拉取关注列表
            参数:
                offset:偏移,以30为单位
            成功返回:
                userlist:[(id,关系)……] 关系释义参见:RelationType
            '''
            url = URLS.FOLLOWING_LIST
            self.__flush_params()
            params = {
                'userid':self.heybox_id,
                'offset':offset,
                'limit':30,
                **self._params
            }
            resp = self.Session.get(url=url,params=params,headers=self._headers,cookies=self._cookies)

            jsondict = resp.json()
            self.__check_status(jsondict)
            userlist = []
            for user in jsondict['follow_list']:
                try:
                    userid = int(user['userid'])
                    is_follow = BoolenString(user['is_follow'] == 1)
                    #self.logger.debug(f'ID{userid}|关系{is_follow}')
                    userlist.append((userid,is_follow))
                except KeyError as e:
                    self.logger.debug(f'提取关注列表出错[{item}]')

            self.logger.debug(f'拉取[{len(userlist)}]个用户')
            return(userlist)
        #==========================================
        followinglist = []
        max = (value // 30) + 3 #最大拉取次数
        i = 0
        while True:
            try:
                templist = _get_following_list(i * 30)
            except ClientException:
                continue
            i+=1

            if templist:
                self.logger.info(f'拉取第[{i}]批关注列表')
                followinglist.extend(templist)             
                sortedlist = list(set(followinglist))
                sortedlist.sort(key=followinglist.index)
                followinglist = sortedlist
            else:
                self.logger.error('拉取完毕，关注列表为空，可能遇到错误')
                break

            if len(followinglist) >= value or i >= max:
                break

        if len(followinglist) > value:
            followinglist = followinglist[:value]
        if len(followinglist) > 0:
            self.logger.debug(f'操作完成，拉取了[{len(followinglist)}]个用户')
        else:
            self.logger.debug('拉取完毕，关注列表为空，可能遇到错误')
        return(followinglist)

    #NT
    def get_ads_info(self):
        '''
        拉取广告信息
        成功返回:
            广告标题
        失败返回:
            False
        '''
        url = URLS.GET_ADS_INFO
        self.__flush_params()
        resp = self.Session.get(url=url,params=self._params,headers=self._headers,cookies=self._cookies)

        try:
            jsondict = resp.json()
            self.__check_status(jsondict)
            title = jsondict['result']['title']
            self.logger.debug(f'广告标题:[{title}]')
            return(title)
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'拉取广告信息出错[{e}]')
            return(False)

    #NT
    def like_news(self,linkid:int,newsid:int,index:int=1):
        '''
        给新闻点赞
        参数:
            linkid:链接id
            newsid:新闻id
            index:索引
        成功返回:
            True
        失败返回:
            False
        '''
        url = URLS.LIKE_LINK
        headers = {
            **self._headers,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'link_id': linkid,
            'award_type': 1
        }
        self.__flush_params()
        params = {
            'h_src': 'LTE=',
            'newsid': newsid,
            'rec_mark': 'timeline',
            'pos': index + 1,
            'index': index,
            'page_tab': 1,
            'al': 'set_top',
            'from_recommend_list': 3,
            **self._params
        }
        if index == 0:
            params['al'] = 'set_top'
        resp = self.Session.post(url=url,data=data,params=params,headers=headers,cookies=self._cookies)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)
            self.logger.debug('文章点赞成功')
            return(True)
        except Ignore:
            self.logger.debug('已经点过赞了')
            return(True)
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'点赞出错[{e}]')
            return(False)
    
    #NT
    def like_follow_post(self,linkid:int,followtype:int=0): 
        '''
        给好友动态点赞
        参数:
            linkid:链接id
            type:动态类型,释义参见FollowPostType
        成功返回:
            True
        失败返回:
            False
        '''
        headers = {
            **self._headers,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'link_id': linkid,
        }
        if followtype == FollowPostType.CommentGame:
            url = URLS.SUPPORT_COMMENT
            data['support_type'] = 1
        else:
            url = URLS.LIKE_LINK
            data['award_type'] = 1
        self.__flush_params()

        resp = self.Session.post(url=url,data=data,params=self._params,headers=headers,cookies=self._cookies)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)
            self.logger.debug('动态点赞成功')
            return(True)
        except Ignore:
            self.logger.debug('已经点过赞了')
            return(True)
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'动态点赞出错[{e}]')
            return(False)
     
    #NT
    def userlist_simplify(self,userlist:list):
        '''
        简化userlist,只保留userid
        参数:
            userlist:[userobj,…],userobj应该是包含userid的对象
        成功返回:
            suserlist:[userid,…],简化后的userlist
        '''
        suserlist = []
        if userlist:
            for userobj in userlist:
                try:
                    if type(userobj) == tuple or type(userobj) == list:
                        suserlist.append(int(userobj[0]))
                    else:
                        suserlist.append(int(userobj))
                except ValueError:
                    self.logger.debug(f'处理UserList元素出错[{userlist}]')
        else:
            self.logger.waring('Userlist是空的! 没有进行任何操作')
            suserlist = userlist
        return(suserlist)


            
                
    #NT
    def userlist_filte(self,userlist:list,filtersetting:dict):
        '''
        用户列表过滤
        参数:
            userlist:[(用户id,关系类型,用户标签),…]
            filtersetting:过滤器设置,过滤器设置按照从上到下的顺序匹配第一个有效的设置
                'FollowValue':过滤阈值  粉丝-关注>给定值的将被过滤
                'RelationType':过滤关系  正数:白名单|负数:黑名单  数字含义参见RelationType
                'RecTagType':过滤类型  正数:白名单|负数:黑名单  数字含义参见RecTagType  userlist需要包含'用户标签'
                'InvalidType':任意值  过滤正确的数值,不完整或者有错误的值会被过滤掉
        成功返回:
            fuserlist:过滤后的列表
        失败返回:
            False
        '''
        def filter_by_follow(userobj:list) -> bool:
            '''
            根据关注数量和粉丝数量过滤
            参数:
                userobj:(userid,关系,[类型])
            能通过返回:
                True
            通不过返回:
                False
            '''
            try:
                userid = int(userobj[0])
                relation = int(userobj[1])
                follow_num , fan_num , awd_num = self.get_user_profile(userobj[0])
                return(fan_num - follow_num <= value)
            except (ValueError,IndexError,TypeError):
                return(False)
        def filter_by_relation(userobj:list) -> bool:
            '''
            根据关系过滤
            参数:
                userobj:(userid,关系,[类型])
            能通过返回:
                True
            通不过返回:
                False
            '''
            try:
                userid = int(userobj[0])
                relation = int(userobj[1])
                if value >= 0:
                    return(relation == value)
                else:
                    return(relation != -value)
            except (ValueError,IndexError,TypeError):
                return(False)
        def filter_by_tagtype(userobj:list) -> bool:
            '''
            根据类型过滤
            参数:
                userobj:(userid,关系,类型)
            能通过返回:
                True
            通不过返回:
                False
            '''
            try:                
                userid = int(userobj[0])
                relation = int(userobj[1])
                type = int(userobj[2])
                if value >= 0:
                    return(type == value)
                else:
                    return(type != -value)
            except (ValueError,IndexError,TypeError):
                return(False)
        def filter_Invalid(userobj:list) -> bool:
            '''
            默认过滤器,过滤掉格式不对的userobj
            能通过返回:
                True
            通不过返回:
                False
            '''
            try:
                userid = int(userobj[0])
                relation = int(userobj[1])
                return(True)
            except(ValueError,IndexError,TypeError):
                return(False)
        #========================================
        if 'FollowValue' in filtersetting:
            value = filtersetting['FollowValue']
            filter = filter_by_follow
        elif 'RelationType' in filtersetting:
            value = filtersetting['RelationType']
            filter = filter_by_relation
        elif 'RecTagType' in filtersetting:
            value = filtersetting['RecTagType']
            filter = filter_by_tagtype
        elif 'InvalidType' in filtersetting:
            filter = filter_Invalid
        else:
            self.logger.waring('未设置过滤器,请指定正确的过滤器')
            return(False)

        fuserlist = []
        for user in userlist:
            if filter(user):
                fuserlist.append(user)
            #    self.logger.debug(f'保留用户[{user}]')
            #else:
            #    self.logger.debug(f'过滤用户[{user}]')
        self.logger.debug(f'过滤后共有[{len(fuserlist)}]个用户')
        return(fuserlist)

    #NT
    def share(self,newsid:int,index:int=1):
        '''
        分享新闻
        参数:
            newsid:新闻id
            index:索引
        成功返回:
            True
        失败返回:
            False
        '''
        def simu_share():
            '''
            模拟点击分享按钮
            成功返回:
                True
            失败返回:
                False
            '''
            url = URLS.SHARE_CLICK
            self.__flush_params()
            referer = {
                'from_tag':-1,
                'newsid':newsid,
                'rec_mark':'timeline',
                'pos':index + 1,
                'index':index,
                'page_tab':1,
                'from_recommend_list':9,
                'h_src':'LTE=',
                **self._params
            }
            if index == 0:
                referer['al'] = 'set_top'
            headers = {
                'Host': 'api.xiaoheihe.cn',
                'Connection': 'keep-alive',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1.0; MI 4LTE Build/OPM2.171019.029; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/75.0.3770.101 Mobile Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'X-Requested-With': 'com.max.xiaoheihe',   
                'Referer':URLS.GET_NEWS_DETAIL + str(newsid) + '?' + urllib.parse.urlencode(query=referer)
            }
            cookies = { 
                'user_pkey' : self._cookies['pkey'],
                'user_heybox_id' : self.heybox_id
            }
            resp = self.Session.get(url=url,headers=headers,cookies=cookies)
            try:
                jsondict = resp.json()
                self.__check_status(jsondict)
                self.logger.debug('模拟点击分享按钮')
                return(True)
            except ClientException as e:
                self.logger.error(f'分享出错[{e}]')
                return(False)
        def check_share_task_qq():
            '''
            检查分享结果
            成功返回:
                True
            '''
            url = URLS.SHARE_CHECK
            self.__flush_params()
            params = {
                'shared_type':'normal',
                'share_plat':'shareQQFriend',
                **self._params
            }
            resp = self.Session.get(url=url,headers=self._headers,params=params,cookies=self._cookies)
            try:
                jsondict = resp.json()
                self.__check_status(jsondict)
                self.logger.debug('分享成功')
                return(True)
            except (ShareError,ClientException) as e:
                self.logger.debug(f'分享出错(貌似还是可以完成任务) [{e}]')
                return(True) #貌似也能完成任务，所以返回True
        #==========================================
        op1 = simu_share()
        op2 = check_share_task_qq()
        return(op1 and op2)
    
    #NT
    def sign(self):
        '''
        签到
        成功返回:
            True
        失败返回:
            False
        '''
        url = URLS.SIGN
        self.__flush_params()
        resp = self.Session.get(url=url,params=self._params,headers=self._headers,cookies=self._cookies)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)

            level_info = jsondict['result']['level_info']
            exp = level_info['exp']
            coin = level_info['coin']
            max_exp = level_info['max_exp']
            level = level_info['level']

            result = jsondict['result']
            sign_in_coin = result['sign_in_coin']
            sign_in_exp = result['sign_in_exp']
            sign_in_streak = result['sign_in_streak']

            self.logger.debug(f'签到成功，连续[{sign_in_streak}]天')
            self.logger.info(f'获得[{sign_in_coin}]盒币,[{sign_in_exp}]经验')
            return(True)
        except Ignore:
            self.logger.debug('已经签过到了')
            return(True)
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'签到出错[{e}]')
            return(False)

    #NT
    def send_message(self,userid:int,message:str):
        '''
        发送消息
        参数:
            userid:用户id
            text:消息文字
        成功返回:
            True
        失败返回:
            False
        '''
        url = URLS.SEND_MESSAGE
        self.__flush_params()
        params = {
            'userid':userid,
            **self._params
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            **self._headers
        }
        data = {
            'text':message,
            'img':''
        }
        resp = self.Session.post(url=url,headers=headers,cookies=self._cookies,params=params,data=data)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)
            self.logger.debug('发送私信成功')
            return(True)
        except ClientException  as e:
            self.logger.error(f'发送私信出错[{e}]')
            return(False)

    #NT
    def get_game_detail(self,appid:int):
        '''
        读取游戏信息
        参数:
            appid:游戏id
        成功返回:
            (name,name_en):(中文名,英文名)
            is_follow:关注?
            (is_free,initial_price,current_price,discount):(免费?,原价,现价,折扣)
            (score,game_review_summary_num):(评分,评价):评价释义参见GameReviewSummaryType
            game_platform_type_num:平台:释义参见GamePlatformType
        失败返回:
            False
        '''
        url = URLS.GET_GAME_DETAIL
        self.__flush_params()
        params = {
            'appid':appid,
            **self._params
        }
        resp = self.Session.get(url=url,headers=self._headers,cookies=self._cookies,params=params)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)
            
            result = jsondict['result']
            name = result['name']
            name_en = result['name_en']
            name_en = name_en if name_en else name

            topic_detail = result['topic_detail']
            is_follow = BoolenString(topic_detail['is_follow'] == 1)
            is_free = BoolenString(result['is_free'])

            release_date = result['release_date']
            score = result.get('score',-1) #小黑盒评分
            game_platform_type = result['game_type']
            if game_platform_type == 'pc':
                game_platform_type_num = GamePlatformType.PCGame
                game_review_summary = result['game_review_summary']
                if not is_free:
                    price = result['price']
                    initial_price = price['initial']
                    current_price = price['current']
                    discount = price['discount']
                    lowest_price = price.get('lowest_price',price)
                    lowest_discount = price.get('lowest_discount',discount)
            elif game_platform_type == 'console':
                game_platform_type_num = GamePlatformType.ConsoleGame
                game_review_summary = '不支持'
            else:
                self.logger.warn(f'未知的游戏类型[{game_type}]')
                game_platform_type_num = GamePlatformType.UnknownType
                game_review_summary = '不支持'

            if game_review_summary == '好评如潮':
                game_review_summary_num = GameReviewSummaryType.PPPP
            elif game_review_summary == '特别好评':
                game_review_summary_num = GameReviewSummaryType.PPP
            elif game_review_summary == '多半好评':
                game_review_summary_num = GameReviewSummaryType.PP
            elif game_review_summary == '褒贬不一':
                game_review_summary_num = GameReviewSummaryType.PN
            elif game_review_summary == '多半差评':
                game_review_summary_num = GameReviewSummaryType.NN
            elif game_review_summary == '特别差评':
                game_review_summary_num = GameReviewSummaryType.NNN
            elif game_review_summary == '差评如潮':
                game_review_summary_num = GameReviewSummaryType.NNNN
            elif game_review_summary[-5:] == '篇用户评测':
                game_review_summary_num = GameReviewSummaryType.No
            else:
                game_review_summary_num = GameReviewSummaryType.UnknownType
                
            self.logger.debug(f'名称[{name} {name_en}] @ {appid}')
            if is_free:
                self.logger.debug('价格[免费游戏]')
            elif game_platform_type == GamePlatformType.PCGame:
                self.logger.debug(f'价格[{initial_price}￥ - {discount}% = {current_price}￥{" 史低" if current_price==lowest_price else ""}]')
            else:
                self.logger.debug('价格[不支持主机游戏]')
            self.logger.debug(f'评分[{score if score != -1 else "评分较少"}|{game_review_summary}] 发布日期[{release_date}]')
            return(((name,name_en),is_follow,(is_free,initial_price,current_price,discount),(score,game_review_summary_num),game_platform_type_num))
        except  (ClientException,KeyError,NameError)  as e:
            self.logger.error(f'拉取游戏详情出错[{e}]')
            return(False)

    #NT
    def get_game_detail_ex(self,appid:int):
        '''
        读取游戏更多信息
        参数:
            appid:游戏id
        成功返回:
            (developer,publishers,release_date):(开发商,发行商,发布日期)
            (follow_num,link_num):(关注数,帖子数)
            tags:[黑盒标签]
            genres:[Steam标签]
        失败返回:
            False
        '''
        url = URLS.GET_GAME_DETAIL
        self.__flush_params()
        params = {
            'appid':appid,
            **self._params
        }
        resp = self.Session.get(url=url,headers=self._headers,cookies=self._cookies,params=params)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)
            
            result = jsondict['result']
            name = result['name']
            name_en = result['name_en']
            name_en = name_en if name_en else name
 
            release_date = result['release_date']
            publishers = result['publishers'][0]['value']

            topic_detail = result['topic_detail']
            follow_num = topic_detail['follow_num'] #关注数
            link_num = topic_detail['link_num'] #帖子数
    
            game_platform_type = result['game_type']
            if game_platform_type == 'pc':
                developer = result['menu_v2'][1]['value']
            elif game_platform_type == 'console':
                developer = publishers
            else:
                self.logger.warn(f'未知的游戏类型[{game_type}]')
                developer = publishers

            tags = [] #小黑盒标签
            for tag in result['hot_tags']:
                desc = tag['desc']
                #key = tag['key']
                tags.append(desc)
            genres = [] #steam标签
            for genre in result['genres']:
                genres.append(genre)
                
            self.logger.debug(f'名称[{name} {name_en}] @ {appid}')
            self.logger.debug(f'开发商[{developer}] 发行商[{publishers}] 发布日期[{release_date}]')
            self.logger.debug(f'关注[{follow_num}] 帖子[{link_num}]')
            self.logger.debug(f'黑盒标签[{tags}]')
            self.logger.debug(f'Steam标签[{genres}]')
            return(((developer,publishers,release_date),(follow_num,link_num),tags,genres))
        except  (ClientException,KeyError,NameError)  as e:
            self.logger.error(f'拉取游戏详情出错[{e}]')
            return(False)

    #NT
    def do_communitu_surver(self):
        '''
        完成社区答题
        成功返回:
            True
        失败返回:
            False
        '''
        def get_community_survey():
            '''
            拉取社区答题题目
                成功返回:
                    True
                失败返回:
                    False
            '''
            url = URLS.COMMUNITY_SURVEY
            headers = {
                'Host': 'api.xiaoheihe.cn',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1.0; MI 4LTE Build/OPM2.171019.029; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/75.0.3770.101 Mobile Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'X-Requested-With': 'com.max.xiaoheihe'            
            }
            cookies = { 
                **self._cookies,
                'user_pkey' : self._cookies['pkey'],
                'user_heybox_id' : self.heybox_id
            }
            self.__flush_params()
            resp = self.Session.get(url=url,headers=headers,params=self._params,cookies=cookies)
            html = resp.text
            self.logger.debug(f'题库共[{len(html)}]字')
            return(True)
        def get_bbs_qa_state():
            '''
            获取答题情况，调用可以完成答题任务
            成功返回:
                state:1:答题成功,2:已经答过了|释义参见StateType
            失败返回:
                False
            '''
            url = URLS.BBS_QA_STATE
            self.__flush_params()
            headers = {
                'Host': 'api.xiaoheihe.cn',
                'Connection': 'keep-alive',
                'Accept': '*/*',
                'X-Requested-With': 'XMLHttpRequest',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1.0; MI 4LTE Build/OPM2.171019.029; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/75.0.3770.143 Mobile Safari/537.36',
                'Referer': URLS.COMMUNITY_SURVEY + '?' + urllib.parse.urlencode(query=self._params),
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            }
            cookies = {
                **self._cookies,
                'user_heybox_id':self.heybox_id
            }
            resp = self.Session.get(url=url,headers=self._headers,cookies=cookies)
            try:
                jsondict = resp.json()
                self.__check_status(jsondict)
                state = jsondict['result']['state']
                return(state)
            except (ClientException,KeyError,NameError)  as e:
                self.logger.error(f'获取答题情况出错[{e}]')
                return(False)
        #==========================================
        get_community_survey()
        state = get_bbs_qa_state()

        if state == 1 or state == 2:
            if state == StateType.Complete:
                self.logger.debug('答题完成，获得10经验')
            elif state == StateType.AlreadyDone:
                self.logger.debug('已经答过题了，无法重复答题')

            return(True)
        else:
            self.logger.debug('答题出错')
            return(False)

    #NT
    def get_news_body(self,newsid:int,index:int=1):
        '''
        拉取文章正文内容
        参数:
            newsid:新闻id
            index:索引
        成功返回:
            文章正文
        失败返回:
            False
        '''
        url = URLS.GET_NEWS_DETAIL + str(newsid)
        headers = {
            'Host': 'api.xiaoheihe.cn',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1.0; MI 4LTE Build/OPM2.171019.029; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/75.0.3770.101 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'X-Requested-With': 'com.max.xiaoheihe'            
        }
        cookies = { 
            **self._cookies,
            'user_pkey' : self._cookies['pkey'],
            'user_heybox_id' : self.heybox_id
        }
        self.__flush_params()
        params = {
            'from_recommend_list':9,
            'from_tag':-1,
            'h_src':'LTE=',
            'index':index,
            'newsid':newsid,
            'page_tab':1,
            'pos':index + 1,
            'rec_mark':'timeline',
            **self._params
        }
        if index == 0:
            params['al'] = 'set_top'
        resp = self.Session.get(url=url,params=params,headers=headers,cookies=cookies)
        try:
            html = resp.text
            soup = BeautifulSoup(html,'lxml')
            wz = soup.find(name='div',attrs={'class':'article-content','id':'post-content'}).get_text()
            if wz:
                self.logger.debug(f'拉取完成，共[{len(wz)}]字')
            else:
                self.logger.error('拉取内容为空，可能遇到错误')
            return(wz)
        except (ValueError,AttributeError) as e:
            self.logger.error(f'拉取文章出错[{e}]')
            return(False)    

    #NT
    def get_video_title(self,linkid:int,newsid:int,index:int=1):
        '''
        拉取视频标题
        参数:
            linkid:链接id
            newsid:新闻id
            index:索引
        成功返回:
            视频标题
        失败返回:
            False
        '''
        url = URLS.GET_VIDEO_VIEW
        headers = {
            'Host': 'api.xiaoheihe.cn',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 8.1.0; MI 4LTE Build/OPM2.171019.029; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/75.0.3770.101 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'X-Requested-With': 'com.max.xiaoheihe'            
        }
        cookies = { 
            **self._cookies,
            'user_pkey' : self._cookies['pkey'],
            'user_heybox_id' : self.heybox_id
        }
        self.__flush_params()
        params = {
            'from_recommend_list':9,
            'from_tag':-1,
            'h_src':'LTE=',
            'index':index,
            'newsid':newsid,
            'page_tab':1,
            'pos':index + 1,
            'link_id':linkid,
            'rec_mark':'timeline',
            **self._params
        }
        if index == 0:
            params['al'] = 'set_top'
        resp = self.Session.get(url=url,params=params,headers=headers,cookies=cookies)
        try:
            html = resp.text
            soup = BeautifulSoup(html,'lxml')
            wz = soup.title
            self.logger.debug('**暂不支持视频文章的处理**')
            return(wz)
        except (ValueError,AttributeError) as e:
            self.logger.error(f'拉取视频信息出错[{e}]')
            return(False)

    #NT
    def check_achieve_alert(self):
        '''
        查询有无新成就
        有成就返回:
            text:成就名
            desc:成就描述
        无成就返回:
            True
        失败返回:
            False
        '''
        url = URLS.ACHIEVE_LIST
        self.__flush_params()
        params = {
            'userid':self.heybox_id,
            'only_event':1,
            **self._params
        }
        resp = self.Session.get(url=url,params=params,headers=self._headers,cookies=self._cookies)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)
            if 'result' in jsondict:
                achieve_event = jsondict['result']['achieve_event']
                text = achieve_event['text']
                desc = achieve_event['desc']
                self.logger.debug(f'解锁新成就[{text}]|[{desc}]')
                return((text,desc))
            else:
                self.logger.debug('无新成就')
                return(True)
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'查询新成就出错[{e}]')
            return(False)    

    #NT
    def get_daily_task_stats(self):
        '''
        获取每日任务状态
        成功返回:
            finish_count:完成数
            task_count:任务总数
        失败返回:
            False
        '''
        url = URLS.GET_TASK_STATS
        self.__flush_params()
        resp = self.Session.get(url=url,params=self._params,headers=self._headers,cookies=self._cookies)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)
            result = jsondict['result']
            wait_count = result['wait']
            task_count = result['task']
            finish_count = task_count - wait_count
            self.logger.debug(f'任务完成度[{finish}/{task}]')
            return((finish_count,task_count))
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'获取任务状态出错[{e}]')
            return(False)

    #NT
    def get_daily_task_detail(self):
        '''
        获取每日任务详情
        成功返回:
            is_sign:签到?
            is_share:分享?
            is_like:点赞?
        失败返回:
            False
        '''
        url = URLS.GET_TASK_LIST
        self.__flush_params()
        resp = self.Session.get(url=url,params=self._params,headers=self._headers,cookies=self._cookies)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)
            
            task_list = jsondict['result']['task_list'][0]['tasks']
            is_sign = BoolenString(task_list[0]['state'] == 'finish')
            is_share = BoolenString(task_list[1]['state'] == 'finish')
            is_like = BoolenString(task_list[2]['state'] == 'finish')
            self.logger.debug(f"签到{sign}|分享{share}|点赞{like}")
            return((is_sign,is_share,like))
        except ClientException as e:
            self.logger.error(f'获取任务详情出错[{e}]')
            return(False)

    #NT
    def get_ex_task_detail(self):
        '''
        获取更多任务详情
        成功返回:(True:该任务*可能*完成,False:该任务*一定*未完成)
            band:绑定?
            bandwx:微信?
            public:公开?
            evaluate:评价?
            exam:答题?
            push:推送?
            profile:资料?
        失败返回:
        False
        '''
        url = URLS.GET_TASK_LIST
        self.__flush_params()
        resp = self.Session.get(url=url,params=self._params,headers=self._headers,cookies=self._cookies)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)          
            band = public = bandwx = exam = push = profile = evaluate = BoolenString(True)
            for task in jsondict['result']['task_list'][1]['tasks']:
                title = task['title']
                if title == '绑定Steam账号':
                    band = BoolenString(task['state'] == 'finish')
                elif title == '公开steam个人信息':
                    public = BoolenString(task['state'] == 'finish')
                elif title == '绑定微信号':
                    bandwx = BoolenString(task['state'] == 'finish')
                elif title == '完成社区答题':
                    exam = BoolenString(task['state'] == 'finish')
                elif title == '开启推送通知':
                    push = BoolenString(task['state'] == 'finish')
                elif title[:8] == '完善个人资料信息':
                    profile = BoolenString(task['state'] == 'finish')
                elif title[-4:] == '游戏评价':
                    evaluate = BoolenString(task['state'] == 'finish')
            self.logger.debug(f'绑定{band}|微信{bandwx}|公开{public}|评价{evaluate}|答题{exam}|推送{push}|资料{profile}')
            return((band,bandwx,public,evaluate,exam,push,profile))
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'获取任务详情出错[{e}]')
            return(False)

    #NT
    def get_my_data(self):
        '''
        获取我的任务数据
        成功返回:
            username:昵称
            coin:H币
            (level,exp,max_exp):(等级,经验,下级经验)
            sign_in_streak:连续签到天数)
        失败返回:
            False
        '''
        url = URLS.GET_TASK_LIST
        self.__flush_params()
        resp = self.Session.get(url=url,params=self._params,headers=self._headers,cookies=self._cookies)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)

            result = jsondict['result']['user']
            username = result['username']
            userid = result['userid']

            level_info = jsondict['result']['level_info']
            coin = level_info['coin']
            exp = level_info['exp']
            level = level_info['level']
            max_exp = level_info['max_exp']
            sign_in_streak = jsondict['result']['task_list'][0]['tasks'][0]['sign_in_streak']
            self.logger.debug(f'昵称:{username} @{userid} [{level}级]')
            self.logger.debug(f'盒币[{coin}]|经验[{exp}/{max_exp}]|连续签到[{sign_in_streak}]天')
            return((username,coin,(level,exp,max_exp),sign_in_streak))
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'获取我的任务数据详情出错[{e}]')
            return(False)

    #NT
    def get_user_profile(self,userid:int=-1):
        '''
        获取个人资料
        参数:
            userid:用户id,不填代入自己的id
        成功返回:
            follow_num:关注数
            fan_num:粉丝数
            awd_num:获赞数
        失败返回:
            False
        '''
        url = URLS.GET_USER_PROFILE
        if userid < 0:
            userid = self.heybox_id

        self.__flush_params()
        params = {
            'userid':userid,
            **self._params
        }
        resp = self.Session.get(url=url,params=params,headers=self._headers,cookies=self._cookies)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)

            bbs_info = jsondict['result']['account_detail']['bbs_info']
            follow_num = bbs_info['follow_num']
            fan_num = bbs_info['fan_num']
            awd_num = bbs_info['awd_num']

            account_detail = jsondict['result']['account_detail']
            level = account_detail['level_info']['level']
            userid = account_detail['userid']
            username = account_detail['username']
            self.logger.debug(f'昵称:{username} @{userid} [{level}级]')
            self.logger.debug(f'关注[{follow_num}],粉丝[{fan_num}],获赞[{awd_num}]')
            return((follow_num,fan_num,awd_num))
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'获取任务详情出错[{e}]')
            return(False)

    #NT
    def get_auth_info(self):
        '''
        获取自己的认证信息
        成功返回:
            has_password:有密码?
            phone_num:手机号
        失败返回:
            False
        '''
        url = URLS.GET_AUTH_INFO
        self.__flush_params()
        resp = self.Session.get(url=url,params=self._params,headers=self._headers,cookies=self._cookies)
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)

            result = jsondict['result'][0]
            has_password = BoolenString(result['has_password'] == 1)
            phone_num = result['src_id']
            if has_password:
                self.logger.debug(f'手机号[{src_id}]')
            else:
                self.logger.debug(f'手机号[{src_id}],**未设置密码**')
            return((has_password,phone_num))
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'获取安全信息出错[{e}]')
            return(False)

    #NT
    def check_heybox_version(self):
        '''
        检查小黑盒最新版本
        成功返回:
            True
        失败返回:
            False
        '''
        url = URLS.HEYBOX_VERSION_CHECK
        resp = self.Session.get(url=url,headers=self._headers)
        global HEYBOX_VERSION
        try:
            jsondict = resp.json()
            self.__check_status(jsondict)
            version = jsondict['result']['version']
            self.logger.info(f'检查更新成功，当前版本为[{version}]')
            HEYBOX_VERSION = version
            return(True)
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'获取小黑盒最新版本出错[{e}]')
            return(False)

    #未实现
    #def
    #NotImplementedupdate_profile(self,birthday=0,career='在校学生',education='本科',gender=1,nickname='',email=''):
    #    '''
    #    ***未实现***
    #    修改个人信息(生日,职业,教育经历,性别[1男2女],昵称,邮箱)
    #    '''
    #    url = URLS.UPDATE_PROFILE
    #    self.logger.error('该函数尚未实现')
    #    raise NotImplemented
    #    return(False)


    #未实现
    #def NotImplementedcheck_notice(self):
    #    '''
    #    ***未实现***
    #    查询有无新消息,返回True,False
    #    '''
    #    self.logger.error('该函数尚未实现')
    #    raise NotImplementedError
    #    return(False)

    #NT
    def check_script_version(self):
        '''
        检查脚本有无更新。
        有更新返回:
            tag_name:最新版本名称
            detail:更新简介
            download_url:下载地址)
        无更新返回:
            False
        失败返回:
            False
        '''
        url = URLS.SCRIPT_UPDATE_CHECK
        resp = requests.get(url=url)
        try:
            jsondict = resp.json()
            tag_name = jsondict['tag_name']
            detail = jsondict['body']
            #date = jsondict['created_at']
            download_url = jsondict['assets'][0]['browser_download_url']
            if (SCRIPT_VERSION[1:] != tag_name[1:]):
                if (float(SCRIPT_VERSION[1:]) < float(tag_name[1:])):
                    self.logger.debug(f'脚本有更新，当前版本{SCRIPT_VERSION} | 最新版{tag_name}')
                    return((tag_name,body,download_url))
            else:
                self.logger.debug('已经是最新版本')
            return(False)
        except (ClientException,KeyError,NameError) as e:
            self.logger.error(f'检测脚本更新出错[{e}]')
            return(False)

    #NT
    def __check_status(self,jsondict:dict):
        '''
        检查返回值
        参数:
            jsondict:json字典
        成功返回:
            True
        失败抛出异常
        '''
        try:
            status = jsondict['status']
            if status == 'ok':
                return (True)
            elif status == 'ignore':
                raise Ignore
            elif status == 'failed':
                msg = jsondict['msg'] 
                if msg == '操作已经完成':
                    raise Ignore
                elif msg == '不能进行重复的操作哦':
                    raise Ignore
                elif msg == '帖子已被删除':
                    raise ObjectError
                elif msg == '不能给自己的评价点赞哟':
                    raise SupportMyselfError
                elif msg == '自己不能粉自己哦':
                    raise FollowMyselfError
                elif msg == '您今日的关注次数已用完':
                    raise FollowLimitedError
                elif msg == '您的关注已经到上限了':
                    raise FollowLimitedError
                elif msg == '您今日的赞赏次数已用完':
                    raise LikeLimitedError
                elif msg == 'invalid userid':
                    raise UseridError
                elif msg == '参数错误':
                    raise ParamsError
                elif msg == '系统时间不正确':
                    raise LocalTimeError
                elif msg == '':
                    raise ShareError
                self.logger.error(f'未知的返回值[{msg}]')
                self.logger.error('请将以下内容发送到chr@chrxw.com')
                self.logger.error(f'{jsondict}')
                self.logger.error(f'{traceback.print_stack()}')
                raise UnknownError
            elif status == 'relogin':
                raise TokenError
        except (ValueError,NameError):
            self.logger.debug('JSON格式错误，请提交到chr@chrxw.com')
            self.logger.debug(f'{jsondict}')
            raise JsonAnalyzeError

    #NT
    def __flush_params(self):
        '''
        刷新_params里的time_和hkey键
        '''
        def gen_hkey(time:int):
            strhash = 'xiaoheihe/_time=' + str(time)
            md5 = hashlib.md5()
            md5.update(str(strhash).encode('utf-8'))
            hash = md5.hexdigest()
            hash = hash.replace('a','app')
            hash = hash.replace('0','app')
            md5 = hashlib.md5()
            md5.update(hash.encode('utf-8'))
            hkey = md5.hexdigest()
            return(hkey)
        asctime = int(time.time())
        self._params['hkey'] = gen_hkey(asctime)    
        self._params['_time'] = asctime

if __name__ == '__main__':
    print("请勿直接运行本模块，使用方法参见【README.md】")
else:
    HeyboxClient(0,'','','模块初始化').check_heybox_version()
                 