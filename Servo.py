#!/usr/bin/python3
import time
from machine import Pin, UART
from parameter import errorCode
import uasyncio as asyncio

class Servo:
    def __init__(self,id,baudrate,tx,rx,bits,parity,stop,distance) -> None:
        """初始化类Servo

        Args:
            id (int): 设备id
            distance (int): 设备与主机之间的物理距离
        """
        self.id=id
        self.distance=distance
        self.uart = UART(id, baudrate, tx=Pin(tx), rx=Pin(rx), bits=bits, parity=parity, stop=stop)

    def __hex2str(self,data):
        """hex编码的bytes字节流转换成str，更便于人阅读

        Args:
            data (bytes): 要转换的数据

        Returns:
            data(str):转换后的数据
        """
        data = data.hex()
        data = data.upper()
        data = data.replace(" ", "")
        data = data.replace("0X", "")
        data = data.replace("0x", "")
        data = data.replace("X", "")
        data = data.replace("x", "")
        data = data.replace(" ", "")
        return data

    def __str2hex(self,data):
        """str转换成hex编码的bytes字节流，机器只支持hex编码格式

        Args:
            data (str): 要转换的数据

        Returns:
            data(bytes):转换后的数据
        """
        data = data.replace(" ", "")
        data = data.replace("0X", "")
        data = data.replace("0x", "")
        data = data.replace("X", "")
        data = data.replace("x", "")
        data = data.replace(" ", "")
        data = bytes.fromhex(data)
        return data

    def __calculate_time(self,distance):
        """计算传输距离下正常等待时间

        Args:
            distance (int): 设备的物理距离

        Returns:
            int:时间，单位：秒
        """
        return distance/1000+0.05


    def checkSum(self,buf):
        """计算校验和

        Args:
            buf (bytearray):要算校验和的字符串

        Returns:
            bytearray: 一字节的校验码
        """
        _sum = 0x00
        for b in buf:  #求和
            _sum += b
        _sum = _sum - 0x55 - 0x55  #去掉命令开头的两个 0x55
        _sum = ~_sum  #取反
        return 0xff & _sum  #取低8位

    def generateServoCmd(self, cmd, par1 = None, par2 = None):
        """生成控制舵机的命令

        Args:
            cmd (int): 指令值
            par1 (int, optional): 参数1(不同指令参数不同,具体指令参数见说明文档). Defaults to None.
            par2 (int, optional): 参数2. Defaults to None.
        
        Returns:
            buf(str): 返回指令字符串
        """
        buf = bytearray(b'\x55\x55')
        cmdlen = 3   #若命令是没有参数的话数据长度就是3
        buf1 = bytearray(b'')
        # 对参数进行处理
        if par1 is not None:
            cmdlen += 2  #数据长度加2
            par_1=bytearray([(0xff & par1), (0xff & (par1 >> 8))])
            buf1.extend(par_1)  #分低8位 高8位 放入缓存
        if par2 is not None:
            cmdlen += 2
            par_2=bytearray([(0xff & par2), (0xff & (par2 >> 8))])
            buf1.extend(par_2)  #分低8位 高8位 放入缓存
        par_3=bytearray([(0xff & self.id), (0xff & cmdlen), (0xff & cmd)])
        buf.extend(par_3)
        buf.extend(buf1) #追加参数

        ##计算校验和
        Csum = self.checkSum(buf)
        buf.append(Csum)  
        return self.__hex2str(buf)
        
    def revCheck(self,data):
        """判断接收的报文是否正确

        Args:
            data (hex): 接收到的报文数据

        Returns:
            retData (str):报文数据部分，若为空则报文错误
        """
        if(data==None):
            return errorCode["noReceive"]
        
        #crc校验错误
        crc = self.checkSum(data[:-1])
        if crc!=data[-1]:
            return errorCode["crcCheckSum"]
        
        #判断读到的数据格式对不对
        ret_data=data[2:-1] #hex格式 #剥离报文头尾
        data_len=int(ret_data[1])
        if len(ret_data)==data_len:   #判断数据格式是否正确
            return True
        else:
            return errorCode["messageLengthError"] #数据格式错误

    async def readCmd(self,cmd,par1=None,par2=None,timeout=1):
        """发出读指令，有数据返回

        Args:
            cmd (int): 指令值
            par1 (int, optional): 参数1(不同指令参数不同,具体指令参数见说明文档). Defaults to None.
            par2 (int, optional): 参数2. Defaults to None.
            timeout (int, optional):最长等待时间. Defaults to 1.

        Returns:
            flag(int):错误码，0表示正确
            ret_data:若flag=0，则传回数据包，否则传回错误信息
        """
        cmd=self.generateServoCmd(cmd,par1,par2)
        phyTime=self.__calculate_time(self.distance)
        flag,revMessage=0,None
        while timeout>0:
            start_time = time.time() 
            #清空读写缓冲区
            self.uart.write(b'')
            self.uart.read(self.uart.any())
            #发送指令
            self.uart.write(self.__str2hex(cmd))
            # print("cmd:",cmd)
            await asyncio.sleep(phyTime)
            if self.uart.any():
                revMessage = self.uart.read()
                # print("revMessage",revMessage)
            flag=self.revCheck(revMessage) #判断报文是否正确
            # print("flag",flag)
            if flag:
                return flag,revMessage
            else:
                #报错后重试
                print("servo send_cmd 错误：cmd="+cmd+", flag="+str(flag))
                end_time = time.time()  
                timeout = timeout-(end_time - start_time)  # 计算函数执行时间
        error = list(errorCode.keys())[-flag-1]
        return flag,error

        
    async def writeCmd(self,cmd,par1=None,par2=None,timeout=1):
        """发出写指令，无数据返回

        Args:
            cmd (int): 指令值
            par1 (int, optional): 参数1(不同指令参数不同,具体指令参数见说明文档). Defaults to None.
            par2 (int, optional): 参数2. Defaults to None.
            timeout (int, optional):最长等待时间. Defaults to 1.
        """
        cmd=self.generateServoCmd(cmd,par1,par2)
        phyTime=self.__calculate_time(self.distance)
        self.uart.write(b'')
        self.uart.read(self.uart.any())
        #发送命令
        self.uart.write(self.__str2hex(cmd))
        # print("cmd:",cmd)
        await asyncio.sleep(phyTime)
            
        
    def processData(self,data):
        """将报文中的信息提取出来

        Args:
            data (bytearrays): 要处理的数据字符数组（去掉报文头尾）

        Returns:
            value(int): 依据报文长度，可能返回一个数字，也可能返回两个数字
        """
        data=data[2:-1]
        if(data[1]==5):
            par=data[3:]
            par=bytes(reversed(par))
            #par转int型变量
            value = (par[0] << 8) | par[1]
            # 如果最高位是1，则为负数，需要进行符号扩展
            if value & 0x8000:
                value = -(0x10000 - value)
            return value
        elif(data[1]==7):
            par1=data[3:5]
            par1=bytes(reversed(par1))
            par2=data[5:7]
            par2=bytes(reversed(par2))
            value1 = (par1[0] << 8) | par1[1]
            value2 = (par2[0] << 8) | par2[1]
            # 如果最高位是1，则为负数，需要进行符号扩展
            if value1 & 0x8000:
                value1 = -(0x10000 - value1)
            if value2 & 0x8000:
                value2 = -(0x10000 - value2)
            return value1,value2
        elif (data[1]==4):
            value=data[2]
            # print("value",par)
            return value
        else:
            return None

    
# 舵机发送对应指令，即可转动。在控制舵机之前，需要设置好舵机的各项参数及id
#舵机控制角度范围0-1000对应0-240°
    async def get_currentPos(self):
        flag,result=await self.readCmd(28)
        if flag:
            pos=self.processData(result)
            return pos
        else:
            raise Exception("servo读取当前位置失败--"+"flag="+str(flag)+","+str(result))


    async def turn2PosInTime(self,pos,time):
        await self.writeCmd(1,pos,time)
        await asyncio.sleep_ms(time)
    

