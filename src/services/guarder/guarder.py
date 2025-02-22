# -*- coding: utf-8 -*-
# Time       : 2022/7/16 17:42
# Author     : QIN2DIM
# Github     : https://github.com/QIN2DIM
# Description:
from __future__ import annotations

import hashlib
import os
import random
import time

from loguru import logger
from selenium.common.exceptions import WebDriverException

from services.guarder.core import Guarder
from settings import project, SiteKey


class RainbowClaimer(Guarder):
    boolean_tags = ["yes", "bad"]

    def __init__(self, sitekey: str | None = SiteKey.epic):
        super().__init__()
        self.sitekey = sitekey
        self.monitor_site = f"https://accounts.hcaptcha.com/demo?sitekey={self.sitekey}"

        # 1. 添加 label_alias
        # ---------------------------------------------------
        # 不在 alias 中的挑战将被跳过

        # 2. 创建彩虹键
        # ---------------------------------------------------
        # 彩虹表中的 rainbow key

        # 3. 创建挑战目录
        # ---------------------------------------------------
        # 遇到新挑战时，先手动创建 rainbow_backup/challengeName/
        # 再在这个目录下分别创建 yes 和 bad 两个文件夹
        self.rainbow_backup_dir = project.rainbow_backup_dir

    @property
    def channel_dirs(self):
        channel_dirs = list(self.label_alias.values())
        for tag in self.boolean_tags:
            for channel_dir in channel_dirs:
                tmp = self.rainbow_backup_dir.joinpath(f"{channel_dir}/{tag}")
                tmp.mkdir(777, parents=True, exist_ok=True)
        return channel_dirs

    def download_images(self):
        if self.label_alias.get(self.label):
            super().download_images()

    def claim(self, ctx, retries=5):
        """定向采集数据集"""
        loop_times = -1
        start = time.time()

        while loop_times < retries:
            loop_times += 1
            # 有头模式下自动最小化
            try:
                ctx.get(self.monitor_site)
            except WebDriverException as err:
                if "ERR_PROXY_CONNECTION_FAILED" in err.msg:
                    logger.warning(err.msg)
                    ctx.close()
                    time.sleep(30)
                    continue
                raise err
            ctx.minimize_window()
            # 激活 Checkbox challenge
            self.anti_checkbox(ctx)
            for _ in range(random.randint(5, 8)):
                # 更新挑战框架 | 任务提前结束或进入失败
                if self.switch_to_challenge_frame(ctx) in [
                    self.CHALLENGE_SUCCESS,
                    self.CHALLENGE_REFRESH,
                ]:
                    loop_times -= 1
                    break
                # 勾取数据集 | 跳过非聚焦挑战
                self.hacking_dataset(ctx)
                # 随机休眠 | 降低请求频率
                time.sleep(random.uniform(1, 2))
            if time.time() - start > 180:
                # 解包数据集 | 每间隔运行3分钟解压一次数据集
                self.unpack()
                start = time.time()

    def _unpack(self, dst_dir, flag):
        """
        將 _challenge 中的内容解壓到目標路徑

        :param flag: 自定義標簽名
        :param dst_dir: rainbow_backup/<label>/
        :return:
        """
        # rainbow_backup/_challenge
        src_dir = self.workspace_dir

        # 标记已有的内容
        _exists_files = {}
        for _, _, files in os.walk(dst_dir):
            for fn in files:
                _exists_files.update({fn: "*"})

        # 清洗出包含標簽名的文件夾緩存
        # 1. 拼接挑戰圖片的絕對路徑
        # 2. 读取二进制流编成hash文件名
        # 3. 写到目标路径
        samples = set()
        for dir_challenge_cache_name in os.listdir(src_dir):
            if flag != dir_challenge_cache_name.split("_", 1)[
                -1
            ] or dir_challenge_cache_name.endswith(".png"):
                continue
            path_fs = os.path.join(src_dir, dir_challenge_cache_name)
            for img_filename in os.listdir(path_fs):
                path_img = os.path.join(path_fs, img_filename)
                with open(path_img, "rb") as file:
                    data = file.read()
                filename = f"{hashlib.md5(data).hexdigest()}.png"

                # 过滤掉已存在的文件，无论是 yes|bad|pending
                if not _exists_files.get(filename):
                    with open(os.path.join(dst_dir, filename), "wb") as file:
                        file.write(data)
                        samples.add(filename)

        return len(samples)

    def unpack(self):
        """
        解构彩虹表，自动分类，去重，拷贝

        FROM: rainbow_backup/_challenge
        TO: rainbow_backup/[*challengeName]

        :return:
        """
        statistics_ = {}
        for flag in self.channel_dirs:
            statistics_[flag] = self._unpack(
                dst_dir=os.path.join(self.rainbow_backup_dir, flag), flag=flag
            )
        return statistics_
