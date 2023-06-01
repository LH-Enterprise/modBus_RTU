# from machine import WDT
# import gc
# import uasyncio as asyncio
import math

# import CJY
# from Servo import Servo
# import lds


# servo=Servo(1,50)
# rangefinder=CJY.RangeFinder(1,500)  

def processDS(ds,r,d,l):
    """处理数据列表,剔除异常数据和空数据,将数据全都加上测距仪长度
    （利用来回扫描得来的两组数据进行处理）

    Args:
        ds (list): 距离
        r (int): 圆柱体半径r
        d (int): 测距仪距离圆心位置d，
        l(int):测距仪长度l
    Returns:
        ds():返回一个180个元素的数组。若为None，则该组数据废了，需要重新测量
    """
    ##############################################更改角度
    # 若距离列表中超过6个None值，则测量失败
    if ds.count(None)>6:
        return None
    #处理空数据
    ds_len=len(ds)
    for i in range(ds_len):
        if ds[0]==None: ds[0]=r+d
        if ds[-1]==None: ds[-1]=r-d
        if ds[i]==None and ds[i-1]!=None and ds[i+1]!=None: #若某个位置未测量到，则取左右两个数据的平均值
            ds[i]=(ds[i-1]+ds[i+1])/2
        elif ds[i]==None and ds[ds_len-i-1]!=None:
            ds[i]=ds[ds_len-i-1]  #取对称的数据
    #处理异常数据 并加上测距仪的数据
    extra=ds[0]-(r+d) 
    for i in range(math.ceil(ds_len/2)):
        j=ds_len-i-1 #对称的index
        if abs(ds[i]-ds[j])>0.05:
            #判断是ds[i]还是ds[j]异常
            if abs(ds[i]-ds[i+1])>0.05: #ds[i]异常
                ds[i]=ds[j]+l
            if abs(ds[j]-ds[j+1])>0.05: #ds[j]异常不用管，反正后半部分也不要了
                ds[j]=ds[i] 
        else:#数据无异常，就加上测距仪的长度和误差大小
            ds[i]=ds[i]+l+extra  

    return ds[:150] #截取前180个元素返回

def separate(ds,r,d,h):
    """ 分离筒壁与粉料的距离数据,将到桶壁的距离置为0

    Args:
        ds (list): 距离列表
        r (int): 圆柱体半径r
        h (int): 圆柱体高度h
        d (int): 测距仪距离圆心位置d，

    Returns:
        ds: 距离列表，将到粉料的距离置为0了
    """
    #####################################################更改角度
    # 桶底最大的角度是 h/(r+d)=tan(0)
    alpha=math.atan(h/(r-d))   #81
    alpha = math.degrees(alpha)/1.2 #这个角度代表桶壁到测距仪的最大角度，不可能超过这个角度
    for i in range(1,len(ds)): 
        if i<alpha:#左半边数据
            angle = math.radians(i)
            e =ds[i]-ds[0]/math.cos(angle) 
            if abs(e) <= 0.01: #误差 0.005m
                ds[i]=0
        elif i>(150-alpha):#右半边数据
            angle=math.radians(180-i)
            e=ds[i]-ds[-1]/math.cos(angle)
            if abs(e) <= 0.01: #误差 0.005m
                ds[i]=0
    ds[0]=0
    ds[-1]=0
    return ds

def calculous(highs,lens,r,d):
    """用微积分的方法计算体积

    Args:
        highs (list): 粉料顶端到桶底的高度列表
        lens (list): （该点垂直于桶底的直线）到(测距仪垂直于桶底直线)的距离
        r (int): 圆柱体半径r
        d (int): 测距仪距离圆心位置d

    Returns:
        sumV: 体积
    """
    sumV=0
    _len=r+d #len[-1]应该在的位置
    if _len-lens[-1]>0.03:
        #只计算左半边数据，围着y轴绕一圈
        #找出最高点的index
        j =lens[0]
        for i in range(len(lens)):
            abs(lens[i]-)

        for i in range(j-1):
            dx= abs(lens[i+1]-lens[i])   
            len0=abs(lens[i]-d)  #到圆心的距离
            lens[i]=len0
            dy=3.1416*len0
            dh=(highs[i+1]+highs[i])/2 
            dv=dx*dy*dh
            sumV+=dv
    else:
        #求出高度列表中长方体的体积并相加
        for i in range(len(highs)-1):
            dx= abs(lens[i+1]-lens[i])   
            len0=abs(lens[i]-d)  #到圆心的距离
            lens[i]=len0
            dy=3.1416*len0
            dh=(highs[i+1]+highs[i])/2 
            dv=dx*dy*dh
            sumV+=dv
    return sumV

