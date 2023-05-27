import uasyncio as asyncio
import time
import lds

md=lds.modbusDevise(0,9600,0, 1, 8, None, 1)


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
        flag,ret_data =await md.send_cmd(self.addr,6,start_addr,data,self.distance,timeout=0.3)
        if  flag!=0:
            lds.loginfo("CJY_write_",4,"写入寄存器指令失败..."+ret_data)
            print("写入寄存器指令失败..."+ret_data)
            return False
        else:
            # print("写入寄存器成功")
            return True

    async def read_(self,start_addr,data):
        """读取寄存器

        Args:
            start_addr (int): 寄存器的开始地址
            data (int): 要读取的字节数

        Returns:
            result(int):读取到的结果
        """
        flag,ret_data =await md.send_cmd(self.addr,3,start_addr,data,self.distance,timeout=0.3)
        if flag!=0:
            lds.loginfo("CJY_read_",4,"读取寄存器指令失败..."+ret_data)
            print("读取寄存器指令失败..."+ret_data)
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
            # print("read_result=",result)
            return result


    async def get_cjy_dis(self):
        """得到该测距仪对象所测量的距离

        Returns:
            dis(int):距离，发生错误返回None 
        """
        res=await self.read_(16,1)
        if res==0:
            if await self.write_(16,1): #向寄存器写入1表示测量一次
                res=1
            else:
                lds.loginfo("get_cjy_dis",4,"write_(16,1)error...")
                return None
        if res==1:
            res=await self.read_(21,2)   #测量距离得到的结果要除10000
            if res!=None:
                dis=int(res)/10000
                print("dis:",dis)
                return dis
            else:
                lds.loginfo("get_cjy_dis",4,"read_(21,2)error...")
                return None
        else:
            lds.loginfo("get_cjy_dis",4,"read_(16,1)||write_(16,1)error...")
            return None    


async def monitor(t,timeout):
    """在ts内监测，在每timeout时间段内测量一次数据

     Args:
            start_addr (int): 寄存器的开始地址
            data (int): 要读取的字节数

    """
    c1=RangeFinder(1,1)
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
    # return d
    print("ds.legth:",len(ds))
    print("ds:",ds)
    return ds


# async def main():
#     task1=asyncio.create_task(monitor(120,0.34))#60s扫一周，测量180下.一度测一次，一度花费0.34s.
#     task2=asyncio.create_task(Servo.scan())#扫一圈

#     result=await asyncio.wait_for(task1,timeout=130)
#     print("result:",result)
#        getV()

#     while True:
#         await asyncio.sleep(2)
#         erha.feed()
#         gc.collect()
#         print("memery free:", gc.mem_free(), "memery alloc:", gc.mem_alloc())
        

# erha = WDT(timeout=5000)
# asyncio.run(main())


