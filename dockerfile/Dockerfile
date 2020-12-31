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
      
