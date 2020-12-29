import random
import time
import requests
import functools
import json
import os
import pickle

from lxml import etree
from jd_logger import logger
from timer import Timer
from config import global_config
from concurrent.futures import ProcessPoolExecutor
from exception import SKException
from util import (
    parse_json,
    send_wechat,
    wait_some_time,
    response_status,
    save_image,
    open_image
)


class SpiderSession:
    """
    Session相关操作
    """
    def __init__(self):
        self.cookies_dir_path = "./cookies/"
        self.user_agent = global_config.getRaw('config', 'DEFAULT_USER_AGENT')

        self.session = self._init_session()

    def _init_session(self):
        session = requests.session()
        session.headers = self.get_headers()
        return session

    def get_headers(self):
        return {"User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;"
                          "q=0.9,image/webp,image/apng,*/*;"
                          "q=0.8,application/signed-exchange;"
                          "v=b3",
                "Connection": "keep-alive"}

    def get_user_agent(self):
        return self.user_agent

    def get_session(self):
        """
        获取当前Session
        :return:
        """
        return self.session

    def get_cookies(self):
        """
        获取当前Cookies
        :return:
        """
        return self.get_session().cookies

    def set_cookies(self, cookies):
        self.session.cookies.update(cookies)

    def load_cookies_from_local(self):
        """
        从本地加载Cookie
        :return:
        """
        cookies_file = ''
        if not os.path.exists(self.cookies_dir_path):
            return False
        for name in os.listdir(self.cookies_dir_path):
            if name.endswith(".cookies"):
                cookies_file = '{}{}'.format(self.cookies_dir_path, name)
                break
        if cookies_file == '':
            return False
        with open(cookies_file, 'rb') as f:
            local_cookies = pickle.load(f)
        self.set_cookies(local_cookies)

    def save_cookies_to_local(self, cookie_file_name):
        """
        保存Cookie到本地
        :param cookie_file_name: 存放Cookie的文件名称
        :return:
        """
        cookies_file = '{}{}.cookies'.format(self.cookies_dir_path, cookie_file_name)
        directory = os.path.dirname(cookies_file)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(cookies_file, 'wb') as f:
            pickle.dump(self.get_cookies(), f)


class QrLogin:
    """
    扫码登录
    """
    def __init__(self, spider_session: SpiderSession):
        """
        初始化扫码登录
        大致流程：
            1、访问登录二维码页面，获取Token
            2、使用Token获取票据
            3、校验票据
        :param spider_session:
        """
        self.qrcode_img_file = 'qr_code.png'

        self.spider_session = spider_session
        self.session = self.spider_session.get_session()

        self.is_login = False
        self.refresh_login_status()

    def refresh_login_status(self):
        """
        刷新是否登录状态
        :return:
        """
        self.is_login = self._validate_cookies()

    def _validate_cookies(self):
        """
        验证cookies是否有效（是否登陆）
        通过访问用户订单列表页进行判断：若未登录，将会重定向到登陆页面。
        :return: cookies是否有效 True/False
        """
        url = 'https://order.jd.com/center/list.action'
        payload = {
            'rid': str(int(time.time() * 1000)),
        }
        try:
            resp = self.session.get(url=url, params=payload, allow_redirects=False)
            if resp.status_code == requests.codes.OK:
                return True
        except Exception as e:
            logger.error("验证cookies是否有效发生异常", e)
        return False

    def _get_login_page(self):
        """
        获取PC端登录页面
        :return:
        """
        url = "https://passport.jd.com/new/login.aspx"
        page = self.session.get(url, headers=self.spider_session.get_headers())
        return page

    def _get_qrcode(self):
        """
        缓存并展示登录二维码
        :return:
        """
        url = 'https://qr.m.jd.com/show'
        payload = {
            'appid': 133,
            'size': 147,
            't': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.spider_session.get_user_agent(),
            'Referer': 'https://passport.jd.com/new/login.aspx',
        }
        resp = self.session.get(url=url, headers=headers, params=payload)

        if not response_status(resp):
            logger.info('获取二维码失败')
            return False

        save_image(resp, self.qrcode_img_file)
        logger.info('二维码获取成功，请打开京东APP扫描')
        open_image(self.qrcode_img_file)
        return True

    def _get_qrcode_ticket(self):
        """
        通过 token 获取票据
        :return:
        """
        url = 'https://qr.m.jd.com/check'
        payload = {
            'appid': '133',
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            'token': self.session.cookies.get('wlfstk_smdl'),
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.spider_session.get_user_agent(),
            'Referer': 'https://passport.jd.com/new/login.aspx',
        }
        resp = self.session.get(url=url, headers=headers, params=payload)

        if not response_status(resp):
            logger.error('获取二维码扫描结果异常')
            return False

        resp_json = parse_json(resp.text)
        if resp_json['code'] != 200:
            logger.info('Code: %s, Message: %s', resp_json['code'], resp_json['msg'])
            return None
        else:
            logger.info('已完成手机客户端确认')
            return resp_json['ticket']

    def _validate_qrcode_ticket(self, ticket):
        """
        通过已获取的票据进行校验
        :param ticket: 已获取的票据
        :return:
        """
        url = 'https://passport.jd.com/uc/qrCodeTicketValidation'
        headers = {
            'User-Agent': self.spider_session.get_user_agent(),
            'Referer': 'https://passport.jd.com/uc/login?ltype=logout',
        }

        resp = self.session.get(url=url, headers=headers, params={'t': ticket})
        if not response_status(resp):
            return False

        resp_json = json.loads(resp.text)
        if resp_json['returnCode'] == 0:
            return True
        else:
            logger.info(resp_json)
            return False

    def login_by_qrcode(self):
        """
        二维码登陆
        :return:
        """
        self._get_login_page()

        # download QR code
        if not self._get_qrcode():
            raise SKException('二维码下载失败')

        # get QR code ticket
        ticket = None
        retry_times = 85
        for _ in range(retry_times):
            ticket = self._get_qrcode_ticket()
            if ticket:
                break
            time.sleep(2)
        else:
            raise SKException('二维码过期，请重新获取扫描')

        # validate QR code ticket
        if not self._validate_qrcode_ticket(ticket):
            raise SKException('二维码信息校验失败')

        self.refresh_login_status()

        logger.info('二维码登录成功')


