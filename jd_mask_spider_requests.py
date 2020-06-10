import random
import sys
import time
from jdlogger import logger
from timer import Timer
import requests
from util import parse_json, get_session, get_sku_title,send_wechat
from config import global_config


class Jd_Mask_Spider(object):
    def __init__(self):
        # 初始化信息
        self.session = get_session()
        self.sku_id = global_config.getRaw('config', 'sku_id')
        self.seckill_init_info = dict()
        self.seckill_url = dict()
        self.seckill_order_data = dict()
        self.timers = Timer()
        self.default_user_agent = global_config.getRaw('config', 'DEFAULT_USER_AGENT')

    def login(self):
        for flag in range(1, 3):
            try:
                targetURL = 'https://order.jd.com/center/list.action'
                payload = {
                    'rid': str(int(time.time() * 1000)),
                }
                resp = self.session.get(
                    url=targetURL, params=payload, allow_redirects=False)
                if resp.status_code == requests.codes.OK:
                    logger.info('校验是否登录[成功]')
                    logger.info('用户:{}'.format(self.get_username()))
                    return True
                else:
                    logger.info('校验是否登录[失败]')
                    logger.info('请重新输入cookie')
                    time.sleep(1)
                    continue
            except Exception as e:
                logger.info('第【%s】次失败请重新获取cookie', flag)
                time.sleep(1)
                continue
        sys.exit(1)

    def make_reserve(self):
        """商品预约"""
        logger.info('商品名称:{}'.format(get_sku_title()))
        url = 'https://yushou.jd.com/youshouinfo.action?'
        payload = {
            'callback': 'fetchJSON',
            'sku': self.sku_id,
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.default_user_agent,
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
            'callback': 'jQuery'.format(random.randint(1000000, 9999999)),
            '_': str(int(time.time() * 1000)),
        }
        headers = {
            'User-Agent': self.default_user_agent,
            'Referer': 'https://order.jd.com/center/list.action',
        }
        try:
            resp = self.session.get(url=url, params=payload, headers=headers)
            resp_json = parse_json(resp.text)
            # 响应中包含了许多用户信息，现在在其中返回昵称
            # jQuery2381773({"imgUrl":"//storage.360buyimg.com/i.imageUpload/xxx.jpg","lastLoginTime":"","nickName":"xxx","plusStatus":"0","realName":"xxx","userLevel":x,"userScoreVO":{"accountScore":xx,"activityScore":xx,"consumptionScore":xxxxx,"default":false,"financeScore":xxx,"pin":"xxx","riskScore":x,"totalScore":xxxxx}})
            return resp_json.get('nickName') or 'jd'
        except Exception:
            return 'jd'

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
            'User-Agent': self.default_user_agent,
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
                logger.info("抢购链接获取失败，%s不是抢购商品或抢购页面暂未刷新，0.5秒后重试")
                time.sleep(0.1)

    def request_seckill_url(self):
        """访问商品的抢购链接（用于设置cookie等"""
        logger.info('用户:{}'.format(self.get_username()))
        logger.info('商品名称:{}'.format(get_sku_title()))
        self.timers.start()
        self.seckill_url[self.sku_id] = self.get_seckill_url()
        logger.info('访问商品的抢购连接...')
        headers = {
            'User-Agent': self.default_user_agent,
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
            'num': 2,
            'rid': int(time.time())
        }
        headers = {
            'User-Agent': self.default_user_agent,
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
            'num': 1,
            'isModifyAddress': 'false',
        }
        headers = {
            'User-Agent': self.default_user_agent,
            'Host': 'marathon.jd.com',
        }
        resp = self.session.post(url=url, data=data, headers=headers)
        return parse_json(resp.text)

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
            'num': 1,
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
            'password': '',
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
        self.seckill_order_data[self.sku_id] = self._get_seckill_order_data(
            )
        logger.info('提交抢购订单...')
        headers = {
            'User-Agent': self.default_user_agent,
            'Host': 'marathon.jd.com',
            'Referer': 'https://marathon.jd.com/seckill/seckill.action?skuId={0}&num={1}&rid={2}'.format(
                self.sku_id, 1, int(time.time())),
        }
        resp = self.session.post(
            url=url,
            params=payload,
            data=self.seckill_order_data.get(
                self.sku_id),
            headers=headers)
        resp_json = parse_json(resp.text)
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
            logger.info(
                '抢购成功，订单号:{}, 总价:{}, 电脑端付款链接:{}'.format(order_id,total_money,pay_url)
                )
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