import time
from machine import WDT,Pin
import gc
import uasyncio as asyncio

from rangeFinder import RangeFinder
from thermometer import Thermometer
from servo import Servo
from relay import Relay
from modbusDevice import modbusDevice
from parameter import DeviseCode,FeedBucket
import volumeAlgorithm 
import log


modbus=modbusDevice(0,9600,0, 1, 8, None, 1)
relay=Relay(3,50,modbus)
turnServo=Servo(1,115200, 4, 5, 8, None, 1,50)
rangefinder=RangeFinder(1,50,modbus)  
thermometer=Thermometer(2,50,modbus)
erha = WDT(timeout=5000)
reachPosition1 = Pin(18, Pin.IN) #到达1号粉仓信号
reachPosition2 = Pin(19, Pin.IN) #到达2号粉仓信号
reachPosition3 = Pin(20, Pin.IN) #到达3号粉仓信号
reachPosition4 = Pin(21, Pin.IN) #到达4号粉仓信号
dropFinish = Pin(15, Pin.IN) #下降完成信号

pos0=85 #角度为0度时舵机的值
signals=[0,0,0,0,0] #接收信号的状态
status=[0,0,0,0] #输出信号的状态 


#还需要根据舵机位置实际情况初始化调整舵机角度
async def init_move(timeout=5):
    print("init_move start...")
    flag=0
    while timeout>0:
        start_time = time.time() 
        await turnServo.turn2PosInTime(pos0,100)
        currentPos=await turnServo.get_currentPos()
        if(abs(currentPos-pos0)<=2):
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
        await turnServo.turn2PosInTime(pos,100)  #0.4s
        current_pos=await turnServo.get_currentPos()
        if(abs(current_pos-pos)<=2):
            dis = await rangefinder.get_cjy_dis() 
            print("转到角度",current_pos)
            print("dis:",dis)
            return dis,current_pos
        end_time = time.time()  
        timeout = timeout-(end_time - start_time)  # 计算函数执行时间
    return None,None

async def scan_getV():
    ds={}
    start_time = time.time() 
    flag=await init_move() #输入参数
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
    for i in range(150):
        #转动1.2度,测距
        if(cnt_None>3): 
            await relay.writeOneRelay(DeviseCode["Servo"],True)  #报警
            raise Exception("舵机转动出错")
        currentPos=pos0+5*(i+1)
        dis,currentPos=await true_getdis(currentPos) 
        if(dis!=None and currentPos!=None):
            angle=str((currentPos-pos0)/5*1.2)
            ds[angle]=dis
            cnt_None=0
        else:
            cnt_None=cnt_None+1
    await turnServo.turn2PosInTime(pos0+5*75,100) #恢复到90度的状态
    #记录到文件中
    filepath='data_6_23.txt'
    record_data(ds,filepath)

    V=volumeAlgorithm.caculateV(ds)
    end_time = time.time()  
    t = end_time - start_time
    print("escape_time:",t) #160s
    print("V:",V)
    return V

async def monitorTemperature():
    tempera=await thermometer.getTemperature()
    print("temperature:",tempera)
    return tempera
            
async def ReachPositionIsFull():
    try:
        #测量粉仓是否满了
        cnt=5
        while cnt>0:
            pos=pos0+75*5 #转到90度
            cnt=cnt-1
            await turnServo.turn2PosInTime(pos,100)
            currentPos=await turnServo.get_currentPos()
            if abs(pos-currentPos)<=2:
                dis = await rangefinder.get_cjy_dis()
                if dis-FeedBucket["disOfRangefinder2cylinderTop"]<0.05:
                    #粉仓满了,发送不可以下降
                    await relay.writeOneRelay(DeviseCode["canNotDescend"],True)
                    break
                else:
                    #粉仓没满，发送可以下降
                    await relay.writeOneRelay(DeviseCode["canDescend"],True)
                    break
        if cnt<=0:
            raise Exception ("Servo turn error")
    except Exception as e:
        await relay.writeOneRelay(DeviseCode["Servo"],True)
        log.loginfo("ReachPositionIsFull",4,str(e))
    finally:
        await asyncio.sleep_ms(50)


