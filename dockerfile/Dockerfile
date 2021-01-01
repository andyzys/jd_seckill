FROM python:3.8-slim-buster

LABEL MAINTAINER="@weidonggg"

ENV GIT_BRANCH master
ENV TIMEZONE Asia/Shanghai

COPY docker-python-entrypoint /usr/local/bin/
COPY qrcode /usr/local/bin/

RUN set -ex; \
    ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime \
      && echo $TIMEZONE > /etc/timezone; \
     \
      { \
      echo 'deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster main contrib non-free'; \
      echo '# deb-src https://mirrors.tuna.tsinghua.edu.cn/debian/ buster main contrib non-free'; \
      echo 'deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-updates main contrib non-free'; \
      echo '# deb-src https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-updates main contrib non-free'; \
      echo 'deb https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-backports main contrib non-free'; \
      echo '# deb-src https://mirrors.tuna.tsinghua.edu.cn/debian/ buster-backports main contrib non-free'; \
      echo 'deb https://mirrors.tuna.tsinghua.edu.cn/debian-security buster/updates main contrib non-free'; \
      echo '# deb-src https://mirrors.tuna.tsinghua.edu.cn/debian-security buster/updates main contrib non-free'; \
      } > /etc/apt/sources.list; \
      \
      # install qrcode view tools.
      apt-get update \
        && apt-get install -y --no-install-recommends \
                   git \
                   qrencode \
                   zbar-tools; \
      \
      # clone jd seckill code.
      git clone -b $GIT_BRANCH https://github.com/huanghyw/jd_seckill.git /app; \
      cd /app \
        && rm -rf .git; \
      \
       \
        \
      sed -i \
        -e 's/^eid.*/eid=$JD_SECKILL_EID/g' \
        -e 's/^fp.*/fp=$JD_SECKILL_FP/g' \
        -e 's/^sku_id.*/sku_id=$JD_SECKILL_SKU_ID/g' \
        -e 's/^buy_time.*/buy_time=$JD_SECKILL_BUY_TIME/g' \
        -e 's/^default_user_agent.*/default_user_agent=$JD_SECKILL_DEFAULT_USER_AGENT/g' \
        -e 's/^random_useragent.*/random_useragent=$JD_SECKILL_RANDOM_USERAGENT/g' \
        -e 's/^payment_pwd.*/payment_pwd=$JD_SECKILL_PAYMENT_PWD/g' \
        -e 's/^server_chan_enable.*/server_chan_enable=$JD_SECKILL_SERVER_CHAN_ENABLE/g' \
        -e 's/^server_chan_sckey.*/server_chan_sckey=$JD_SECKILL_SERVER_CHAN_SCKEY/g' \
        -e 's/^email_enable.*/email_enable=$JD_SECKILL_EMAIL_ENABLE/g' \
        -e 's/^email_host.*/email_host=$JD_SECKILL_EMAIL_HOST/g' \
        -e 's/^email_user.*/email_user=$JD_SECKILL_EMAIL_USER/g' \
        -e 's/^email_pwd.*/email_pwd=$JD_SECKILL_EMAIL_PWD/g' \
        -e '/#/d' \
        config.ini; \
      \
       \
        \
      pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/; \
      \
      chmod +x /usr/local/bin/docker-python-entrypoint; \
      chmod +x /usr/local/bin/qrcode; \
      \
      # clean apt cache.
      apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false; \
      rm -rf /var/lib/apt/lists/*


WORKDIR /app

ENTRYPOINT ["docker-python-entrypoint"]

CMD ["seckill"]
      
