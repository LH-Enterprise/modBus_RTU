# 继电器

class Relay:
    def __init__(self,addr,distance,modbus) -> None:
        """初始化类RangeFinder

        Args:
            addr (int): 设备id
            distance (int): 设备与主机之间的物理距离
            modbus(modbusDevise):485总线
        """
        self.addr=addr
        self.distance=distance
        self.modbus=modbus

    async def writeOneRelay(self,registerAddr,isOn):
        # 0xFF00：继电器开启；0x0000：继电器关闭；
        registerAddr=int(registerAddr)
        directive=65280 if isOn else 0
        flag,message =await self.modbus.send_cmd(self.addr,func=5,start_addr=registerAddr,data=directive,distance=self.distance,timeout=1)
        if flag is not True:
            raise Exception("writeOneRelay error--"+", flag="+str(flag)+","+message)


    async def writeAllRelay(self,isOn):
        # 0xFF00：继电器开启；0x0000：继电器关闭；
        directive=65280 if isOn else 0
        flag,message =await self.modbus.send_cmd(self.addr,func=5,start_addr=255,data=directive,distance=self.distance,timeout=1)
        if flag is not True:
            raise Exception("writeAllRelay error--"+", flag="+str(flag)+","+message)


    async def getAllStatus(self):
        flag,message =await self.modbus.send_cmd(self.addr,func=1,start_addr=0,data=8,distance=self.distance,timeout=1)
        if flag is not True:
            raise Exception("RelaygetStatus error--"+", flag="+str(flag)+","+message)
        else:
            status = "{0:08b}".format(message[3])
            return status
