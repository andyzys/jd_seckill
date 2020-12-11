import sys
from jd_mask_spider_requests import JdSecKill




if __name__ == '__main__':
    a = """
  ________   __    _ 
 |___  /\ \ / /   | |
    / /  \ V /    | |
   / /    > < _   | |
  / /__  / . \ |__| |1.预约商品
 /_____|/_/ \_\____/ 2.秒杀抢购商品 
    """
    print(a)

    jd_seckill = JdSecKill()
    choice_function = input('选择功能:')
    if choice_function == '1':
        jd_seckill.reserve()
    elif choice_function == '2':
        jd_seckill.seckill_by_proc_pool()
    else:
        print('没有此功能')
        sys.exit(1)

