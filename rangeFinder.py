import uasyncio as asyncio


class RangeFinder:
    def __init__(self,id,distance,modbus) -> None:
        """初始化类RangeFinder

        Args:
            id (int): 设备id
            distance (int): 设备与主机之间的物理距离
        """
        self.addr=id
        self.distance=distance
        self.modbus=modbus

    async def write_(self,start_addr,data):
        """写入寄存器

        Args:
            start_addr (int):寄存器地址
            data (int): 写入的数据
        """
        RevMessFlag,ret_data =await self.modbus.send_cmd(self.addr,6,start_addr,data,self.distance,timeout=1)
        if RevMessFlag is True:
            return True
        else:
            raise Exception(" 测距仪写寄存器错误："+", flag="+str(RevMessFlag)+","+ret_data)

    async def read_(self,start_addr,data):
        """读取寄存器

        Args:
            start_addr (int): 寄存器的开始地址
            data (int): 要读取的字节数

        Returns:
            result(int):读取到的结果
        """
        RevMessFlag,ret_data =await self.modbus.send_cmd(self.addr,3,start_addr,data,self.distance,timeout=1)
        if RevMessFlag is True:
            #处理数据---测距仪的处理方式
            ret_data=self.modbus.checkMessLen(ret_data)
            data_len=int(ret_data[0])  
            factor=[1] #因子矩阵
            result=0 #结果
            for i in range(1,data_len):
                factor.append(256*factor[i-1])
            for i in range(1,data_len+1):
                result=result+ret_data[-i]*factor[i-1]
            return result
        else:
            raise Exception(" 测距仪读寄存器错误："+", flag="+str(RevMessFlag)+","+ret_data)
        
    async def get_cjy_dis(self):
        """得到该测距仪对象所测量的距离

        Returns:
            dis(float):距离，发生错误返回None 
        """
        res=await self.read_(16,1)
        if res==0:
            if await self.write_(16,1): #向寄存器写入1表示测量一次
                res=1
        if res==1:
            res=await self.read_(21,2)   #测量距离得到的结果要除10000
            dis=int(res)/10000
            return dis

