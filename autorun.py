#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author：mgboy time:2020/8/2

import win32api
import win32con, winreg, os, sys

"""判断键是否存在"""


def Judge_Key(key_name=None,
              reg_root=win32con.HKEY_CURRENT_USER,  # 根节点
              reg_path=r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",  # 键的路径
              abspath=None
              ):
    """
	:param key_name: #  要查询的键名
	:param reg_root: # 根节点
		#win32con.HKEY_CURRENT_USER
		#win32con.HKEY_CLASSES_ROOT
		#win32con.HKEY_CURRENT_USER
		#win32con.HKEY_LOCAL_MACHINE
		#win32con.HKEY_USERS
		#win32con.HKEY_CURRENT_CONFIG
	:param reg_path: #  键的路径
	:return:feedback是（0/1/2/3：存在/不存在/权限不足/报错）
	"""
    reg_flags = win32con.WRITE_OWNER | win32con.KEY_WOW64_64KEY | win32con.KEY_ALL_ACCESS
    try:
        key = winreg.OpenKey(reg_root, reg_path, 0, reg_flags)
        location, type = winreg.QueryValueEx(key, key_name)
        print("键存在", "location（数据）:", location, "type:", type)
        feedback = 0
        if location != abspath:
            feedback = 1
            print('键存在，但程序位置发生改变')
    except FileNotFoundError as e:
        print("键不存在", e)
        feedback = 1
    except PermissionError as e:
        print("权限不足", e)
        feedback = 2
    except:
        print("Error")
        feedback = 3
    return feedback


"""开机自启动"""


def AutoRun(switch="open",  # 开：open # 关：close
            key_name=None,
            abspath=os.path.abspath(sys.argv[0])):
    # 如果没有自定义路径，就用os.path.abspath(sys.argv[0])获取主程序的路径，如果主程序已经打包成exe格式，就相当于获取exe文件的路径
    judge_key = Judge_Key(reg_root=win32con.HKEY_CURRENT_USER,
                          reg_path=r"Software\Microsoft\Windows\CurrentVersion\Run",  # 键的路径
                          key_name=key_name,
                          abspath=abspath)
    # 注册表项名
    KeyName = r'Software\Microsoft\Windows\CurrentVersion\Run'
    key = win32api.RegOpenKey(win32con.HKEY_CURRENT_USER, KeyName, 0, win32con.KEY_ALL_ACCESS)
    if switch == "open":
        # 异常处理
        try:
            if judge_key == 0:
                print("已经开启了，无需再开启")
            elif judge_key == 1:
                win32api.RegSetValueEx(key, key_name, 0, win32con.REG_SZ, abspath)
                win32api.RegCloseKey(key)
                print('开机自启动添加成功！')
        except:
            print('添加失败')
    elif switch == "close":
        try:
            if judge_key == 0:
                win32api.RegDeleteValue(key, key_name)  # 删除值
                win32api.RegCloseKey(key)
                print('成功删除键！')
            elif judge_key == 1:
                print("键不存在")
            elif judge_key == 2:
                print("权限不足")
            else:
                print("出现错误")
        except:
            print('删除失败')



def check(state=1):
    """开机自启动函数"""
    if state == 1:
        AutoRun(switch='open', key_name='wallzoom')  # 键的名称应该起得特别一些，起码和已经存在的自启动软件名称不一致

    else:
        AutoRun(switch='close', key_name='wallzoom')