async def DropFinishMeasured():
    try:
        #开始测量
        results = await asyncio.gather(monitorTemperature(), scan_getV())
        print("results:",results) #数据传给谁？
        print("measured  Finish.....")
        await relay.writeOneRelay(DeviseCode["measureComplete"],True)
    except Exception as e:
        log.loginfo("monitorDropFinish",4,str(e))
        #测量失败
        await relay.writeOneRelay(DeviseCode["measureFailure"],True)
    finally:
        await asyncio.sleep_ms(50)


## 使用功能函数    
async def monitoringSignal(flag):
    while flag:
        try:
            if reachPosition1.value() == 1:
                signals[0]=1
            else:
                signals[0]=0
            if reachPosition2.value()==1:
                signals[1]=1
            else:
                signals[1]=0
            if reachPosition3.value()==1:
                signals[2]=1
            else:
                signals[2]=0
            if reachPosition4.value()==1:
                signals[3]=1
            else:
                signals[3]=0
            if dropFinish.value()==1:
                signals[4]=1
            else:
                signals[4]=0
            relayStatus=await relay.getAllStatus()
            for i in range(4):
                if relayStatus[3-i]==1:
                    status[0]=1
                else:
                    status[0]=0
            
            print("signals:",signals)
            print("status:",status)

            if signals[-1]==0: #未下降
                if signals[0]==1 or signals[1]==1 or signals[2]==1 or signals[3]==1:
                    if status[0]==0 and status[1]==0 and status[2]==0 and status[3]==0:
                        # await ReachPositionIsFull()
                        print("ReachPositionIsFull()....")
                        await asyncio.sleep(2)
                        await relay.writeOneRelay(DeviseCode["canDescend"],True)
                        # await relay.writeOneRelay(DeviseCode["canNotDescend"],True)
                    elif status[0]==1 or status[1]==1:
                        await asyncio.sleep_ms(500) #监听状态

                elif signals[0]==0 and signals[1]==0 and signals[2]==0 and signals[3]==0:
                    # await relay.writeAllRelay(False)  #流程结束，回到初始状态
                    status=[[0]*4]
            elif signals[-1]==1:#下降完成
                if signals[0]==1 or signals[1]==1 or signals[2]==1 or signals[3]==1:
                    if status[0]==1 and status[1]==0 and status[2]==0 and status[3]==0:
                        # FeedBucketID=signals.index(1)  #粉仓ID
                        # await DropFinishMeasured()
                        print("DropFinishMeasured()....")
                        await asyncio.sleep(20)
                        await relay.writeOneRelay(DeviseCode["measureComplete"],True)
                        # await relay.writeOneRelay(DeviseCode["measureFailure"],True)
                    elif status[2]==1 or status[3]==1:
                        await asyncio.sleep_ms(500) #监听状态
                
        except Exception as e:
            log.loginfo("monitoringSignal",4,str(e))
        finally:
            await asyncio.sleep_ms(50)


async def testDevise():
    try:
        # await relay.writeOneRelay(0,True) #开启0号继电器
        pos0=80
        await turnServo.turn2PosInTime(pos0,200) 
        for i in range(50):
            pos=pos0+i*5
            angle=await turnServo.get_currentPos()
            print("angle",angle)
            await turnServo.turn2PosInTime(pos,200) 
            dis = await rangefinder.get_cjy_dis()
            print("dis:",dis)
            # tempera=await thermometer.getTemperature()
            # print("temperature:",tempera)
            await asyncio.sleep(2)
        return pos0
    except Exception as e:
        print(e)


async def main():
    #先把继电器所有开关都关闭
    await relay.writeAllRelay(False)
    # await relay.writeOneRelay(DeviseCode["measureComplete"],True)
    # status=await relay.getAllStatus()
    # print("status:",status[7-DeviseCode["measureComplete"]])

    dropFinishFlag=True
    mainFlag=True

    asyncio.create_task(monitoringSignal(dropFinishFlag))
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



