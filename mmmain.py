import time
from machine import WDT
import gc
import uasyncio as asyncio
import math

import caculate_V
import CJY
import Servo
import lds


#还需要根据舵机位置实际情况初始化调整舵机角度
async def init_move(r,d,l):
    # 获取当前位置,自动对准桶壁的角度0°,返回当前位置
    print("init_move start...")
    flag,result=await servo.readCmd(28)
    if(flag==0):
        pos=servo.processData(result)
        print("pos:",pos)
        pos=pos-375   #pos减90°---375
        await servo.writeCmd(1,pos,1000)
    else:
        return None
    e=0.02
    d1 = await rangefinder.get_cjy_dis()
    for i in range(10):
        if abs(d1+l-(r-d))<e:
            print("已校准位置。。。")
            return pos
        elif abs(d1+l-(r+d))<e:
            # 旋转180°
            pos=pos+750 #pos加180°
            await servo.writeCmd(1,pos,1000)
            print("旋转180°")
        else:#没转到合适的角度
            pos=pos+(i-5)*5
            await servo.writeCmd(1,pos,1000)
            d1 = await rangefinder.get_cjy_dis()
    pos=None
    print("finally pos:",pos)
    return pos

async def scan_getV(r,h,d,l=0):
    # 获取当前位置,自动对准桶壁的角度0°
    # pos=await init_move(r,d,l)
    ###################################
    # await servo.writeCmd(1,0,1000)  
 
    flag,result=await servo.readCmd(28)
    if(flag==0):
        pos=servo.processData(result)
        # print("pos0:",pos)
    else:
        pos=None
    ###################################
    if(pos!=None):
        ds=[]
        d0 = await rangefinder.get_cjy_dis()
        ds.append(d0)
        for i in range(150):
            #转动1.2度,测距
            start_time = time.time() 
            pos=pos+5
            await servo.writeCmd(1,pos,1000)  
            print("转到pos:",pos)
            d = await rangefinder.get_cjy_dis()
            end_time = time.time() 
            elapsed_time = end_time - start_time
            print("elapsed_time:",elapsed_time)
            # if(timeout<0.4):
            #     await asyncio.sleep(0.4-timeout) 
            await asyncio.sleep(2)
            print("===========================================")
            ds.append(d)
        print("ds:",ds)
        # 算体积
        # V=caculate_V.caculateV(ds,r,h,d,l)
        if(V==None):
            #测量的数据有问题
            lds.loginfo("caculateV",4,"测量数据有误，请重新测量")
        else:
            print("V",V)
    else:
        lds.loginfo("init_move",4,"舵机自动校准位置失败")

    # return V


#60s扫一周，测量180下.一度测一次，一度花费0.34s.
async def main():
    r,h,d=2,6,1 #圆柱的半径和高度
    l=0.05
    asyncio.create_task(scan_getV(r,h,d,l))
    # asyncio.create_task(init_move(r,d,l))
    # asyncio.create_task(CJY.monitor(10,0.5))
    while True:
        await asyncio.sleep(2)
        erha.feed()
        gc.collect()
        print("memery free:", gc.mem_free(), "memery alloc:", gc.mem_alloc())
        
servo=Servo.Servo(1,50)
rangefinder=CJY.RangeFinder(1,50)  

erha = WDT(timeout=5000)
asyncio.run(main())



