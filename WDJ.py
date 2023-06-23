import uasyncio as asyncio
from parameter import errorCode

class Thermometer:
    def __init__(self,id,distance,modbus) -> None:
        """初始化类RangeFinder

        Args:
            id (int): 设备id
            distance (int): 设备与主机之间的物理距离
        """
        self.addr=id
        self.distance=distance
        self.modbus=modbus
   

    async def getTemperature(self):
        """得到温度计的温度

        Returns:
            temperature(int):温度值，发生错误抛出异常
        """
        flag,ret_data =await self.modbus.send_cmd(self.addr,func=4,start_addr=1024,data=1,distance=self.distance,timeout=1)
        if flag:
            # tempera=self.ProcessTemperaMeasure(ret_data)
            ret_data=self.modbus.checkMessLen(ret_data) #检查报文长度是否正确
            if ret_data==errorCode["messageLengthError"]:
                raise Exception("温度计messageLengthError")
            else:
                value = (ret_data[1] << 8) | ret_data[2]
                if value == 0x7FFF: #错误码
                    raise Exception("温度传感器损坏")
                if value & 0x8000: #补码转换
                    value = -(0x10000 - value)
                tempera=value/10
                return tempera
        else:
            raise Exception("温度计getTemperature错误："+", flag="+str(flag)+","+ret_data)





