import math
import random
import mmmain

#分段函数
#固定点到分段函数的距离

#曲线： f(x)=-0.2 x* x+5
#转动180°, m=tan(0)
#直线：y=m(x-a)+f(a)
#切点

def curve_intersection(a, b, c, d, e):
    """计算直线 y = ax + b 和曲线 y = cx^2 + dx + e 的交点"""
    # 将方程 y = ax + b 和 y = cx^2 + dx + e 相减, 即 cx^2 + (d-a)x + (e-b) = 0，
    delta = (d-a)**2 - 4*c*(e-b)
    # 转化为一元二次方程求根问题
    if delta < 0:  # 无实数解
        return None
    elif delta == 0:  # 有一个实数解
        x_root = (a-d) / (2*c)
        y_root = a*x_root+b
        return x_root, y_root
    else:  # 有两个实数解
        x1 = ((a-d) - math.sqrt(delta)) / (2*c)
        x2 = ((a-d) + math.sqrt(delta)) / (2*c)
        y1 =  a*x1+b
        y2 =  a*x2+b
        return (x1, y1), (x2, y2)


def distance(x1, y1, x2, y2):
    """计算两个点之间的距离"""
    ds=math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    ds=round(ds, 3)
    return ds


#测距仪的位置(x0,y0)
def Emit_light(x0,y0,a, b, c,r):
    ds=[]
    for i in range(150):
        if(i!=75): #当i不等于90°时
            j=i*1.2
            beta=math.radians(j)
            m=math.tan(beta)
            # y=m(x-x0)+y0
            #计算该射线和曲线的交点
            roots=curve_intersection(m,y0-m*x0,a,b,c)
            if roots is None: #没有交点
                #计算该射线与直线的交点
                x1=-r if i<75 else r
                y1=m*(x1-x0)+y0
            elif isinstance(roots[0], tuple): #两个交点,一个交点的情况不存在
                if -r < roots[0][0] < r and (roots[1][0]<-r or roots[1][0]>r):
                    x1=roots[0][0]
                    y1=roots[0][1]
                elif -r< roots[1][0]< r and (roots[0][0]<-r or roots[0][0]>r):
                    x1=roots[1][0]
                    y1=roots[1][1]
                elif -r< roots[1][0]< r and -r<roots[0][0]<r :#两个点都在桶内
                    x1=roots[0][0] if abs(roots[0][0])>abs(roots[1][0]) else roots[1][0]
                    y1=m*(x1-x0)+y0
                else:#两个点都在桶外
                    x1=-r if i<75 else r
                    y1=m*(x1-x0)+y0
            else:#一个交点
                if -r<roots[0]<r:
                    x1=roots[0] 
                    y1=roots[1]
                else:
                    x1=-r if i<75 else r
                    y1=m*(x1-x0)+y0
            d=distance(x0,y0,x1,y1)
            ds.append(d)
        else: #m为正无穷   
            # 找出x=x0时，曲线的坐标y 
            y=a*(x0**2)+b*x0+c
            d=round(y0-y, 3)
            ds.append(d)
    return ds
    

a, b, c = -0.2, 0, 4  # 定义曲线的系数
r,h=2,6 #圆柱的半径和高度
x0,y0=-1,6 #测距仪坐标

ds=Emit_light(x0, y0, a, b, c,r)

V=mmmain.caculateV(ds,2,6,1,0)
print("V:",V)

# 随机将几个元素置为None
# list=[]
# for i in range(5):
#     num = random.randint(1, 180)
#     if num in list:
#         i=i-1
#     else:
#         list.append(num)
# for i in list:
#     ds[i]=None

# 输出结果
# print(ds)
# print("len(list):",len(ds))


