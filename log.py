
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



