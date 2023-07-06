#错误码 ---uart串口发送报文时使用
errorCode={
    "noReceive":-1, #未接收到报文
    "crcCheckSum":-2, #crc校验失败
    "revMessageError":-3,# 接收到的报文错误
    "messageLengthError":-4 #接收到的报文长度错误
}

#继电器的信号输出端口
DeviseCode={
    "Servo":0,  #舵机报警
    "RangeFinder":1, #测距仪报警
    "Thermometer":2,  #温度计报警
    "canDescend":4,  #可以下降信号
    "canNotDescend":5, #不能下降信号
    "measureComplete":6,  #测量完成信号
    "measureFailure":7  #测量失败信号
}

#粉仓的大小数据
FeedBucket={
    "radius":0.29,   #圆柱的半径
    "cylinderHigh":0.78, #圆柱的高度
    "coneHigh":0.4,    #圆锥的高度
    "rangeFinderLen":0.059,  #测距仪自身长度，这个不用更改
    "disOfRangefinder2circleCenter":0.078,  #测距仪到圆心的距离
    "disOfRangefinder2cylinderTop":0.1,  #测距仪到圆柱顶的高度距离
    "volume":0.2621   #空桶的体积。用扫一圈空桶的方法测量，可能比直接根据数据计算得出的更准确一点
}


