from machine import Pin, UART
import uasyncio as asyncio
import time


def loginfo(name,level,info):
    """设置日志输出格式，包含调用函数名、日志级别、日志信息

    Args:
        name (str): 调用函数名
        level (int): 日志级别 (1-DEBUG,2-INFO,3-WARNNING,4-ERROR,5-CRITICAL)
        info (str): 错误信息
    """
    levels_info=['DEBUG','INFO','WARNNING','ERROR','CRITICAL']
    level_info=levels_info[level-1]
    res= name +"--"+level_info+"--"+info
    with open('log.txt', 'a') as f:
        f.write(res+'\n')
    print(res)

def modbus_cmd(addr, func, start_addr, data):
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
    crc = crc16(cmd)
    # 将地址、功能码、起始地址、数据、crc校验码拼接成一个bytes
    cmd = addr + func + start_addr + data + crc
    # 将bytes转换为字符串
    cmd = hex2str(cmd)
    return cmd

def crc16(data):
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

def hex2str(data):
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
def str2hex(data):
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

class modbusDevise:
    def __init__(self,id,baudrate,tx,rx,bits,parity,stop) -> None:
        self.uart = UART(id, baudrate, tx=Pin(tx), rx=Pin(rx), bits=bits, parity=parity, stop=stop)
        self.uart_lock = asyncio.Lock() 
        
    #判断接收的报文data是否正确，返回ret_data
    def __rev(self,data,cmd):
        """判断接收的报文是否正确

        Args:
            data (hex): 接收到的报文数据
            cmd (str): 发送的报文命令

        Returns:
            flag (int):错误码
            retData (str):报文数据部分，若为空则报文错误
        """
        # print("rev",hex2str(data))#data是hex格式
        cmd=str2hex(cmd)
        #crc校验错误返回1
        crc = crc16(data[:-2])
        if(crc!=data[-2:]):

            return 1,"crc校验码错误"
        #报文出错：cmd+128 返回2
        if(data[1:2]!=cmd[1:2]):
            return 2,"报文出错cmd=cmd+128"
        
        func=3 #当读寄存器时，判断读到的数据格式对不对
        if data[1:2]==func.to_bytes(1, "little"):
            ret_data=data[2:-2] #hex格式 #剥离报文头尾
            # print("ret_data=",ret_data)
            data_len=int(ret_data[0])
            if len(ret_data)==data_len+1:   #判断数据格式是否正确
                flag=0 #正确返回0
                return flag,hex2str(ret_data) 
            else:
                return 3,"数据长度出错" #数据格式错误
            
        #全都没出错返回0表示正确
        flag=0
        return flag,"success"

    def __calculate_time(self,distance):
        """计算传输距离下正常等待时间

        Args:
            distance (int): 设备的物理距离

        Returns:
            int:时间，单位：秒
        """
        return distance/1000+0.05

    async def __uartSend(self,cmd,phyTime):
        """UART串口传输，发送报文与接收报文

        Args:
            cmd (str): 待发送命令
            phyTime (int): 等待报文回传的时间

        Returns:
            data(bytes): 接收到的报文（hex编码格式）
        """
        self.uart.write(b'')
        self.uart.read(self.uart.any())
        #发送命令
        await self.uart_lock.acquire()
        try:
            self.uart.write(str2hex(cmd))
            # print("cmd:",cmd)
        except Exception as e:
            loginfo("__uartSend",4,"cmd:"+cmd+'--发送指令失败：'+ str(e))
        finally:
            await asyncio.sleep(phyTime)
        data=""
        if self.uart.any():
            data = self.uart.read()
        else:
            loginfo("__uartSend",4,"cmd:"+cmd+'--接收指令失败：')
            data=None
        self.uart_lock.release()
        return data

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
            flag(int):错误码，0表示正确
            ret_data:若flag=0，则传回数据包，否则传回错误信息
        """
        cmd=modbus_cmd(addr,func,start_addr,data)
        phyTime=self.__calculate_time(distance)
        flag=-1 #错误标识
        while True:
            start_time = time.time() 
            if(timeout<=0):
                break
            retdata= await self.__uartSend(cmd,phyTime)
            if retdata!=None:
                flag,_result=self.__rev(retdata,cmd) #判断报文是否正确
            else:
                flag=-1
                _result="报文为空"
            if flag==0:
                return flag,_result   #ret_data传回数据包部分
            else:
                loginfo("__rev",4,"接收报文错误："+str(flag)+str(_result))
                #报错后重试
            end_time = time.time()  
            timeout = timeout-(end_time - start_time)  # 计算函数执行时间

        ret_data="回传报文错误:"+_result
        loginfo("send_cmd",4,"cmd:"+cmd+"...接收报文错误："+ret_data)
        return flag,ret_data #发送失败，传回错误信息


