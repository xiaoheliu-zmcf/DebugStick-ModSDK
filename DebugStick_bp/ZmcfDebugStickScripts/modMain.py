# -*- coding: utf-8 -*-
from mod.common.mod import Mod
import mod.client.extraClientApi as clientApi
import mod.server.extraServerApi as serverApi
import modConfig


@Mod.Binding(name=modConfig.ModName, version=modConfig.ModVersion)
class DebugStickScript(object):
    def __init__(self):
        pass

    @Mod.InitServer()
    def InitServer(self):
        serverApi.RegisterSystem(
            modConfig.ModName,
            modConfig.server_system_name,
            modConfig.server_class_path
        )
        print("[调试棒-追梦次方-Studio]ServerSystem注册成功")

    @Mod.InitClient()
    def InitClient(self):
        clientApi.RegisterSystem(
            modConfig.ModName,
            modConfig.client_system_name,
            modConfig.client_class_path
        )
        print("[调试棒-追梦次方-Studio]ClientSystem注册成功")

    @Mod.DestroyServer()
    def DestroyServer(self):
        pass

    @Mod.DestroyClient()
    def DestroyClient(self):
        pass
