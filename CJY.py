import uasyncio as asyncio
import time


class RangeFinder:
    def __init__(self,id,distance,md) -> None:
        """初始化类RangeFinder

        Args:
            id (int): 设备id
            distance (int): 设备与主机之间的物理距离
        """
        self.addr=id
        self.distance=distance
        self.md=md

    async def write_(self,start_addr,data):
        """写入寄存器

        Args:
            start_addr (int):寄存器地址
            data (int): 写入的数据
        """
        ret_data =await self.md.send_cmd(self.addr,6,start_addr,data,self.distance,timeout=0.3)
        if(ret_data==None):
            raise Exception("RangeFinder写入寄存器失败")
        return True


    async def read_(self,start_addr,data):
        """读取寄存器

        Args:
            start_addr (int): 寄存器的开始地址
            data (int): 要读取的字节数

        Returns:
            result(int):读取到的结果
        """
        message =await self.md.send_cmd(self.addr,3,start_addr,data,self.distance,timeout=0.3)
        if(message==None):
            raise Exception("RangeFinder读寄存器失败")
        #处理数据---测距仪的处理方式
        ret_data=self.md.checkMessLen(message)
        data_len=int(ret_data[0])  
        factor=[1] #因子矩阵
        result=0 #结果
        for i in range(1,data_len):
            factor.append(256*factor[i-1])
        for i in range(1,data_len+1):
            result=result+ret_data[-i]*factor[i-1]
        return result


    async def get_cjy_dis(self):
        """得到该测距仪对象所测量的距离

        Returns:
            dis(float):距离，发生错误返回None 
        """
        try:
            res=await self.read_(16,1)
            if res==0:
                if await self.write_(16,1): #向寄存器写入1表示测量一次
                    res=1
            if res==1:
                res=await self.read_(21,2)   #测量距离得到的结果要除10000
                dis=int(res)/10000
                return dis
        except Exception as e:
            raise Exception("测距仪测距失败--"+str(e))


async def monitor(t,timeout):
    """在ts内监测，在每timeout时间段内测量一次数据

     Args:
            start_addr (int): 寄存器的开始地址
            data (int): 要读取的字节数
    Returns:
            ds(list):返回距离列表，存储了t秒内检测到的数据
    """
    c1=RangeFinder(1,500)
    timeout1=timeout
    ds=[]#距离列表，存储了t秒内检测到的数据
    while t>0:
        start_time = time.time() 
        d1 = await c1.get_cjy_dis()
        ds.append(d1)
        end_time = time.time()  
        timeout = timeout-(end_time - start_time)  # 计算函数执行时间
        if timeout>0:
            await asyncio.sleep(timeout)
        t=t-timeout1
    print("ds.legth:",len(ds))
    print("ds:",ds)
    # return ds

