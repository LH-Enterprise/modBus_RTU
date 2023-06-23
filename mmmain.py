import time
from machine import WDT,Pin
import gc
import uasyncio as asyncio

from CJY import RangeFinder
from WDJ import Thermometer
from Servo import Servo
from Relay import Relay
from modbusDevise import modbusDevise
from parameter import DeviseCode,FeedBucket
import volumeAlgorithm 
import log


modbus=modbusDevise(0,9600,12, 13, 8, None, 1)
relay=Relay(3,50,modbus)
servo=Servo(1,115200, 4, 5, 8, None, 1,50)
rangefinder=RangeFinder(1,50,modbus)  
thermometer=Thermometer(2,50,modbus)
erha = WDT(timeout=5000)
reachPosition = Pin(14, Pin.IN) #到达位置信号
dropFinish = Pin(15, Pin.IN) #下降完成信号


#还需要根据舵机位置实际情况初始化调整舵机角度
async def init_move(pos,timeout=5):
    print("init_move start...")
    flag=0
    while timeout>0:
        start_time = time.time() 
        await servo.turn2PosInTime(pos,100)
        pos0=await servo.get_currentPos()
        # print("pos0:",pos0)
        if(abs(pos0-pos)<=2):
            dis0 = await rangefinder.get_cjy_dis() 
            print("dis0:",dis0)
            if dis0 is not None and abs(dis0+FeedBucket["rangeFinderLen"]-(FeedBucket["radius"]-FeedBucket["disOfRangefinder2circleCenter"]))<0.02:
                print("init_move finishing...")
                return True
            else:
                flag=-2
        else:
            flag=-1   
        end_time = time.time()  
        timeout = timeout-(end_time - start_time)  # 计算函数执行时间
    return flag


def record_data(ds,filepath):
    with open(filepath, 'a') as f:
        current=time.time()
        f.write('['+ str(current) +']'+ str(ds) +'\n')
    

async def true_getdis(pos,timeout=5):
    #不停发指令让它转，转到了pos，再测量距离,返回距离
    while timeout>0: 
        start_time = time.time() 
        await servo.turn2PosInTime(pos,100)  #0.4s
        current_pos=await servo.get_currentPos()
        if(abs(current_pos-pos)<=2):
            dis = await rangefinder.get_cjy_dis() 
            print("转到角度",current_pos)
            print("dis:",dis)
            return dis,current_pos
        end_time = time.time()  
        timeout = timeout-(end_time - start_time)  # 计算函数执行时间
    return None,None

async def scan_getV(pos0):
    ds={}
    try:
        start_time = time.time() 
        flag=await init_move(pos0) #输入参数
        print("flag:",flag)
        if(flag==-1):
            await relay.writeOneRelay(DeviseCode["Servo"],True) #报警
            raise Exception("无法转动到初始位置pos0")
        if(flag==-2):
            await relay.writeOneRelay(DeviseCode["RangeFinder"],True) #报警
            raise Exception("位置校正失败，该位置pos不是指向桶壁的0°或参数有误")
        dis0 = await rangefinder.get_cjy_dis()
        ds['0']=dis0
        cnt_None=0    #测量为空的次数（连续）超过3就报警
        for i in range(50):
            #转动1.2度,测距
            if(cnt_None>3): 
                await relay.writeOneRelay(DeviseCode["Servo"],True)  #报警
                raise Exception("舵机转动出错")
            pos=pos0+5*(i+1)
            dis,pos=await true_getdis(pos) 
            if(dis!=None and pos!=None):
                angle=str((pos-pos0)/5*1.2)
                ds[angle]=dis
                cnt_None=0
            else:
                cnt_None=cnt_None+1
        #记录到文件中
        filepath='data_6_23.txt'
        record_data(ds,filepath)

        V=volumeAlgorithm.caculateV(ds)
        end_time = time.time()  
        t = end_time - start_time
        print("escape_time:",t) #255s
        print("V:",V)
        return V
    except Exception as e:
        print(e)
        # log.loginfo("scan_getV",4,str(e))
    finally:
        await asyncio.sleep_ms(50)

async def monitorTemperature():
    try:
        tempera=await thermometer.getTemperature()
        print("temperature:",tempera)
        return tempera
    except Exception as e:
        log.loginfo("monitorTemperature",4,str(e))
    finally:
        await asyncio.sleep_ms(50)
            

async def monitorReachPosition(flag):
    while flag:
        try:
            if reachPosition.value() == 1: 
                #测量粉仓是否满了
                print("reach Position")
                dis = await rangefinder.get_cjy_dis()
                if dis-FeedBucket["disOfRangefinder2cylinderTop"]<0.05:
                    #粉仓满了,怎么做？
                    pass
                else:
                    #粉仓没满，可以下降
                    await relay.writeOneRelay(DeviseCode["startDrop"],True)
        except Exception as e:
            log.loginfo("ReachPosition",4,str(e))
        finally:
            await asyncio.sleep_ms(50)
        

async def monitorDropFinish(flag):
    while flag:
        try:
            if dropFinish.value()==1:
                #开始测量
                print("drop finish......")
                results = await asyncio.gather(monitorTemperature(), scan_getV(pos0=85))
                print("results:",results) #数据传给谁？
                print("measuredFinish.....")
                await relay.writeOneRelay(DeviseCode["measuredFinish"],True)
        except Exception as e:
            log.loginfo("monitorDropFinish",4,str(e))
        finally:
            await asyncio.sleep_ms(50)


async def testDevise():
    try:
        # await relay.writeOneRelay(0,True) #开启0号继电器
        pos0=80
        await servo.turn2PosInTime(pos0,200) 
        for i in range(50):
            pos=pos0+i*5
            angle=await servo.get_currentPos()
            print("angle",angle)
            await servo.turn2PosInTime(pos,200) 
            dis = await rangefinder.get_cjy_dis()
            print("dis:",dis)
            # tempera=await thermometer.getTemperature()
            # print("temperature:",tempera)
            await asyncio.sleep(2)
        return pos0
    except Exception as e:
        print(e)

# async def test(flag):
#     while flag:
#         try:
#             if dropFinish.value()==1:
#                 print("drop finish......")
#                 results = await asyncio.gather(monitorTemperature(), testDevise())
#                 print("results:",results)
#                 print("measuredFinish.....")

#             await asyncio.sleep(2)
#         except Exception as e:
#                 print(e)
#         finally:
#             await asyncio.sleep_ms(50)

async def main():
    #先把继电器所有开关都关闭
    await relay.writeAllRelay(False)
    ReachPositionFlag=True
    dropFinishFlag=True
    mainFlag=True

    asyncio.create_task(monitorReachPosition(ReachPositionFlag))
    asyncio.create_task(monitorDropFinish(dropFinishFlag))
    # asyncio.create_task(testDevise(mainFlag))
    
    while mainFlag:
        await asyncio.sleep(2)
        erha.feed()
        gc.collect()
        print("内存占用："+str(gc.mem_alloc()/gc.mem_free()))
        # print("memery free:", gc.mem_free(), "memery alloc:", gc.mem_alloc())
        
try:
    asyncio.run(main())
except KeyboardInterrupt:
    mainFlag=False
    ReachPositionFlag=False
    dropFinishFlag=False



