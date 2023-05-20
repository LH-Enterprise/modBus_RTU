from machine import WDT
import uasyncio as asyncio
import gc
import lds

md=lds.modbusDevise(9600,0, 1, 8, None, 1)

class RangeFinder:
    def __init__(self,id,distance) -> None:
        """初始化类RangeFinder

        Args:
            id (int): 设备id
            distance (int): 设备与主机之间的物理距离
        """
        self.addr=id
        self.distance=distance
        

    async def write_(self,start_addr,data):
        """写入寄存器

        Args:
            start_addr (int):寄存器地址
            data (int): 写入的数据
        """
        flag,ret_data =await md.send_cmd(self.addr,6,start_addr,data,self.distance,timeout=5)
        if  flag!=0:
            print(ret_data)
            print("写入寄存器指令失败...")
        else:
            print(ret_data)

    async def read_(self,start_addr,data):
        """读取寄存器

        Args:
            start_addr (int): 寄存器的开始地址
            data (int): 要读取的字节数

        Returns:
            result(int):读取到的结果
        """
        flag,ret_data =await md.send_cmd(self.addr,3,start_addr,data,self.distance,timeout=5)
        if flag!=0:
            print(ret_data)
            return None
        else:
            #处理数据---测距仪的处理方式
            ret_data=lds.str2hex(ret_data)
            data_len=int(ret_data[0])  
            factor=[1] #因子矩阵
            result=0 #结果
            for i in range(1,data_len):
                factor.append(256*factor[i-1])
            for i in range(1,data_len+1):
                result=result+ret_data[-i]*factor[i-1]
            # print("result=",result)
            return result


    async def get_cjy_dis(self):
        """得到该测距仪对象所测量的距离

        Returns:
            dis(int):距离，发生错误返回None 
        """
        res=await self.read_(16,1)
        if res==0:
            await self.write_(16,1) #向寄存器写入1表示测量一次
            res=1
        if res==1:
            res=await self.read_(21,2)   #测量距离得到的结果要除10000
            if res!=None:
                dis=int(res)/10000
                print("dis:",dis)
                return dis
            else:
                return None
        else:
            print("error")
            return None    


async def monitor():
    """监测距离，每2s返回一次数据
    """
    c1=RangeFinder(1,500)
    # c2=RangeFinder(2,600)
    while True:
        d1 = await c1.get_cjy_dis()
        # d2 = await c2.get_cjy_dis()
        print("d1:",d1)
        await asyncio.sleep(2)


async def main():
    asyncio.create_task(monitor())
    while True:
        await asyncio.sleep(2)
        erha.feed()
        gc.collect()
        print("memery free:", gc.mem_free(), "memery alloc:", gc.mem_alloc())
        

erha = WDT(timeout=5000)
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