def caculateV(ds,r,h,d,l=0):
    """求粉料体积
    Args:
        result (list):测距仪的结果
        r (int): 圆柱体半径r
        h (int): 圆柱体高度h
        d (int): 测距仪距离圆心位置d
        l(int):测距仪长度l

    Returns:
        V(float): 计算得到的体积，若返回None,则说明
    """
    #计算过程中的精度处理
    # ds=processDS(ds,r,d,l)
    if(ds==None):
        return None  #数据出错，返回None

    ds=separate(ds,r,d,h)

    #求出粉料顶端到桶底的高度列表
    highs=[] # 粉料顶端到桶底的高度列表
    lens=[] # （该点垂直于桶底的直线）到(测距仪垂直于桶底直线)的距离
    for i in range(150):
        if(ds[i]!=0):
            beta=math.radians(i*1.2)
            high=h- ds[i]*math.sin(beta)
            if(i==90): llen=0
            else: llen=(ds[i])*math.cos(beta) # 超过90°lens是负的
            highs.append(high) 
            lens.append(llen) 

    V=calculous(highs,lens,r,d)
    return V


#还需要根据舵机位置实际情况初始化调整舵机角度
async def init_move(r,d):
    # 获取当前位置,自动对准桶壁的角度0°,返回当前位置
    result=servo.readCmd(28)
    #90°对应375
    pos=None
    if result[0]==0:
        pos=servo.processData(result[1]) #舵机的当前位置
        pos=pos-375  #pos减90°
        await servo.writeCmd(1,pos,1000)
    else:
        return None
    d1 = await rangefinder.get_cjy_dis()
    for i in range(10):
        if abs(d1-(r-d))<0.01:
            return pos
        elif abs(d1-(r+d))<0.01:
            # 旋转180°
            pos=pos+750 #pos加180°
            await servo.writeCmd(1,pos,1000)
            return pos
        else:#没转到合适的角度
            pos=pos+(i-5)
            await servo.writeCmd(1,pos,1000)
            d1 = await rangefinder.get_cjy_dis()
    pos=None
    return pos

async def scan_getV(r,h,d,l=0):
    # 获取当前位置,自动对准桶壁的角度0°
    pos=await init_move(r,d)
    if(pos!=None):
        ds=[]
        for i in range(150):
            #转动一度,测距
            pos=pos+i*5
            await servo.writeCmd(1,pos+i,1000)
            d = await rangefinder.get_cjy_dis()
            # sleep(0.4s)
            ds.append(d)
        for i in range(180):
            await servo.writeCmd(1,pos-i,1000)
            d = await rangefinder.get_cjy_dis()
            # sleep(0.4s)
            ds.append(d)
        # 算体积
        V=caculateV(ds,r,h,d,l)
        if(V==None):
            #测量的数据有问题
            lds.loginfo("caculateV",4,"测量数据有误，请重新测量")
        else:
            print("V",V)
    else:
        lds.loginfo("init_move",4,"舵机自动校准位置失败")

    # return V


#60s扫一周，测量180下.一度测一次，一度花费0.34s.
# async def main():
#     r,h,d=2,6,1 #圆柱的半径和高度
#     asyncio.create_task(scan_getV(r,h,d))

#     while True:
#         await asyncio.sleep(2)
#         erha.feed()
#         gc.collect()
#         print("memery free:", gc.mem_free(), "memery alloc:", gc.mem_alloc())
        
# servo=Servo(1,50)
# rangefinder=CJY.RangeFinder(1,500)  
# erha = WDT(timeout=5000)
# asyncio.run(main())



