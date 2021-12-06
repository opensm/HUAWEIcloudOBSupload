#!/usr/bin/python
# -*- coding:utf-8 -*-
import glob
import hashlib
import json
import os
import sys
import time

import commands
from obs import ObsClient, LogConf

from Log import RecodeLog
from settings import *


def out_md5(src):
    # 简单封装
    m = hashlib.md5()
    m.update(src)
    return m.hexdigest()


class HUAWEIOBSManager:

    def __init__(self):
        self.tag_file = os.path.join(LOG_DIR, 'obs.tag')
        try:
            self.obs_obj = ObsClient(**HUAWEI_OBS_AUTH)
            self.obs_obj.initLog()
        except Exception as error:
            print("验证失败：{}".format(error))
            sys.exit(1)

    @staticmethod
    def read_json(json_file):
        """
        :param json_file:
        :return:
        """
        try:
            if not os.path.exists(json_file):
                raise Exception("文件不存在,{0}".format(json_file))
            with open(json_file, 'r') as fff:
                data = json.loads(fff.read())
                return data
        except Exception as error:
            RecodeLog.error(msg="读取{1}文件失败：{0}".format(error, json_file))
            return None

    @staticmethod
    def read_js(js_file):
        """
        :param js_file:
        :return:
        """
        try:
            if not os.path.exists(js_file):
                raise Exception("文件不存在,{0}".format(js_file))
            with open(js_file, 'r', ) as fff:
                data = fff.readlines()
                return data
        except Exception as error:
            RecodeLog.error(msg="读取{1}文件失败：{0}".format(error, js_file))
            return False

    def check_package(self, abs_path, archives):
        """
        :param abs_path:
        :param archives:
        :return:
        """
        archives_list = []
        for x in ['version.json', 'version.js', 'notice.json']:
            abs_archives = os.path.join(abs_path, x)
            if not os.path.exists(abs_archives):
                RecodeLog.warn(msg="{1}文件异常，文件个数：0,请检查压缩包:{0}！".format(archives, abs_archives))
                self.alert(message="{1}文件异常，文件个数：0,请检查压缩包:{0}！".format(archives, abs_archives))
                return False
            archives_list.append(abs_archives)
        json_version_data = self.read_json(json_file=os.path.join(abs_path, 'version.json'))
        if not json_version_data:
            RecodeLog.error(msg="{0}:数据读取异常！".format(os.path.join(abs_path, 'version.json')))
            self.alert(message="{0}:数据读取异常！".format(os.path.join(abs_path, 'version.json')))
            return False

        package = json_version_data['apk']
        version = json_version_data['version']
        abs_package = os.path.join(abs_path, package)
        if not os.path.exists(abs_package):
            RecodeLog.error(msg="文件不存在：{0}".format(abs_package))
            self.alert(message="文件不存在：{0}".format(abs_package))
            return False
        if package.split("_")[2] != version:
            RecodeLog.error(msg="获取的文件版本：{0}和version.json版本不一致：{1}".format(package, version))
            self.alert(message="获取的文件版本：{0}和version.json版本不一致：{1}".format(package, version))
            return False
        # 检查js
        js_version_data = self.read_js(js_file=os.path.join(abs_path, 'version.js'))
        js_version_status = False
        js_package_status = False
        for y in js_version_data:
            if "'version':'{0}'".format(version) in y.replace(' ', '').strip('\n'):
                js_version_status = True
            if "'package':'{0}'".format(package) in y.replace(' ', '').strip('\n'):
                js_package_status = True
        archives_list.append(abs_package)
        if js_version_status and js_package_status:
            RecodeLog.info(msg="{0},{1},{2},三者信息对应，检查无问题！".format(
                *[os.path.basename(x) for x in archives_list]
            ))
            return archives_list
        else:
            RecodeLog.error(msg="{0},{1},{2},三者信息不对应对应，检查不通过，请打包人员检查！".format(
                *[os.path.basename(x) for x in archives_list]
            ))
            self.alert(message="{0},{1},{2},三者信息不对应对应，检查不通过，请打包人员检查！".format(
                *[os.path.basename(x) for x in archives_list]
            ))
            return False

    @staticmethod
    def cmd(cmd_str):
        """
        :param cmd_str:
        :return:
        """
        try:
            status, output = commands.getstatusoutput(cmd_str)
            if status != 0:
                raise Exception(output)
            RecodeLog.info("执行:{0},成功!".format(cmd_str))
            return True
        except Exception as error:
            RecodeLog.error(msg="执行:{0},失败，原因:{1}".format(cmd_str, error))
            return False

    def unzip_package(self, package):
        """
        :param package:
        :return:
        """
        if not os.path.exists(package):
            RecodeLog.error("解压文件不存在，{0}!".format(package))
            sys.exit(1)
        filename, filetype = os.path.splitext(package)
        if filetype != ".zip":
            RecodeLog.error("打包的文件不是zip格式:{0}".format(package))
            self.alert(message="打包的文件不是zip格式:{0}".format(package))
            sys.exit(1)

        exec_str1 = "unzip -t {0}".format(package)
        if not self.cmd(cmd_str=exec_str1):
            RecodeLog.error("解压文件失败：{0}，任务退出!".format(package))
            return False

        exec_str = "unzip -o {0} -d {1}".format(package, filename)
        if not self.cmd(cmd_str=exec_str):
            RecodeLog.error("解压文件失败：{0}，任务退出!".format(package))
            sys.exit(1)
        return True

    def upload(self, archive_path, path):
        """
        :param archive_path:
        :param path:
        :return:
        """
        # 定义
        upload_path = os.path.join(archive_path, path)
        version_data = self.read_json(json_file=os.path.join(upload_path, 'version.json'))
        achieve_base_name = os.path.basename(archive_path)
        bucket = os.path.splitext(achieve_base_name)[-1].split("_")[-1]

        try:
            from obs import PutObjectHeader

            headers = PutObjectHeader()
            headers.contentType = 'text/plain'
            upload_data = "{}/".format(upload_path) if not upload_path.endswith(os.sep) else upload_path
            resp = self.obs_obj.putFile(
                bucketName=bucket, objectKey=path,
                file_path=upload_data,
                headers=headers
            )
            if isinstance(resp, list):
                for k, v in resp:
                    if v.status < 300:
                        RecodeLog.info(msg='requestId:{},etag:{},versionId:{},storageClass:{}'.format(
                            v.requestId, v.body.etag,
                            v.body.versionId,
                            v.body.storageClass
                        ))
                        RecodeLog.info(msg="上传资源成功,移动文件失败,文件名:{0},\n版本信息：{1}!".format(
                            os.path.basename("{}.zip".format(archive_path)),
                            json.dumps(version_data).replace(',', ',\n')))
            else:
                if resp.status < 300:
                    RecodeLog.info(msg='requestId:{},etag:{},versionId:{},storageClass:{}'.format(
                        resp.requestId, resp.body.etag,
                        resp.body.versionId,
                        resp.body.storageClass
                    ))
                    RecodeLog.info(msg="上传资源成功,移动文件失败,文件名:{0},\n版本信息：{1}!".format(
                        os.path.basename("{}.zip".format(archive_path)),
                        json.dumps(version_data).replace(',', ',\n')))
                else:
                    RecodeLog.error(msg='errorCode:{},errorMessage:{}'.format(
                        resp.errorCode,
                        resp.errorMessage
                    ))
                    raise Exception("上传异常！")
            return True
        except:
            import traceback
            RecodeLog.error(msg="上传异常:{}".format(traceback.format_exc()))
            return False

    def touch_tag(self):
        try:
            with open(self.tag_file, 'w') as fff:
                fff.write(str(time.time()))
        except Exception as error:
            RecodeLog.error(msg="创建tag文件:{0},失败，原因:{1}!".format(self.tag_file, error))
            self.alert(message="创建tag文件:{0},失败，原因:{1}!".format(self.tag_file, error))
            sys.exit(1)

    def check_tag(self):
        if os.path.exists(self.tag_file):
            try:
                with open(self.tag_file, 'r') as fff:
                    data = float(fff.readline().strip('\n'))
                    if time.time() - data > 1800:
                        raise Exception("标志文件产生时间超过30分钟，请运维检查是否有问题！")
                return True
            except Exception as error:
                self.alert(message=error)
                return True
        else:
            return False

    def check_task_file(self, archives_name):
        """
        :param archives_name:
        :return:
        """
        current_dir = os.path.dirname(archives_name)
        archives_path, filetype = os.path.splitext(os.path.basename(archives_name))
        finish_dir = os.path.join(current_dir, FINISH_DIR)
        error_dir = os.path.join(current_dir, ERROR_DIR)
        rm_cmd_str = "rm -f {0}".format(archives_name)
        if os.path.exists(
                os.path.join(
                    finish_dir,
                    os.path.basename(archives_name)
                )
        ) or os.path.exists(
            os.path.join(
                error_dir,
                os.path.basename(archives_name)
            )
        ) or os.path.exists(
            os.path.join(
                finish_dir,
                archives_path
            )
        ) or os.path.exists(
            os.path.join(
                error_dir,
                archives_path
            )
        ):
            RecodeLog.warn(msg="文件已经上传完成过：{0}".format(os.path.basename(archives_name)))
            self.alert(message="文件已经上传完成过：{0}".format(os.path.basename(archives_name)))
            self.cmd(cmd_str=rm_cmd_str)
            return False
        if not os.path.exists(archives_name):
            RecodeLog.error(msg="文件不存在:{0}".format(archives_name))
            self.alert(message="文件不存在:{0}".format(archives_name))
            return False
        archives_base_name = os.path.basename(archives_name)
        archives_name_data = os.path.splitext(archives_base_name)[0].split("_")
        if len(archives_name_data) != 4:
            RecodeLog.error(msg="{0}：上传文件必须以:打包时间_版本号_上传时间_bucket.zip格式，请检查！".format(archives_name_data))
            self.alert(message="{0}：上传文件必须以:打包时间_版本号_上传时间_bucket.zip格式，请检查！".format(archives_name_data))
        try:
            timestamp = time.mktime(time.strptime(archives_name_data[2], "%Y%m%d%H%M%S"))
        except Exception as error:
            RecodeLog.error(msg="{0}：上传文件必须以:打包时间_版本号_上传时间_bucket.zip格式，请检查！".format(archives_name_data, error))
            self.alert(message="{0}：上传文件必须以:打包时间_版本号_上传时间_bucket.zip格式，请检查！".format(archives_name_data))
            return False
        if time.time() < timestamp:
            RecodeLog.warn(msg="任务时间未到：{0}".format(archives_name))
            return False
        else:
            RecodeLog.info(msg="任务时间已到：{0}".format(archives_name))
            return True

    def run(self):
        """
        :return:
        """
        if self.check_tag():
            RecodeLog.warn(msg="已经有进程在上传文件，退出！")
            sys.exit(0)
        self.touch_tag()
        # 按照修改时间排序
        for x in sorted(glob.glob(os.path.join(UPLOAD_DIR, "*", "*.zip")), key=os.path.getmtime):
            # 相关定义
            # 上传前校验文件
            abs_path, filetype = os.path.splitext(x)

            error_dir = os.path.join(os.path.dirname(x), ERROR_DIR)
            finish_dir = os.path.join(os.path.dirname(x), FINISH_DIR)

            # 检查文件 检查异常则移动到报错文件夹
            if not os.path.isfile(x):
                RecodeLog.warn(msg="文件夹:{0},不支持当前上传！".format(x))
                exec_str = "mv {0} {1}".format(x, error_dir)
                if not self.cmd(exec_str):
                    self.alert(message="移动文件失败，文件名:{0}!".format(os.path.basename(x)))
                return False
            # 判断目录是否存在，不存在就创建
            for y in [ERROR_DIR, FINISH_DIR]:
                dirs = os.path.join(os.path.dirname(x), y)
                if os.path.exists(dirs):
                    continue
                os.makedirs(dirs)
                os.chown(dirs, 1000, 1000)
            # 文件名格式 20210410103200_v1.2.1_20210410110100_bucket.zip 打包时间_版本号_上传时间_bucket.zip
            if not self.check_task_file(archives_name=x):
                continue
            if not self.unzip_package(package=x):
                continue

            if os.path.exists(os.path.join(abs_path, 'tsp-android')):
                upload_path = 'tsp-android'
            elif os.path.exists(os.path.join(abs_path, 'tsp-ios')):
                upload_path = 'tsp-ios'
            else:
                RecodeLog.error(msg="打包内容错误！请检查打包！")
                sys.exit(1)
            check_result = self.check_package(abs_path=os.path.join(abs_path, upload_path), archives=x)
            if not check_result:
                exec_str1 = "mv {0} {1}".format(x, error_dir)
                exec_str2 = "mv {0} {1}".format(abs_path, error_dir)
                if not self.cmd(exec_str1) or not self.cmd(exec_str2):
                    self.alert(message="移动文件失败，文件名:{0}!".format(os.path.basename(x)))
                return False

            if not self.upload(archive_path=abs_path, path=upload_path):
                self.alert(message="客户端资源更新提示：上传资源失败。文件名:{0}!".format(os.path.basename(x)))
                RecodeLog.error(msg="打包内容错误！请检查打包！")
                exec_str1 = "mv {0} {1}".format(x, error_dir)
                exec_str2 = "mv {0} {1}".format(abs_path, error_dir)
                if not self.cmd(exec_str1) or not self.cmd(exec_str2):
                    self.alert(message="客户端资源更新提示：移动文件失败。文件名:{0}!".format(
                        os.path.basename(x)
                    ))
                    return False
            else:
                self.alert(message="客户端资源更新提示：上传资源成功。文件名:{0}!".format(os.path.basename(x)))
                exec_str1 = "mv {0} {1}".format(x, finish_dir)
                exec_str2 = "mv {0} {1}".format(abs_path, finish_dir)
                if not self.cmd(exec_str1) or not self.cmd(exec_str2):
                    self.alert(message="上传资源成功,移动文件失败,文件名:{0}!".format(
                        os.path.basename(x)
                    ))
                    # return False
        os.remove(self.tag_file)

    @staticmethod
    def alert(message, user=None):
        """
        :param message:
        :param user:
        :return:
        """
        import requests, hmac, urllib, base64
        token = DINGDING_ALERT_AUTH['dingding_token']
        secret = DINGDING_ALERT_AUTH['dingding_secret']
        if not token or not secret:
            print('you must set ROBOT_TOKEN or SECRET env')
            return
        url = 'https://oapi.dingtalk.com/robot/send?access_token=%s' % token
        if not user:
            send_data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "客户端更新提示",
                    "text": message
                },
                "at": {
                    "isAtAll": True
                }
            }
        else:
            send_data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "客户端更新提示",
                    "text": message
                },
                "at": {
                    "isAtAll": user
                }
            }
        headers = {'Content-Type': 'application/json'}
        timestamp = int(round(time.time() * 1000))
        secret_enc = secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.quote_plus(base64.b64encode(hmac_code))
        url = "{0}&timestamp={1}&sign={2}".format(url, timestamp, sign)
        x = requests.post(url=url, data=json.dumps(send_data), headers=headers)
        if 'errcode' in x.json():
            if x.json()["errcode"] == 0:
                RecodeLog.info("发送请求成功!")
                return True
            else:
                RecodeLog.error("发送请求失败:{0}".format(x.content))
                return False
        else:
            if x.json()["status"] == 0:
                RecodeLog.info("发送请求成功!")
                return True
            else:
                RecodeLog.error("发送请求失败:{0}".format(x.content))
                return False
