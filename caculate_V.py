import math


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
        d (int): 测距仪距离圆心位置d

    Returns:
        lens(list): 长度列表。（该点垂直于桶底的直线）到(圆柱圆心)的距离
        highs(list): 粉料顶端到桶底的高度列表
        left(int): 左角度界限（桶壁与粉料的分界线）
        right(int): 右角度界限（桶壁与粉料的分界线）
    """
    #####################################################更改角度
    # 桶底最大的角度是 h/(r-d)=tan(0)
    e=0.01 #误差参数，可调节
    highs=[]
    lens=[] 
    left,right=0,len(ds) #左右边界角度
    alpha=math.atan(h/(r-d))   #81
    alpha = math.degrees(alpha)/1.2 #这个角度代表左侧桶壁到测距仪的最大角度，不可能超过这个角度
    beta=math.atan(h/(r+d))
    beta=math.degrees(beta)/1.2  #这个角度代表右侧桶壁到测距仪的最大角度，不可能超过这个角度
    len0,len1=ds[0],ds[0]

    for i in range(1,len(ds)): 
        angle=math.radians(i*1.2)
        high=h- ds[i]*math.sin(angle)
        if i<alpha:#左半边数据
            len1=(ds[i])*round(math.cos(angle),4)
            err1=abs(len0-(r-d))
            err2=abs(len1-(r-d))
            if err1 <= e and err2>= e: 
                left=i-1
                lens.append(len0+d)
                high0=h - ds[left]*math.sin(math.radians(left*1.2))
                highs.append(high0)
                highs.append(high)
            elif err1>=e and err2>=e: 
                lens.append(len0+d)
                highs.append(high)
        elif i>(150-beta):#右半边数据
            len1=(ds[i])*round(math.cos(angle),4)  # 超过90°len1是负的
            err1=abs(-len0-(r+d)) 
            err2=abs(-len1-(r+d))
            if err1 >= e and err2<= e: 
                right=i-1
                lens.append(len0+d)
                lens.append(len1)
                highs.append(high)
            elif err1>=e and err2>=e:  
                lens.append(len0+d)
                highs.append(high)
        else:#中间段数据
            lens.append(len0+d)
            highs.append(high)
            if(i==75): len1=0
            else: len1= ds[i]*math.cos(angle)
            
        len0=len1 #len0和len1向后移动一位
    return lens,highs,left,right

def calculous(highs,lens,r,d):
    """用微积分的方法计算体积

    Args:
        highs (list): 粉料顶端到桶底的高度列表
        lens (list): （该点垂直于桶底的直线）到(圆柱圆心)的距离
        r (int): 圆柱体半径r
        d (int): 测距仪距离圆心位置d

    Returns:
        sumV: 体积
    """
    sumV=0
    err=lens[-2]-lens[-1] #lens[-1]右侧误差有多大
    if err>0.05:
        #只计算左半边数据，围着y轴绕一圈
        #找出最高点的index
        for i in range(len(highs)-1): 
            dx= abs(lens[i+1]-lens[i])  
            dy=2*3.1416*abs(lens[i])
            # dy=2*3.1416*abs(lens[i+1])
            # dh=(highs[i+1]+highs[i])/2 
            dh=highs[i]
            dv=dx*dy*dh
            sumV+=dv
            if(lens[i+1]<=0 and lens[i]>=0):
                break
    else:
        #求出高度列表中长方体的体积并相加
        for i in range(len(highs)-1):
            dx= abs(lens[i]-lens[i+1])
            dy=3.1416*abs(lens[i])
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

    # ds=processDS(ds,r,d,l)
    if(ds==None):
        return None  #数据出错，返回None

    #分离数据并返回高度列表highs和距离列表lens
    lens,highs,left,right=separate(ds,r,d,h)
    print("left",left)
    print("right",right)

    V=calculous(highs,lens,r,d)
    print("V",V)

    return V