class JdSeckill(object):
    def __init__(self):
        self.spider_session = SpiderSession()
        self.spider_session.load_cookies_from_local()

        self.qrlogin = QrLogin(self.spider_session)

        # 初始化信息
        self.sku_id = global_config.getRaw('config', 'sku_id')
        self.seckill_num = 2
        self.seckill_init_info = dict()
        self.seckill_url = dict()
        self.seckill_order_data = dict()
        self.timers = Timer()

        self.session = self.spider_session.get_session()
        self.user_agent = self.spider_session.user_agent
        self.nick_name = None

    def login_by_qrcode(self):
        """
        二维码登陆
        :return:
        """
        if self.qrlogin.is_login:
            logger.info('登录成功')
            return

        self.qrlogin.login_by_qrcode()

        if self.qrlogin.is_login:
            self.nick_name = self.get_username()
            self.spider_session.save_cookies_to_local(self.nick_name)
        else:
            raise SKException("二维码登录失败！")

    def check_login(func):
        """
        用户登陆态校验装饰器。若用户未登陆，则调用扫码登陆
        """
        @functools.wraps(func)
        def new_func(self, *args, **kwargs):
            if not self.qrlogin.is_login:
                logger.info("{0} 需登陆后调用，开始扫码登陆".format(func.__name__))
                self.login_by_qrcode()
            return func(self, *args, **kwargs)
        return new_func

    @check_login
    def reserve(self):
        """
        预约
        """
        self._reserve()

    @check_login
    def seckill(self):
        """
        抢购
        """
        self._seckill()

    @check_login
    def seckill_by_proc_pool(self, work_count=5):
        """
        多进程进行抢购
        work_count：进程数量
        """
        with ProcessPoolExecutor(work_count) as pool:
            for i in range(work_count):
                pool.submit(self.seckill)

    def _reserve(self):
        """
        预约
        """
        while True:
            try:
                self.make_reserve()
                break
            except Exception as e:
                logger.info('预约发生异常!', e)
            wait_some_time()

    def _seckill(self):
        """
        抢购
        """
        while True:
            try:
                self.request_seckill_url()
                while True:
                    self.request_seckill_checkout_page()
                    self.submit_seckill_order()
            except Exception as e:
                logger.info('抢购发生异常，稍后继续执行！', e)
            wait_some_time()

    def make_reserve(self):
        """商品预约"""
        logger.info('商品名称:{}'.format(self.get_sku_title()))
        url = 'https://yushou.jd.com/youshouinfo.action?'
        payload = {
            'callback': 'fetchJSON',
            'sku': self.sku_id,
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://item.jd.com/{}.html'.format(self.sku_id),
        }
        resp = self.session.get(url=url, params=payload, headers=headers)
        resp_json = parse_json(resp.text)
        reserve_url = resp_json.get('url')
        self.timers.start()
        while True:
            try:
                self.session.get(url='https:' + reserve_url)
                logger.info('预约成功，已获得抢购资格 / 您已成功预约过了，无需重复预约')
                if global_config.getRaw('messenger', 'enable') == 'true':
                    success_message = "预约成功，已获得抢购资格 / 您已成功预约过了，无需重复预约"
                    send_wechat(success_message)
                break
            except Exception as e:
                logger.error('预约失败正在重试...')

    def get_username(self):
        """获取用户信息"""
        url = 'https://passport.jd.com/user/petName/getUserInfoForMiniJd.action'
        payload = {
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.user_agent,
            'Referer': 'https://order.jd.com/center/list.action',
        }

        resp = self.session.get(url=url, params=payload, headers=headers)

        try_count = 5
        while not resp.text.startswith("jQuery"):
            try_count = try_count - 1
            if try_count > 0:
                resp = self.session.get(url=url, params=payload, headers=headers)
            else:
                break
            wait_some_time()
        # 响应中包含了许多用户信息，现在在其中返回昵称
        # jQuery2381773({"imgUrl":"//storage.360buyimg.com/i.imageUpload/xxx.jpg","lastLoginTime":"","nickName":"xxx","plusStatus":"0","realName":"xxx","userLevel":x,"userScoreVO":{"accountScore":xx,"activityScore":xx,"consumptionScore":xxxxx,"default":false,"financeScore":xxx,"pin":"xxx","riskScore":x,"totalScore":xxxxx}})
        return parse_json(resp.text).get('nickName')

    def get_sku_title(self):
        """获取商品名称"""
        url = 'https://item.jd.com/{}.html'.format(global_config.getRaw('config', 'sku_id'))
        resp = self.session.get(url).content
        x_data = etree.HTML(resp)
        sku_title = x_data.xpath('/html/head/title/text()')
        return sku_title[0]

    def get_seckill_url(self):
        """获取商品的抢购链接
        点击"抢购"按钮后，会有两次302跳转，最后到达订单结算页面
        这里返回第一次跳转后的页面url，作为商品的抢购链接
        :return: 商品的抢购链接
        """
        url = 'https://itemko.jd.com/itemShowBtn'
        payload = {
            'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
            'skuId': self.sku_id,
            'from': 'pc',
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.user_agent,
            'Host': 'itemko.jd.com',
            'Referer': 'https://item.jd.com/{}.html'.format(self.sku_id),
        }
        while True:
            resp = self.session.get(url=url, headers=headers, params=payload)
            resp_json = parse_json(resp.text)
            if resp_json.get('url'):
                # https://divide.jd.com/user_routing?skuId=8654289&sn=c3f4ececd8461f0e4d7267e96a91e0e0&from=pc
                router_url = 'https:' + resp_json.get('url')
                # https://marathon.jd.com/captcha.html?skuId=8654289&sn=c3f4ececd8461f0e4d7267e96a91e0e0&from=pc
                seckill_url = router_url.replace(
                    'divide', 'marathon').replace(
                    'user_routing', 'captcha.html')
                logger.info("抢购链接获取成功: %s", seckill_url)
                return seckill_url
            else:
                logger.info("抢购链接获取失败，稍后自动重试")
                wait_some_time()

    def request_seckill_url(self):
        """访问商品的抢购链接（用于设置cookie等"""
        logger.info('用户:{}'.format(self.get_username()))
        logger.info('商品名称:{}'.format(self.get_sku_title()))
        self.timers.start()
        self.seckill_url[self.sku_id] = self.get_seckill_url()
        logger.info('访问商品的抢购连接...')
        headers = {
            'User-Agent': self.user_agent,
            'Host': 'marathon.jd.com',
            'Referer': 'https://item.jd.com/{}.html'.format(self.sku_id),
        }
        self.session.get(
            url=self.seckill_url.get(
                self.sku_id),
            headers=headers,
            allow_redirects=False)

    def request_seckill_checkout_page(self):
        """访问抢购订单结算页面"""
        logger.info('访问抢购订单结算页面...')
        url = 'https://marathon.jd.com/seckill/seckill.action'
        payload = {
            'skuId': self.sku_id,
            'num': self.seckill_num,
            'rid': int(time.time())
        }
        headers = {
            'User-Agent': self.user_agent,
            'Host': 'marathon.jd.com',
            'Referer': 'https://item.jd.com/{}.html'.format(self.sku_id),
        }
        self.session.get(url=url, params=payload, headers=headers, allow_redirects=False)

    def _get_seckill_init_info(self):
        """获取秒杀初始化信息（包括：地址，发票，token）
        :return: 初始化信息组成的dict
        """
        logger.info('获取秒杀初始化信息...')
        url = 'https://marathon.jd.com/seckillnew/orderService/pc/init.action'
        data = {
            'sku': self.sku_id,
            'num': self.seckill_num,
            'isModifyAddress': 'false',
        }
        headers = {
            'User-Agent': self.user_agent,
            'Host': 'marathon.jd.com',
        }
        resp = self.session.post(url=url, data=data, headers=headers)

        resp_json = None
        try:
            resp_json = parse_json(resp.text)
        except Exception:
            raise SKException('抢购失败，返回信息:{}'.format(resp.text[0: 128]))

        return resp_json

    def _get_seckill_order_data(self):
        """生成提交抢购订单所需的请求体参数
        :return: 请求体参数组成的dict
        """
        logger.info('生成提交抢购订单所需参数...')
        # 获取用户秒杀初始化信息
        self.seckill_init_info[self.sku_id] = self._get_seckill_init_info()
        init_info = self.seckill_init_info.get(self.sku_id)
        default_address = init_info['addressList'][0]  # 默认地址dict
        invoice_info = init_info.get('invoiceInfo', {})  # 默认发票信息dict, 有可能不返回
        token = init_info['token']
        data = {
            'skuId': self.sku_id,
            'num': self.seckill_num,
            'addressId': default_address['id'],
            'yuShou': 'true',
            'isModifyAddress': 'false',
            'name': default_address['name'],
            'provinceId': default_address['provinceId'],
            'cityId': default_address['cityId'],
            'countyId': default_address['countyId'],
            'townId': default_address['townId'],
            'addressDetail': default_address['addressDetail'],
            'mobile': default_address['mobile'],
            'mobileKey': default_address['mobileKey'],
            'email': default_address.get('email', ''),
            'postCode': '',
            'invoiceTitle': invoice_info.get('invoiceTitle', -1),
            'invoiceCompanyName': '',
            'invoiceContent': invoice_info.get('invoiceContentType', 1),
            'invoiceTaxpayerNO': '',
            'invoiceEmail': '',
            'invoicePhone': invoice_info.get('invoicePhone', ''),
            'invoicePhoneKey': invoice_info.get('invoicePhoneKey', ''),
            'invoice': 'true' if invoice_info else 'false',
            'password': global_config.get('account', 'payment_pwd'),
            'codTimeType': 3,
            'paymentType': 4,
            'areaCode': '',
            'overseas': 0,
            'phone': '',
            'eid': global_config.getRaw('config', 'eid'),
            'fp': global_config.getRaw('config', 'fp'),
            'token': token,
            'pru': ''
        }

        return data

    def submit_seckill_order(self):
        """提交抢购（秒杀）订单
        :return: 抢购结果 True/False
        """
        url = 'https://marathon.jd.com/seckillnew/orderService/pc/submitOrder.action'
        payload = {
            'skuId': self.sku_id,
        }
        try:
            self.seckill_order_data[self.sku_id] = self._get_seckill_order_data()
        except Exception as e:
            logger.info('抢购失败，无法获取生成订单的基本信息，接口返回:【{}】'.format(str(e)))
            return False

        logger.info('提交抢购订单...')
        headers = {
            'User-Agent': self.user_agent,
            'Host': 'marathon.jd.com',
            'Referer': 'https://marathon.jd.com/seckill/seckill.action?skuId={0}&num={1}&rid={2}'.format(
                self.sku_id, self.seckill_num, int(time.time())),
        }
        resp = self.session.post(
            url=url,
            params=payload,
            data=self.seckill_order_data.get(
                self.sku_id),
            headers=headers)
        resp_json = None
        try:
            resp_json = parse_json(resp.text)
        except Exception as e:
            logger.info('抢购失败，返回信息:{}'.format(resp.text[0: 128]))
            return False
        # 返回信息
        # 抢购失败：
        # {'errorMessage': '很遗憾没有抢到，再接再厉哦。', 'orderId': 0, 'resultCode': 60074, 'skuId': 0, 'success': False}
        # {'errorMessage': '抱歉，您提交过快，请稍后再提交订单！', 'orderId': 0, 'resultCode': 60017, 'skuId': 0, 'success': False}
        # {'errorMessage': '系统正在开小差，请重试~~', 'orderId': 0, 'resultCode': 90013, 'skuId': 0, 'success': False}
        # 抢购成功：
        # {"appUrl":"xxxxx","orderId":820227xxxxx,"pcUrl":"xxxxx","resultCode":0,"skuId":0,"success":true,"totalMoney":"xxxxx"}
        if resp_json.get('success'):
            order_id = resp_json.get('orderId')
            total_money = resp_json.get('totalMoney')
            pay_url = 'https:' + resp_json.get('pcUrl')
            logger.info('抢购成功，订单号:{}, 总价:{}, 电脑端付款链接:{}'.format(order_id, total_money, pay_url))
            if global_config.getRaw('messenger', 'enable') == 'true':
                success_message = "抢购成功，订单号:{}, 总价:{}, 电脑端付款链接:{}".format(order_id, total_money, pay_url)
                send_wechat(success_message)
            return True
        else:
            logger.info('抢购失败，返回信息:{}'.format(resp_json))
            if global_config.getRaw('messenger', 'enable') == 'true':
                error_message = '抢购失败，返回信息:{}'.format(resp_json)
                send_wechat(error_message)
            return False
