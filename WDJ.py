import uasyncio as asyncio

class Thermometer:
    def __init__(self,id,distance,md) -> None:
        """初始化类RangeFinder

        Args:
            id (int): 设备id
            distance (int): 设备与主机之间的物理距离
        """
        self.addr=id
        self.distance=distance
        self.md=md
   
    def ProcessTemperaMeasure(self,message):
        """将报文转换成温度数字

        Args:
            ret_data (hex): 报文的一部分，第一个元素表示长度

        Returns:
            tempera(int): 温度值，若为None则温度计损坏
        """
        ret_data=self.md.checkMessLen(message) #检查报文长度是否正确
        value = (ret_data[1] << 8) | ret_data[2]
        if value == 0x7FFF: #错误码
            raise Exception("温度传感器损坏")
        if value & 0x8000: #补码转换
            value = -(0x10000 - value)
        tempera=value/10
        return tempera

    async def getTemperature(self):
        """得到温度计的温度

        Returns:
            temperature(int):温度值，发生错误返回None 
        """
        try:
            message =await self.md.send_cmd(self.addr,func=4,start_addr=1024,data=1,distance=self.distance,timeout=1)
            tempera=self.ProcessTemperaMeasure(message)
            return tempera
        except Exception as e:
            raise Exception("温度计测温失败"+str(e))





