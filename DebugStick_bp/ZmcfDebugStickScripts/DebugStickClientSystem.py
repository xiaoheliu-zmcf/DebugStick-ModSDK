# -*- coding: utf-8 -*-
#导入客户端API模块
import mod.client.extraClientApi as clientApi
#获取"客户端'的基类
ClientSystem = clientApi.GetClientSystemCls()
#导入配置文件
import modConfig


class DebugStickClientSystem(ClientSystem):
    def __init__(self, namespace, systemName):
        ClientSystem.__init__(self, namespace, systemName)
        self.noOpSetting = False
        self.ListenEvent()

    def ListenEvent(self):
        ns = clientApi.GetEngineNamespace()
        sys = clientApi.GetEngineSystemName()

        self.ListenForEvent(ns, sys, 'UiInitFinished', self, self.OnUiInitFinished)
        self.ListenForEvent(ns, sys, 'RightClickBeforeClientEvent', self, self.OnRightClickBefore)

    def OnUiInitFinished(self, args):
        levelId = clientApi.GetLevelId()
        comp = clientApi.GetEngineCompFactory().CreateNeteaseWindow(levelId)
        settingInst = comp.RegisterSettingInst(
            modConfig.ResourceId,
            modConfig.ModName,
            modConfig.ModIcon
        )
        if settingInst:
            (settingInst
                .AddButton("OpenDeveloperWindow", "", "作者主页", self.OpenDeveloperWindow, 2)
                .AddButton("OpenResourceCenterDetailWindow", "", "资源中心详情", self.OpenResourceCenterDetailWindow, 2)
                .AddToggle("NoOp_setting", "允许非管理员玩家使用调试棒", self.NoOp_setting, 1, False)
            )

    def OpenDeveloperWindow(self, key, value):
        playerId = clientApi.GetLocalPlayerId()
        comp = clientApi.GetEngineCompFactory().CreateNeteaseWindow(playerId)
        comp.OpenDeveloperHomeWindow(modConfig.DeveloperHome)

    def OpenResourceCenterDetailWindow(self, key, value):
        playerId = clientApi.GetLocalPlayerId()
        comp = clientApi.GetEngineCompFactory().CreateNeteaseWindow(playerId)
        comp.OpenResourceCenterDetailWindow(modConfig.ResourceId)

    def NoOp_setting(self, key, value):
        self.noOpSetting = bool(value)
        eventData = self.CreateEventData()
        eventData['noOpSetting'] = self.noOpSetting
        self.NotifyToServer(modConfig.NoOpSettingEventName, eventData)

    def OnRightClickBefore(self, args):
        playerId = clientApi.GetLocalPlayerId()
        if not self._holdingDebugStick(playerId):
            return
        if not self._canUse(playerId):
            return

        args['cancel'] = True

        cam = clientApi.GetEngineCompFactory().CreateCamera(clientApi.GetLevelId())
        pick = cam.PickFacing()
        if not pick or pick.get('type') != 'Block':
            return

        eventData = self.CreateEventData()
        eventData['playerId'] = playerId
        eventData['x'] = int(pick.get('x', 0))
        eventData['y'] = int(pick.get('y', 0))
        eventData['z'] = int(pick.get('z', 0))
        self.NotifyToServer(modConfig.RightClickEventName, eventData)

    def _holdingDebugStick(self, playerId):
        comp = clientApi.GetEngineCompFactory().CreateItem(playerId)
        itemDict = comp.GetCarriedItem()
        if not itemDict:
            return False
        name = itemDict.get('itemName') or itemDict.get('newItemName')
        return name == modConfig.DebugStickItemName

    def _isCreative(self, playerId):
        if not modConfig.RequireCreative:
            return True
        gameComp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
        return gameComp.GetPlayerGameType(playerId) == clientApi.GetMinecraftEnum().GameType.Creative

    def _canUse(self, playerId):
        if not self._isCreative(playerId):
            return False
        return self._isHost() or self.noOpSetting

    def _isHost(self):
        try:
            hostId = clientApi.GetHostPlayerId()
            if not hostId:
                return True
            return clientApi.GetLocalPlayerId() == hostId
        except Exception:
            return True

    def OnTickClient(self):
        pass

    def Update(self):
        pass

    def Destroy(self):
        pass
