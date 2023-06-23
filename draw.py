import matplotlib.pyplot as plt
import numpy as np

def drawScatterPlot(points,left=0,right=1):
    # 提取数据点的横坐标和纵坐标
    x = [d[0] for d in points]
    y = [d[1] for d in points]

    # 创建一个新的图形对象
    fig, ax = plt.subplots()
    # 在坐标系上画出所有数据点和拟合曲线
    ax.scatter(x, y, color='red')
    # 在坐标系上连接各个数据点
    # ax.plot(x, y, color='gray') 

    # 标记特殊的点
    special_points = [points[left], points[right]]  
    special_x = [p[0] for p in special_points]
    special_y = [p[1] for p in special_points]

    ax.scatter(special_x, special_y, color='blue')

    # 设置坐标轴标签和标题
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_title('Scatter Plot')
    # 显示图形
    plt.show()

def __derivativeOf2point(x1, y1, x2, y2):
    """计算两个点之间函数的导数"""
    if(x2==x1):  
        return 9999
    else:
        k = (y2 - y1) / (x2 - x1)
        return k

def getDerivativeGroup(points):
    #求相邻两个点之间的导数列表
    
     # 提取数据点的横坐标和纵坐标
    x = [d[0] for d in points]
    y = [d[1] for d in points]
    kList=[]
    kmax,kmin,maxIndex,minIndex=0,0,0,0
    for i in range(2,len(points)-3):
        """计算两个点之间函数的导数"""
        k=0
        for j in range(i-2,i+2):
            k=k+__derivativeOf2point(x[j], y[j], x[i], y[i])
            
        k=k/j
        if(k>kmax):
            kmax=k
            maxIndex=i
        if(k<kmin):
            kmin=k
            minIndex=i
        kList.append((i,k))
    print(kList)
    print("kmax,maxIndex",kmax,maxIndex)
    print("kmin,minIndex",kmin,minIndex)
    return kList,minIndex,maxIndex


