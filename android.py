# -*- coding: utf-8 -*-

import os
import simplejson as json
import sys
import getopt
import commands
import shutil, time, datetime


def useage():
    print("%s -h\t#帮助文档" % sys.argv[0])
    print("%s -f\t#读取文件" % sys.argv[0])
    print("%s -s\t#强制升级" % sys.argv[0])
    print("%s -o\t#输出目录" % sys.argv[0])
    print("%s -t\t#任务时间" % sys.argv[0])
    print("%s -r\t#远程目录" % sys.argv[0])


def opt_json(read_file, status, out_dir):
    if not os.path.exists(read_file):
        raise Exception("{0} 文件不存在！".format(read_file))
    if not os.path.exists(out_dir):
        raise Exception("{0}:目录不存在！".format(out_dir))
    try:
        with open(read_file, 'r') as fff:
            source_json = json.loads(fff.read())
        json_data = {
            "version": "v{0}".format(source_json['elements'][0]['versionName']),
            "code": source_json['elements'][0]['versionCode'],
            "apk": source_json['elements'][0]['outputFile'],
            "mustUpgrade": status,
            "date": source_json['elements'][0]['outputFile'].split("_")[4].split(".")[0]
        }
        with open(os.path.join(out_dir, 'version.json'), 'w') as ffff:
            ffff.write(json.dumps(json_data))
        print("生成成功：{0}".format(os.path.join(out_dir, 'version.json')))
        return True
    except Exception as error:
        print(error)
        sys.exit(1)


def opt_js(read_file, status, out_dir):
    if not os.path.exists(read_file):
        raise Exception("{0} 文件不存在！".format(read_file))
    if not os.path.exists(out_dir):
        raise Exception("{0}:目录不存在！".format(out_dir))

    try:
        with open(read_file, 'r') as fff:
            source_json = json.loads(fff.read())
        js_data = "var VERSION_CONFIG = {'version':'v%s','date':'%s','package':'%s','code':'%s','must-upgrade':'%s'}" % (
            source_json['elements'][0]['versionName'],
            source_json['elements'][0]['outputFile'].split("_")[4].split(".")[0],
            source_json['elements'][0]['outputFile'],
            source_json['elements'][0]['versionCode'],
            status
        )
        with open(os.path.join(out_dir, 'version.js'), 'w') as ffff:
            ffff.write(js_data)
        print("生成成功：{0}".format(os.path.join(out_dir, 'version.js')))
        return True
    except Exception as error:
        print(error)
        sys.exit(1)


def zipfile(read_file, out_dir, task_time, remote_dir):
    """
    :param read_file:
    :param out_dir:
    :param task_time:
    :param remote_dir:
    :return:
    """
    if remote_dir == "dev":
        bucket = "tongyichelianwang-dev"
    elif remote_dir == "test":
        bucket = "tongyichelianwang-test"
    elif remote_dir == "prod":
        bucket = "chelianwang-prod"
    else:
        print("输入参数类型错误！")
        sys.exit(1)
    notice_current = os.path.join(out_dir, 'notice.json')
    if not os.path.exists(notice_current):
        print("{}不存在，请上传！".format(notice_current))
        sys.exit(1)
    file_dir = os.path.join(out_dir, "tsp-android")
    os.rename(notice_current, file_dir)
    if not os.path.exists(read_file):
        raise Exception("{0} 文件不存在！".format(read_file))
    if not os.path.exists(os.path.join(
            file_dir, 'version.js'
    )):
        raise Exception("{0}:目录不存在！".format(os.path.join(
            file_dir, 'version.js'
        )))
    if not os.path.exists(os.path.join(
            file_dir, 'version.json'
    )):
        raise Exception("{0}:目录不存在！".format(os.path.join(
            file_dir, 'version.json'
        )))
    if not os.path.exists(os.path.join(
            file_dir, 'notice.json'
    )):
        raise Exception("{0}:目录不存在！".format(os.path.join(
            file_dir, 'notice.json'
        )))
    try:
        timestamp = time.mktime(time.strptime(task_time, "%Y%m%d%H%M%S"))
    except Exception as error:
        print("任务时间异常：{0}".format(task_time, error))
        sys.exit(1)
    if time.time() > timestamp:
        print("任务时间已过，请重新生成!现在时间：{0}，任务时间：{1}".format(time.time(), timestamp))
        sys.exit(1)
    cp_dir = os.path.dirname(read_file)
    try:
        with open(read_file, 'r') as fff:
            source_json = json.loads(fff.read())
        if not os.path.exists(out_dir):
            raise Exception("{0}:文件不存在！".format(
                os.path.join(cp_dir, source_json['elements'][0]['outputFile'])))
        shutil.copy(
            os.path.join(cp_dir, source_json['elements'][0]['outputFile']),
            os.path.join(file_dir, source_json['elements'][0]['outputFile'])
        )
        zip_file = "./{0}_{1}_{2}_{3}.zip".format(
            datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            source_json['elements'][0]['versionName'],
            task_time,
            bucket
        )
        cmd_s = "cd {0} && zip -r {1} ${2} && rm -rf {2}".format(
            out_dir,
            zip_file,
            remote_dir
        )
        result, status = commands.getstatusoutput(cmd_s)
        if result != 0:
            raise Exception(status)
        print("生成成功：{0}".format(
            os.path.join(out_dir, '{0}_{1}_{2}.zip'.format(
                datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
                source_json['elements'][0]['versionName'],
                task_time
            ))))
        # upload_ftp(local_dir=out_dir, zip_file=zip_file, remote_dir=remote_dir)
        return True
    except Exception as error:
        print(error)
        sys.exit(1)


def cmd(cmd_str):
    """
    :param cmd_str:
    :return:
    """
    try:
        status, output = commands.getstatusoutput(cmd_str)
        if status != 0:
            raise Exception(output)
        print("执行:{0},成功!".format(cmd_str))
    except Exception as error:
        print("执行:{0},失败，原因:{1}".format(cmd_str, error))
        sys.exit(1)


def main():
    if len(sys.argv) == 1:
        useage()
        sys.exit()
    try:
        options, args = getopt.getopt(
            sys.argv[1:],
            "f:s:ho:t:r:"
        )
    except getopt.GetoptError:
        print("%s -h" % sys.argv[0])
        sys.exit(1)
    command_dict = dict(options)
    command_data = dict()
    # 帮助
    if '-h' in command_dict:
        useage()
        sys.exit()
    # 获取监控项数据
    elif '-s' in command_dict and "-f" in command_dict and '-o' in command_dict and '-t' in command_dict and '-r' in command_dict:
        command_data['read_file'] = command_dict.get('-f')
        command_data['status'] = command_dict.get('-s')
        command_data['out_dir'] = command_dict.get('-o')
        command_data['task_time'] = command_dict.get('-t')
        command_data['remote_dir'] = command_dict.get('-r')
        sub_path = os.path.join(command_data['out_dir'], command_data['remote_dir'])
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)
        opt_json(
            read_file=command_data['read_file'],
            status=command_data['status'],
            out_dir=sub_path
        )
        opt_js(
            read_file=command_data['read_file'],
            status=command_data['status'],
            out_dir=sub_path
        )
        zipfile(
            read_file=command_data['read_file'],
            out_dir=command_data['out_dir'],
            task_time=command_data['task_time'],
            remote_dir=command_data['remote_dir']
        )
        sys.exit(0)
    else:
        useage()
        sys.exit(1)


if __name__ == "__main__":
    main()
