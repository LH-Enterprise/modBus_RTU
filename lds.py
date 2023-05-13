from machine import Pin, UART
import utime
import time

def modbus_cmd(addr, func, start_addr, data):
    # 将地址转换为16进制bytes
    addr = int(addr)
    addr = addr.to_bytes(1, "little")
    # 将功能码转换为16进制bytes
    func = int(func)
    func = func.to_bytes(1, "little")
    # 将起始地址转换为16进制bytes
    start_addr = int(start_addr)
    start_addr = start_addr.to_bytes(2, "big")
    # 将数据转换为16进制bytes
    data = int(data)
    data = data.to_bytes(2, "big")
    # 将地址、功能码、起始地址、数据拼接成一个bytes
    cmd = addr + func + start_addr + data
    # 计算crc校验码
    crc = crc16(cmd)
    # 将地址、功能码、起始地址、数据、crc校验码拼接成一个bytes
    cmd = addr + func + start_addr + data + crc
    # 将bytes转换为字符串
    cmd = hex2str(cmd)
    return cmd
def crc16(data):
    crc = 0xFFFF
    for i in range(len(data)):
        crc = crc ^ data[i]
        for j in range(8):
            if crc & 0x0001:
                crc = crc >> 1
                crc = crc ^ 0xA001
            else:
                crc = crc >> 1
    # 将crc转化成为16进制的byte，反转
    crc = crc.to_bytes(2, "little")
    return crc
def hex2str(data):
    data = data.hex()
    data = data.upper()
    data = data.replace(" ", "")
    data = data.replace("0X", "")
    data = data.replace("0x", "")
    data = data.replace("X", "")
    data = data.replace("x", "")
    data = data.replace(" ", "")
    return data
def str2hex(data):
    data = data.replace(" ", "")
    data = data.replace("0X", "")
    data = data.replace("0x", "")
    data = data.replace("X", "")
    data = data.replace("x", "")
    data = data.replace(" ", "")
    data = bytes.fromhex(data)
    return data
 
#判断接收的报文data是否正确，返回ret_data
def rev(data,cmd):
    # print("rev",hex2str(data))#data是hex格式
    cmd=str2hex(cmd)
    #crc校验错误返回1
    crc = crc16(data[:-2])
    if(crc!=data[-2:]):
        return 1,""
    #报文出错：cmd+128
    if(data[1:2]!=cmd[1:2]):
        return 2,""
    #数据部分的错误只能在设备处理数据时判断

    flag=0 #正确返回0
    return flag,hex2str(data[2:-2]) #剥离报文头尾

#计算传输距离下正常等待时间,单位：秒
def calculate_time(distance):
    return distance/1000+0.1

#addr从机地址，func功能码，start_addr寄存器地址, data数据，distance传输距离(米)，timeout等待超时
def send_cmd(addr,func,start_addr,data,distance,timeout=5):
    cmd=modbus_cmd(addr,func,start_addr,data)
    phy_time=calculate_time(distance)
    flag=-1 #错误标识
    while True:
        start_time = time.time() 
        #清除发送缓冲区和接收缓冲区
        uart.write(b'')
        uart.read(uart.any())
        #发送命令
        uart.write(str2hex(cmd))
        print("cmd",cmd)
        utime.sleep(phy_time)
        if(timeout==0):
            break
        if uart.any():
            data = uart.read()
            # print("data:",data)
        flag,ret_data=rev(data,cmd)#判断报文是否正确
        # print("flag=",flag,end=" ")
        # print("ret_data=",ret_data)
        if flag==0:
            # print("rev",hex2str(data))
            return flag,ret_data   #ret_data传回数据包部分
        else:
            print("接收报文错误：%d"% flag) #接收报文错误，重发报文
        end_time = time.time()  
        timeout = timeout-(end_time - start_time)  # 计算函数执行时间

    ret_data="回传报文错误:"+str(flag)
    return flag,ret_data #发送失败，传回错误信息


uart = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1), bits=8, parity=None, stop=1)


def write_(addr,start_addr,data):
    #distance由addr决定
    flag,ret_data = send_cmd(addr,6,start_addr,data,500)
    if  flag!=0:
        print(ret_data)
    else:
        #处理数据
        print("写寄存器成功")

def read_(addr,start_addr,data):
    #distance由addr决定
    flag,ret_data=send_cmd(addr,3,start_addr,data,500)
    if flag!=0:
        return ret_data
    else:
        #处理数据---测距仪的处理方式
        ret_data=str2hex(ret_data)
        data_len=int(ret_data[0])
        if len(ret_data)==data_len+1:  #判断数据格式是否正确
            factor=[1] #因子矩阵
            result=0 #结果
            for i in range(1,data_len):
                factor.append(256*factor[i-1])
            for i in range(1,data_len+1):
                result=result+ret_data[-i]*factor[i-1]
            # print("result=",result)
            return result
        else:
            return "回传报文错误：3"



write_(1,16,1)
res=read_(1,16,1)
print("result:",res)

res=read_(1,21,2)#测量距离得到的结果要除10000
print("dis:",int(res)/10000)


# cmd = modbus_cmd(1,6,16,1)
# print("cmd",cmd)
# uart.write(str2hex(cmd))
# utime.sleep(0.2)
# if uart.any():
#     data = uart.read()
#     print("rev",hex2str(data))

# cmd = modbus_cmd(1,3,16,1)
# print("cmd",cmd)
# uart.write(str2hex(cmd))
# utime.sleep(0.2)
# if uart.any():
#     data = uart.read()
#     print("rev",hex2str(data))#rev b'\x01\x03\x02\x00\x01y\x84'
#     print("rev",data[4])#rev 1
#     #当确定16号寄存器中数值为1
#     while data and data[4]==1:
#         uart.write(str2hex(cmd))
#         utime.sleep(0.2)
#         if uart.any():
#             data = uart.read()
#             # print("rev",data[4])

# cmd = modbus_cmd(1,3,21,2)
# print("cmd",cmd)
# uart.write(str2hex(cmd))
# utime.sleep(0.2)
# if uart.any():
#     data = uart.read()
#     print("rev",hex2str(data))
#     #0x0002 6e06=15.8886m
#     if data[0]==1 and data[1] == 3 and data[2] == 4:
#         dis = data[6] + data[5]*256 + data[4]*256*256 + data[3]*256*256*256
#         dis = dis/10000
#         print("dis",dis)
