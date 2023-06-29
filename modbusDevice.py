from machine import Pin, UART
from parameter import errorCode
import uasyncio as asyncio
import time

class modbusDevice:
    def __init__(self,id,baudrate,tx,rx,bits,parity,stop) -> None:
        self.uart = UART(id, baudrate, tx=Pin(tx), rx=Pin(rx), bits=bits, parity=parity, stop=stop)
        self.uart_lock = asyncio.Lock() 
        
    def modbus_cmd(self,addr, func, start_addr, data):
        """生成modebus报文

        Args:
            addr (int): 设备id
            func (int): 功能码
            start_addr (int): 要读/写的寄存器地址
            data (int): 数据码
        Returns:
            str: 返回cmd报文
        """
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
        crc = self.crc16(cmd)
        # 将地址、功能码、起始地址、数据、crc校验码拼接成一个bytes
        cmd = addr + func + start_addr + data + crc
        # 将bytes转换为字符串
        cmd = self.hex2str(cmd)
        return cmd

    def crc16(self,data):
        """为data生成crc校验码

            Args:
                data (bytes): 数据，hex格式

            Returns:
            bytes:crc校验码，2字节长度
        """       
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

    def hex2str(self,data):
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
    
    def str2hex(self,data):
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

    #判断接收的报文data是否正确，返回ret_data
    def checkRevMess(self,data,cmd):
        """判断接收的报文是否正确

        Args:
            data (hex): 接收到的报文数据
            cmd (str): 发送的报文命令

        Returns:
            flag(int):错误码，若没问题返回True
        """
        if data is None:
            return errorCode["noReceive"]
        cmd_hex=self.str2hex(cmd)
        #crc校验错误返回
        crc = self.crc16(data[:-2])
        if(crc!=data[-2:]):
            return errorCode["crcCheckSum"]
        #报文出错：cmd+128 返回
        if(data[1:2]!=cmd_hex[1:2]):
            return errorCode["revMessageError"]
        return True
    
    #只针对读指令，针对需要处理返回数据的指令
    def checkMessLen(self,data):
        ret_data=data[2:-2] #hex格式 #剥离报文头尾
        data_len=int(ret_data[0])
        if len(ret_data)==data_len+1:   #判断数据格式是否正确
            return ret_data 
        else:
            return errorCode["messageLengthError"]

    def __calculate_time(self,distance):
        """计算传输距离下正常等待时间

        Args:
            distance (int): 设备的物理距离

        Returns:
            int:时间，单位：秒
        """
        return distance/1000+0.05


    #addr从机地址，func功能码，start_addr寄存器地址, data数据，distance传输距离(米)，timeout等待超时
    async def send_cmd(self,addr,func,start_addr,data,distance,timeout):
        """向总线上发送指令，并接收返回的数据包

        Args:
            addr (int): 设备id
            func (int): 功能码
            start_addr (int): 要读/写的寄存器地址
            data (int): 数据码
            distance (int): 设备的物理距离
            timeout (int): 最长等待时间

        Returns:
            flag(hex):传回数据报文
        """
        cmd=self.modbus_cmd(addr,func,start_addr,data)
        phyTime=self.__calculate_time(distance)
        RevMessFlag,revMessage,error=0,None,None
        while timeout>0:
            start_time = time.time() 
            #清空读写缓冲区
            self.uart.write(b'')
            self.uart.read(self.uart.any())
            await self.uart_lock.acquire()
            #发送指令
            self.uart.write(self.str2hex(cmd))
            # print("cmd:",cmd)
            await asyncio.sleep(phyTime)

            if self.uart.any():
                revMessage = self.uart.read()
            self.uart_lock.release()
            RevMessFlag=self.checkRevMess(revMessage,cmd) #判断报文是否正确

            if RevMessFlag is True:
                return RevMessFlag,revMessage
            else:
                #报错后重试
                print("send_cmd 错误：cmd="+cmd+", flag="+str(RevMessFlag))
                end_time = time.time()  
                timeout = timeout-(end_time - start_time)  # 计算函数执行时间
        for k, v in errorCode.items():
            if v == RevMessFlag:
                error=k
        # print("error:",error)
        return RevMessFlag,error


    