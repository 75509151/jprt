# -*- coding: UTF-8 -*-
"""
Created on 2017-10-26

@author: jay
"""
import compileall
import os
import shutil
import sys
import glob
import click
import socket
import traceback
from subprocess import call
import datetime
import json

import urllib

import update_info as upi 
import update_utils as upu 

RELEASE_PWD_FILE = "/tmp/release_pwd"

##############
#
##############
DEL_FILES = set([])
OBFUSCATE_FILSE = []
# OBFUSCATE_FILSE = set([])
DEL_FOLDER = set(["tests", "docs", "var", "jprt.egg-info", ".git"])


def generate_version_file(path, version, after_day=7):
    if not os.path.exists(path):
        os.makedirs(path)
    update_day = datetime.date.today() + datetime.timedelta(days=1)
    info = {"version": version, "date": str(update_day)}
    version_info = os.path.join(path, "version")
    with open(version_info, "w") as f:
        json.dump(info, f)
    return version_info


# def _get_project_version(svn_path):
#     def get_svn_tag_version():
#         return_code, out, err = upu.do_cmd("svn info %s" % svn_path)
#         try:
#             lines = out.split('\n')
#             if len(lines) < 4:
#                 raise Exception("illegally svn path")
#             if lines[3].find("tags") == -1:
#                 raise Exception("it's not svn tags: %s" % svn_path)
#             version = lines[3].split('/')[-1]
#         except Exception as e:
#             raise e
#         return version

#     return get_svn_tag_version()


def dosome_folder(parent_path):
    def del_folder():
        if not DEL_FOLDER:
            return
        for folder in DEL_FOLDER:
            need_deal_path = os.path.abspath(os.path.join(parent_path, folder))
            if os.path.exists(need_deal_path):
                print ("delete folder", need_deal_path)
                shutil.rmtree(need_deal_path)

    del_folder()


def dosome_files(need_deal_files):
    def del_files(files):
        if not DEL_FILES:
            return
        for f in files:
            file_name = os.path.basename(f)
            if file_name in DEL_FILES:
                os.remove(f)
                print ("delete file:", file_name)

    def obfuscate_files(files):
        if not OBFUSCATE_FILSE:
            return
        for f in files:
            file_name = os.path.basename(f)
            if file_name in OBFUSCATE_FILSE:
                file_buf = f + "_buf"
                ret = os.system("pyobfuscate %s > %s" % (f, file_buf))
                if ret:
                    raise Exception("pyobfuscate failed!!!")
                os.remove(f)
                os.rename(file_buf, f)
                print ("pyobfuscate file:", file_name)

    del_files(need_deal_files)
    obfuscate_files(need_deal_files)


def _check_project(project_path):
    return
    print ("check svn status")

    # return_code, out, err = upu.do_cmd("svn update")
    # if return_code != 0 or err:
    #     raise Exception(err)

    return_code, out, err = upu.do_cmd("git status")
    print ("out", out)
    if return_code != 0 or err:
        raise Exception(err)
    if out:
        raise Exception("project not clean in svn: %s" % out)
    print ("git check end")
    return True


def _complite_project(project_path):
    return
    compileall.compile_dir(project_path, quiet=True)
    print ("complite end")


def _clean_project(project_path):

    def clean_py():
        print ("clean py begin")
        all_py = []
        for (dirpath, dirnames, filenames) in os.walk(project_path):
            # print dirpath, dirnames, filenames
            all_py += [os.path.join(dirpath, file)
                       for file in filenames if file.endswith(".py")]

        for py_file in all_py:
            os.remove(py_file)
        print ("clean py end")

    def clean_svn():
        print ("clean .svn begin")
        svn_info_path = os.path.join(project_path, ".git")
        if os.path.exists(svn_info_path):
            shutil.rmtree(svn_info_path)
        print ("clean .svn end")

    # clean_py()

    clean_svn()


