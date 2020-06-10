# Jd_mask[如果可以点下右上角的star给颗小星星呗谢谢]
# 因为最近忙于换工作的原因,此代码不会再更新.等后面618之类的活动此代码会再更新.而且一直没来回复issues,各位大佬不好意思.告辞!

##### 此tool只单独支持预约-抢购-成功后直接提交订单的商品.[口罩],只提供学习参考用途.!

##### 此代码基于原作者https://github.com/tychxn/jd-assistan 进行修改合并

##### 非常感谢原作者https://github.com/tychxn/jd-assistant 提供的代码
[![star, issue](https://img.shields.io/badge/star%2C%20issue-welcome-brightgreen.svg)](https://github.com/zhou-xiaojun/jd_mask)

## 主要功能

- 登陆京东商城（[www.jd.com](http://www.jd.com/)）
  - cookies登录 (需要自己手动获取)
- 预约商品
  - 定时自动预约
- 秒杀预约后等待抢购的商品
  - 定时开始自动抢购

## 运行环境

- [Python 3](https://www.python.org/)

## 第三方库

- [Requests](http://docs.python-requests.org/en/master/)

## 使用教程

程序主入口在 `main.py`

在config.ini文件填入config里面对应的内容
eid,和fp找个普通商品随便下单,然后抓包就能看到,这两个值可以填固定的
cookies_string,sku_id,DEFAULT_USER_AGENT(和cookie获取同一个地方就会看到.直接复制进去就可以了),以上都是必填的.

启动时按照提示操作输入需要的功能即可

## 更新记录

- 【2020.02.24】新增微信推送,去除了冗余代码,进行模块化处理.

## 备注

- 关于时间的设置,我测试成功的2次都是设置了整点获取抢购连接失败一次后1s再获取成功,后面试过测试了2次0.6s的反而不行,会出现请求获取订单参数超时导致报错.网络好的可以试一下设置0.5s左右的误差
- 本来时间不足,加上一天只能测试一次.而且网络不稳定.只抢购成功2次.而且都是数量1,我记得有几个口罩不能设置数量,只能抢购1个,所以要注意这点.
- 代码在`macOS`中编写，如果在其他平台上运行出行问题，欢迎提issue。
