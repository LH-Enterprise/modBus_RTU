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

#需要根据舵机位置实际情况初始化调整舵机角度
pos0=85 #角度为0度时舵机的值   参数根据实际情况调整， 建议调整到100左右，安装时调整、因为转动的角度最大不超过1000.
signals=[0,0,0,0,0]  #接收信号的状态  plc发给单片机的信号
status=[0,0,0,0]  #输出信号的状态 分别代表继电器的四个口


async def init_move(timeout=5):
    """初始化调整角度

    Args:
        timeout (int, optional): 初始化的最长时间，超时则返回错误码. Defaults to 5.

    Returns:
        flag: 若正确则返回true，错误返回flag
    """
    print("init_move start...")
    flag=0
    while timeout>0:
        start_time = time.time() 
        await turnServo.turn2PosInTime(pos0,100)
        currentPos=await turnServo.get_currentPos()
        #当前角度是否为pos0
        if(abs(currentPos-pos0)<=2):
            dis0 = await rangefinder.get_cjy_dis() 
            print("dis0:",dis0)
            #判断该角度测得的（距离+测距仪长度）是否为（半径-测距仪到圆心的距离）
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
    """将ds数据记录到filepath中

    Args:
        ds (dict): 距离字典，键为角度，值为距离
        filepath (str): 文件名
    """
    with open(filepath, 'a') as f:
        current=time.time()
        f.write('['+ str(current) +']'+ str(ds) +'\n')
    

async def true_getdis(pos,timeout=5):
    """转到了pos，再测量距离,返回角度和距离

    Args:
        pos (int): 想要转到的角度
        timeout (int, optional): 转动时间最长不超过5秒，若超时了转不到该位置则返回None. Defaults to 5.

    Returns:
        dis,current_pos:该点测得的距离和实际转到的角度
    """
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
    """转动一圈，测量150个点，记录到文件中，并根据点计算体积

    Raises:
        Exception: ("无法转动到初始位置pos0")
        Exception: ("位置校正失败，该位置pos不是指向桶壁的0°或参数有误")
        Exception: ("舵机转动出错")

    Returns:
        V(float): 计算得到的体积
    """
    ds={}
    start_time = time.time() 
    flag=await init_move()   #初始化转动位置调整
    print("flag:",flag) 
    if(flag==-1):
        await relay.writeOneRelay(DeviseCode["Servo"],True) #报警
        raise Exception("无法转动到初始位置pos0")
    if(flag==-2):
        await relay.writeOneRelay(DeviseCode["RangeFinder"],True) #报警
        raise Exception("位置校正失败，该位置pos不是指向桶壁的0°或参数有误")
    dis0 = await rangefinder.get_cjy_dis()
    ds['0']=dis0
    cnt_None=0    #测量为空的次数（连续）
    for i in range(150):
        #转动1.2度,测距
        if(cnt_None>3):  #测量为空的次数（连续）超过3就报警
            await relay.writeOneRelay(DeviseCode["Servo"],True)  #报警
            raise Exception("舵机转动出错")
        currentPos=pos0+5*(i+1)
        dis,currentPos=await true_getdis(currentPos)  #转动到指定位置
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

    #计算体积
    V=volumeAlgorithm.caculateV(ds)
    end_time = time.time()  
    t = end_time - start_time
    print("escape_time:",t) #160s
    print("V:",V)
    return V

async def monitorTemperature():
    """检测温度

    Returns:
        tempera（float）: 温度计测量温度
    """
    tempera=await thermometer.getTemperature()
    print("temperature:",tempera)
    return tempera
            
async def ReachPositionIsFull():
    """到达位置测量粉仓是否满，是否可以下降
    """
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
    """下降后测量体积和温度
    """
    try:
        #开始测量
        results = await asyncio.gather(monitorTemperature(), scan_getV())
        print("results:",results)     #数据上传云平台    #result包括体积和温度
        print("measured  Finish.....")
        await relay.writeOneRelay(DeviseCode["measureComplete"],True)   #测量完成发信号
    except Exception as e:
        log.loginfo("monitorDropFinish",4,str(e))  
        #测量失败
        await relay.writeOneRelay(DeviseCode["measureFailure"],True)   #测量失败发信号
    finally:
        await asyncio.sleep_ms(50)
        await relay.writeAllRelay(False)#流程结束，把所有输出信号都关了


async def monitoringSignal(flag):
    """监视信号，和plc交互.具体参照信号表

    Args:
        flag (bool): 协程开关
    """
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
            #监视信号，刷新两个信号表
            print("signals:",signals)
            print("status:",status)
            
            #这端逻辑未通过测试，要和PLC配合起来，不确定是否有问题。
            if signals[-1]==0: #未下降
                if signals[0]==1 or signals[1]==1 or signals[2]==1 or signals[3]==1:
                    if status[0]==0 and status[1]==0 and status[2]==0 and status[3]==0:
                        await ReachPositionIsFull()
                        # print("ReachPositionIsFull()....")
                        # await asyncio.sleep(2)
                    elif status[0]==1 or status[1]==1:
                        await asyncio.sleep_ms(500) #监听状态

                elif signals[0]==0 and signals[1]==0 and signals[2]==0 and signals[3]==0:
                    await relay.writeAllRelay(False)  #流程结束，回到初始状态
                    # status=[[0]*4]
            elif signals[-1]==1:#下降完成
                if signals[0]==1 or signals[1]==1 or signals[2]==1 or signals[3]==1:
                    if status[0]==1 and status[1]==0 and status[2]==0 and status[3]==0:
                        FeedBucketID=signals.index(1)  #粉仓ID
                        await DropFinishMeasured()
                        # print("DropFinishMeasured()....")
                        # await asyncio.sleep(2)
                    elif status[2]==1 or status[3]==1:
                        await asyncio.sleep_ms(500) #监听状态
                else:
                    print("error")
        except Exception as e:
            log.loginfo("monitoringSignal",4,str(e))
        finally:
            await asyncio.sleep_ms(50)


async def testDevise():
    """该函数与项目无关，但可以用来测量接线是否正确。
    """
    try:
        await relay.writeOneRelay(0,True) #开启0号继电器
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
            await asyncio.sleep(1)
    except Exception as e:
        print(e)


async def main():
    #先把继电器所有开关都关闭
    await relay.writeAllRelay(False)

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
    dropFinishFlag=False