def release_project(project_path, output_path):

    upu.cp_folder(project_path, output_path)
    print ("cp project to: %s" % output_path)

    dosome_folder(parent_path=output_path)
    files = upu.get_recursive_file_list(output_path)
    dosome_files(files)
    _complite_project(output_path)
    _clean_project(output_path)


def creat_and_cp_version_folder(release_path, output_path):

    version_floder = os.path.join(output_path)
    upu.cp_folder(release_path, output_path)
    print ("version floder:", version_floder)


def creat_and_cp_update_folder(source_path, output_path):
    upu.cp_folder(source_path, output_path)
    print ("udpate path:", output_path)


def rsync_file_to_remote(user, server, src, dest):
    #if dest: dest += "/"
    cmd = "rsync -az --delete --password-file=%s %s %s@%s::update/%s" % (
        RELEASE_PWD_FILE, src, user, server, dest)
    print ("do cmd: %s" % cmd)
    call(cmd, shell=True)


def release_to_remote(user, server, src, dest):
    rsync_file_to_remote(user, server, src, dest)


def generate_pwd_file(pwd):
    os.system("echo %s > %s" % (pwd, RELEASE_PWD_FILE))
    os.system("chmod 600 %s" % RELEASE_PWD_FILE)
    return RELEASE_PWD_FILE


def backup_jprt_path():
    jprt_path = os.path.join(upu.get_machine_home(), "jprt")
    backup_path = os.path.join(upu.get_machine_home(), "jprt_backup")
    if jprt_path:
        upu.cp_folder(jprt_path, backup_path)


def recover_jprt_path():
    jprt_path = os.path.join(upu.get_machine_home(), "jprt")
    backup_path = os.path.join(upu.get_machine_home(), "jprt_backup")
    if os.path.exists(backup_path):
        upu.cp_folder(backup_path, jprt_path)


@click.command("release")
@click.option("--user", "-u", prompt=u"版本服务器用户", default="jprt", help=u"版本服务器用户")
@click.option("--pwd", "-p", prompt=u"版本服务器密码", help=u"版本服务器密码")
@click.option("--project_path", "-pp", prompt=u"项目路径", default=os.path.join(upu.get_machine_home(), "release"), help=u"项目版本路径")
@click.option("--version", "-v", prompt=u"版本号",  help=u"版本号")
# @click.option("--svn_check", "-c", prompt=u"检测tag所在目录是否干净", type=click.Choice([True, False]), default=True)
@click.option("--server", "-s", prompt=u"版本服务器地址", default="", help=u"版本服务器地址")
@click.option("--after_day", "-af", prompt=u"几天后可以升级", type=int, default=7, help=u"几天后可以升级")
def generate_version_to_download(user, pwd, project_path, version, server, after_day):
    print ("*********** begin*************")
    # backup_jprt_path()
    try:
        release_path = os.path.join(upu.get_machine_home(), "jprt")

        print ("release path", release_path)

        if not os.path.exists(project_path):
            print ("svn tag路径不存在!!")
            sys.exit(1)

        upu.change_working_path(project_path)

        _check_project(project_path)

        # if not version:
            # version = _get_project_version(project_path)
            # print ("version", version)

        # release_project(project_path, release_path)

        tmp_release_path = os.path.abspath(
            os.path.join("/tmp", "tmp_release"))

        version_floder = os.path.join(tmp_release_path, version)
        project_dest_floder = os.path.join(version_floder, "jprt")
        creat_and_cp_version_folder(
            release_path, output_path=project_dest_floder)

        dosome_folder(parent_path=project_dest_floder)
        generate_pwd_file(pwd)
        release_to_remote(user, server, version_floder, upi.REMOTE_UPDATE_BASE_DIR)

        version_info = generate_version_file(project_dest_floder, version, after_day)

        release_to_remote(user, server, version_info, upi.REMOTE_UPDATE_BASE_DIR)
    except Exception as e:
        print (str(traceback.format_exc()))
        raise e
    # finally:
    #     recover_jprt_path()

    print ("*********** end*************")


if __name__ == '__main__':

    generate_version_to_download()
