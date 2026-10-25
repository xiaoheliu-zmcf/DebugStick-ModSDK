# -*- coding: utf-8 -*-
#导入服务端API模块
import mod.server.extraServerApi as serverApi
#获取"服务端系统"的基类
ServerSystem = serverApi.GetServerSystemCls()
#导入配置文件
import modConfig


class DebugStickServerSystem(ServerSystem):
    def __init__(self, namespace, systemName):
        ServerSystem.__init__(self, namespace, systemName)
        self.playerSelected = {}
        self.playerNoOp = {}
        self.blockStateCache = {}
        self.ListenEvent()

    def ListenEvent(self):
        # 监听事件
        ns = serverApi.GetEngineNamespace()
        sys = serverApi.GetEngineSystemName()

        self.ListenForEvent(ns, sys, 'AddServerPlayerEvent', self, self.OnAddServerPlayer)
        self.ListenForEvent(ns, sys, 'ServerPlayerTryDestroyBlockEvent', self, self.OnTryDestroyBlock)

        self.ListenForEvent(modConfig.ModName, modConfig.client_system_name, modConfig.RightClickEventName, self, self.OnClientRightClick)
        self.ListenForEvent(modConfig.ModName, modConfig.client_system_name, modConfig.NoOpSettingEventName, self, self.OnNoOpSetting)


    def OnAddServerPlayer(self, args):
        playerId = args.get("id", "")
        self.playerSelected[playerId] = None
        self.playerNoOp[playerId] = False
        levelId = serverApi.GetLevelId()
        comp = serverApi.GetEngineCompFactory().CreateGame(levelId)
        comp.AddTimer(10.0, self.SendWelcomeMessage, playerId)
        comp.AddTimer(11.0, self.SendUsageMessage, playerId)

    def OnNoOpSetting(self, args):
        playerId = args.get('__id__', '') or args.get('playerId', '')
        if playerId:
            self.playerNoOp[playerId] = bool(args.get('noOpSetting', False))

    def OnClientRightClick(self, args):
        playerId = args.get('__id__', '') or args.get('playerId', '')
        if not playerId or not self._holdingDebugStick(playerId) or not self._hasPermission(playerId):
            return
        pos = (args.get('x'), args.get('y'), args.get('z'))
        dimensionId = self._getPlayerDimensionId(playerId)
        blockName = self._getBlockName(pos, dimensionId)
        self._cycleProperty(playerId, blockName, pos, dimensionId)

    def OnTryDestroyBlock(self, args):
        playerId = args.get('playerId', '')
        if not self._holdingDebugStick(playerId) or not self._hasPermission(playerId):
            return

        blockName = args.get('fullName', '')
        pos = (args.get('x'), args.get('y'), args.get('z'))
        dimensionId = args.get('dimensionId', 0)
        if not blockName or blockName == 'minecraft:air':
            return

        args['cancel'] = True
        args['spawnResources'] = False
        self._cycleValue(playerId, blockName, pos, dimensionId)


    def _cycleProperty(self, playerId, blockName, pos, dimensionId):
        stateMap = self._getBlockStateMap(blockName)
        if not stateMap:
            self._notify(playerId, '§c该方块没有可修改的方块状态。')
            return
        keys = sorted(stateMap.keys())
        cur = self.playerSelected.get(playerId)
        if cur in keys:
            nxt = keys[(keys.index(cur) + 1) % len(keys)]
        else:
            nxt = keys[0]
        self.playerSelected[playerId] = nxt
        values = stateMap[nxt]
        self._notify(playerId, '§a[属性] §f{0}  §7(可选: {1}§7)'.format(nxt, '/'.join(str(v) for v in values)))

    def _cycleValue(self, playerId, blockName, pos, dimensionId):
        stateMap = self._getBlockStateMap(blockName)
        if not stateMap:
            self._notify(playerId, '§c该方块没有可修改的方块状态。')
            return
        keys = sorted(stateMap.keys())
        sel = self.playerSelected.get(playerId)
        if sel not in keys:
            sel = keys[0]
            self.playerSelected[playerId] = sel
        values = stateMap[sel]
        if not values:
            return

        levelId = serverApi.GetLevelId()
        comp = serverApi.GetEngineCompFactory().CreateBlockState(levelId)
        states = comp.GetBlockStates(pos, dimensionId)
        if not states:
            self._notify(playerId, '§c无法读取该方块状态。')
            return

        cur = states.get(sel)
        if cur in values:
            idx = values.index(cur)
        else:
            idx = -1
        nxt = values[(idx + 1) % len(values)]

        states[sel] = nxt
        comp.SetBlockStates(pos, states, dimensionId)
        self._notify(playerId, '§a{0}§f: {1} §7-> §e{2}'.format(sel, cur, nxt))

    def _getBlockStateMap(self, blockName):
        if blockName in self.blockStateCache:
            return self.blockStateCache[blockName]

        levelId = serverApi.GetLevelId()
        comp = serverApi.GetEngineCompFactory().CreateBlockState(levelId)
        stateMap = {}
        for aux in range(64):
            try:
                states = comp.GetBlockStatesFromAuxValue(blockName, aux)
            except Exception:
                continue
            if not states:
                continue
            for k, v in states.items():
                if k not in stateMap:
                    stateMap[k] = []
                if v not in stateMap[k]:
                    stateMap[k].append(v)
        for k in stateMap:
            stateMap[k] = sorted(stateMap[k], key=lambda x: str(x))

        self.blockStateCache[blockName] = stateMap
        return stateMap


    def _isDebugStick(self, itemDict):
        if not itemDict:
            return False
        name = itemDict.get('itemName') or itemDict.get('newItemName')
        return name == modConfig.DebugStickItemName

    def _holdingDebugStick(self, playerId):
        comp = serverApi.GetEngineCompFactory().CreateItem(playerId)
        itemDict = comp.GetPlayerItem(serverApi.GetMinecraftEnum().ItemPosType.CARRIED, 0, False)
        return self._isDebugStick(itemDict)

    def _hasPermission(self, playerId):
        if modConfig.RequireCreative:
            gameComp = serverApi.GetEngineCompFactory().CreateGame(serverApi.GetLevelId())
            if gameComp.GetPlayerGameType(playerId) != serverApi.GetMinecraftEnum().GameType.Creative:
                return False
        if modConfig.RequireOperator and not self.playerNoOp.get(playerId, False):
            if playerId != serverApi.GetHostPlayerId():
                return False
        return True

    def _getPlayerDimensionId(self, playerId):
        try:
            comp = serverApi.GetEngineCompFactory().CreateDimension(playerId)
            return comp.GetEntityDimensionId()
        except Exception:
            return 0

    def _getBlockName(self, pos, dimensionId):
        comp = serverApi.GetEngineCompFactory().CreateBlockInfo(serverApi.GetLevelId())
        blockDict = comp.GetBlockNew(pos, dimensionId)
        if blockDict:
            return blockDict.get('name', '')
        return ''

    def _notify(self, playerId, msg):
        comp = serverApi.GetEngineCompFactory().CreateGame(playerId)
        comp.SetOneTipMessage(playerId, msg)

    def SendWelcomeMessage(self, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, modConfig.WelcomeMessage, '§a')

    def SendUsageMessage(self, playerId):
        comp = serverApi.GetEngineCompFactory().CreateMsg(playerId)
        comp.NotifyOneMessage(playerId, modConfig.UsageMessage, '§f')

    def OnTickServer(self):
        pass

    def Update(self):
        pass

    def Destroy(self):
        pass
