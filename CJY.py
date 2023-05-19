from machine import WDT
import uasyncio as asyncio
import gc
import lds

md=lds.modbusDevise(9600,0, 1, 8, None, 1)

async def write_(addr,start_addr,data,distance):
    flag,ret_data =await md.send_cmd(addr,6,start_addr,data,distance,5)
    if  flag!=0:
        print(ret_data)
        print("请检查设备...")
    else:
        print(ret_data)

async def read_(addr,start_addr,data,distance):
    flag,ret_data =await md.send_cmd(addr,3,start_addr,data,distance,timeout=5)
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
        print("result=",result)
        return result


async def get_cjy1_dis():
    dis=500
    res=await read_(1,16,1,dis)
    if res==1:
        res=await read_(1,21,2,dis)   #测量距离得到的结果要除10000
        print("dis:",int(res)/10000)
    elif res==0:
        await write_(1,16,1,dis) #向寄存器写入1表示测量一次
        res=await read_(1,21,2,dis)   #读取距离寄存器的数据
        print("dis:",int(res)/10000)
    else:
        print("error")    


async def main():
    asyncio.create_task(get_cjy1_dis())
    while True:
        await asyncio.sleep(2)
        erha.feed()
        gc.collect()
        print("memery free:", gc.mem_free(), "memery alloc:", gc.mem_alloc())
        

erha = WDT(timeout=5000)
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
