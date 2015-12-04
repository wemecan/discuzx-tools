#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""以服务的形式运行模拟用户操作.
"""

from __future__ import unicode_literals, print_function

import time
import datetime
import random
import string

from twisted.internet import task

from twisted.internet import reactor

from conf.data_config import robot_session, forum_session
from conf.logger_config import user_info
from common.func import Utils, CacheService
from register.factory import FakeMember, FakePost
from models.record import Member
from models.remote import CommonMember, CenterMember


def fake_member(gen_data_count=1):
    """创建虚拟账户.

        gen_data_count的取值建议不要大, 因为不希望在时间点上跳跃性增长.
        :parameter gen_data_count: 生成数据数量
    """

    for entity in FakeMember().generate(gen_data_count):
        username = entity["username"].lower()

        length = random.randint(6, 20)
        random_string = ''.join((entity["password"], str(entity["assist_number"])))
        random_string = [random.choice(random_string) for _ in range(length)]
        password = ''.join(random_string)

        # 用户中心md5后的实际密码.
        salt = "".join([random.choice(string.ascii_lowercase + string.digits) for _ in range(6)])
        hash_password = Utils.dz_uc_md5(password, salt)

        # 会员表md5后的伪密码.
        fake_password = Utils.md5(str(random.randint(10 * 9, 10 ** 10 - 1)))

        user_info.info("=" * 80)
        user_info.info("正在注册账户:%s" % username)

        try:
            common_member = CommonMember(__groupid=10,
                                         __username=username,
                                         __password=fake_password,
                                         __email=entity["email"],
                                         __regdate=int(time.time()))
            forum_session.add(common_member)
            forum_session.flush()
            uid = common_member.__uid

            center_member = CenterMember(__salt=salt,
                                         __username=username,
                                         __password=hash_password,
                                         __email=entity["email"],
                                         __regdate=int(time.time()),
                                         __uid=uid)

            forum_session.add(center_member)
            forum_session.commit()

            member = Member(username, password, entity["email"], uid)
            robot_session.add(member)
            robot_session.commit()
        except Exception, ex:
            user_info.exception(ex)
            user_info.info("注册账户失败: Error.")
            forum_session.rollback()
            robot_session.rollback()
        else:
            user_info.info("注册账户成功: OK.")
            CacheService.cache_data_insert_model("common_member", member)
        finally:
            forum_session.close()
            robot_session.close()


def fake_post(gen_data_count=1):
    """虚拟对主题回帖.

        :parameter gen_data_count: 生成数据数量
    """

    for post in FakePost().generate(gen_data_count):
        print(post)


action_data_config = (
    # 任务, 数据量, 时间间隔
    (fake_member, 1, 5.0),
)


def main():
    """事件模拟任务调度.
    """

    for data_item in action_data_config:
        if type(data_item[0]) == 'function':
            create_data = task.LoopingCall(data_item[0], data_item[1])
            create_data.start(data_item[2])

    reactor.run()


def minor():
    """仅对已扫描的数据数据执行上传操作.
    """

    while True:
        print(datetime.datetime.now())
        fake_member(1)
        # time.sleep(60)


def fake_member_only():
    """仅仅注册部分.
    """

    interval = (30, 50, 70, 100)
    limit = (1, 2, 3)

    # 纳入间隔时间后再次执行
    create_data = task.LoopingCall(fake_member, random.choice(limit))
    create_data.start(random.choice(interval))
    reactor.run()


if __name__ == '__main__':
    # main()
    # minor()
    fake_member_only()