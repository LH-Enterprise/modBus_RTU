from machine import WDT
import CJY
import Servo
import uasyncio as asyncio
import gc
import math

def processDS(ds,r,d,l):
    """处理数据列表,剔除异常数据和空数据
    （利用来回扫描得来的两组数据进行处理）

    Args:
        ds (list): 距离
        r (int): 圆柱体半径r
        d (int): 测距仪距离圆心位置d，若在圆柱圆心左侧则为负，圆心右侧则为正。
        l(int):测距仪长度l
    Returns:
        ds():返回一个180个元素的数组。若为None，则该组数据废了，需要重新测量
    """
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
        elif ds[i]==None and ds[360-i+1]:
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

    return ds[:180] #截取前180个元素返回

def Add_getV(result,r,h,d,l):
    """求粉料体积
    Args:
        result (_type_): _description_
        r (int): 圆柱体半径r
        h (int): 圆柱体高度h
        d (int): 测距仪距离圆心位置d，若在圆柱圆心左侧则为负，圆心右侧则为正。
        l(int):测距仪长度l

    Returns:
        V(float): 体积
    """
    #计算过程中的精度处理
    ds=processDS(result,r,d,l)

    #分离筒壁与粉料的距离数据,将到桶壁的距离置为0

    # 桶底最大的角度是r+d/h=tan(0)
    alpha=math.atan(r+d/h)
    alpha = math.degrees(alpha) #这个角度代表桶壁到测距仪的最大角度，不可能超过这个角度
    for i in range(len(ds)): 
        if i<alpha:#左半边数据
            angle = math.radians(i)
            e = ds[i]+l-ds[0]/math.cos(angle) 
            if abs(e) >= 0.03: #误差 0.03m
                ds[i]=0
        elif i>(180-alpha):#右半边数据
            angle=math.radians(180-i)
            e=ds[i]+l-ds[-1]/math.cos(angle)
            if abs(e) >= 0.03: #误差 0.03m
                ds[i]=0
    #求出粉料顶端到桶底的高度列表
    highs=[] # 粉料顶端到桶底的高度列表
    lens=[] # （该点垂直于桶底的直线）到(测距仪垂直于桶底直线)的距离
    for i in range(len(ds)):
        if(ds[i]!=0):
            beta=math.radians(i)
            high=h-(ds[i]+l)*math.sin(beta)
            highs.extend(high)
            _len=(ds[i]+l)*math.cos(beta)
            lens.extend(_len)
        elif(ds[i]==0 and ds[i+1]!=0):
            left=i+1
        elif(ds[i]!=0 and ds[i+1]==0):
            right=i

    #求出高度列表中长方体的体积并相加
    sumV=0
    for i in range(right-left+1):
        dx=lens[i+1]-lens[i]
        len0=abs(lens[i]-d) #到圆心的距离
        dy=2*math.sqrt(r**2 - len0**2)
        dh=(highs[i+1]+highs[i])/2
        dv=dx*dy*dh
        sumV+=dv
    return sumV



# async def main():
#     task1=asyncio.create_task(CJY.monitor(60,0.34))#60s扫一周，测量180下.一度测一次，一度花费0.34s.
#     task2=asyncio.create_task(Servo.scan())#扫一圈

#     result=await asyncio.wait_for(task1,timeout=130)

#     Add_getV(result)

#     while True:
#         await asyncio.sleep(2)
#         erha.feed()
#         gc.collect()
#         print("memery free:", gc.mem_free(), "memery alloc:", gc.mem_alloc())
        

# erha = WDT(timeout=5000)
# asyncio.run(main())

ds=[2 ,2.1 ,2.2 ,2.3 ,2.4 ,2.5 ,2.4 ,2 ]
V=Add_getV(ds,2,6,-0.5,0)
print(V)
















