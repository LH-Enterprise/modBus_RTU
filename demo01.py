import time

def read_():
    raise Exception(" 测距仪读寄存器错误：")
        

def get_cjy_dis():
    read_()

def main():
    while True:
        try:
            get_cjy_dis()
            time.sleep(1)
        except Exception as e:
            print(e)
            
      