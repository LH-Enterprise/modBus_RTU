from machine import WDT
import CJY
import Servo
import uasyncio as asyncio
import gc
import math

#圆柱体半径r，圆柱体高h，测距仪距离圆心位置d若在圆柱圆心左侧则为负，圆心右侧则为正,测距仪长度l
def Add_getV(ds,r,h,d,l):
    """剔除异常数据，还有空数据
    TODO
    """
    #分离筒壁与粉料的距离数据
    ds[0]=ds[0]+l
    ds[-1]=ds[-1]+l
    # extra=ds[0]-(r+d) #误差
    for i in len(ds):  # type: ignore
        # 桶底最大的角度是r+d/h=tan(0)
        if(i<):#左半边数据
            angle = math.radians(i)
            e = ds[i]+l-ds[0]/math.cos(angle) 
            if -0.03 <= e <= 0.03: #误差 0.03m
                ds[i]=0
        else:#右半边数据
            angle=math.radians(180-i)
            e=ds[i]+l-ds[-1]/math.cos(angle)
            if -0.03 <= e <= 0.03: #误差 0.03m
                ds[i]=0
    #找出圆锥顶，列表除0外最小的数


    #找出圆锥边缘，左右边缘做一个平均数

    #计算圆锥体积

    



async def main():
    task1=asyncio.create_task(CJY.monitor(60,0.34))#60s扫一周，测量180下.一度测一次，一度花费0.34s.
    task2=asyncio.create_task(Servo.scan())#扫一圈

    result=await asyncio.wait_for(task1,timeout=130)
    getV(result)

    while True:
        await asyncio.sleep(2)
        erha.feed()
        gc.collect()
        print("memery free:", gc.mem_free(), "memery alloc:", gc.mem_alloc())
        

erha = WDT(timeout=5000)
# asyncio.run(main())

ds=[2 ,2.1 ,2.2 ,2.3 ,2.4 ,2.5 ,2.4 ,2 ]
ds[-1]
getV(ds)
















