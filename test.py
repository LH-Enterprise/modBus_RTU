# signals: [0, 0, 0, 0, 0]
# status: [0, 0, 0, 0]
from parameter import DeviseCode

async def main():
    print("signals:",signals)
    print("status:",status)
    if signals[-1]==0: #未下降
        if signals[0]==1 or signals[1]==1 or signals[2]==1 or signals[3]==1:
            if status[0]==0 and status[1]==0 and status[2]==0 and status[3]==0:
                # await ReachPositionIsFull()
                print("ReachPositionIsFull()....")
                await asyncio.sleep(2)
                status[0]=1 
                # status[1]=1
            elif status[0]==1 or status[1]==1:
                await asyncio.sleep_ms(500) #监听状态

        elif signals[0]==0 and signals[1]==0 and signals[2]==0 and signals[3]==0:
            # await relay.writeAllRelay(False)  #流程结束，回到初始状态
            status=[[0]*4]
        else:
            print("signals error")
            
    elif signals[-1]==1:#下降完成
        if signals[0]==1 or signals[1]==1 or signals[2]==1 or signals[3]==1:
            if status[0]==1 and status[1]==0 and status[2]==0 and status[3]==0:
                # FeedBucketID=signals.index(1)  #粉仓ID
                # await DropFinishMeasured()
                print("DropFinishMeasured()....")
                await asyncio.sleep(20)
                status[2]=1 
                #status[3]=1
            elif status[2]==1 or status[3]==1:
                await asyncio.sleep_ms(500) #监听状态

        else:
            print("signals error")


signals = [0, 1, 0, 0, 1]
status=[0,0,0,0]
index = signals.index(1)
print(index)


