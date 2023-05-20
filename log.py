# utf-8
import logging
import logging.handlers
import os

def get_console_log(debug):
    """日志器的初始化，该日志写在控制台中，按要求返回一个日志器

    Args:
        debug (bool):是否设为debug级别，否则设为INFO级别

    Returns:
        logger: 返回一个logger对象
    """
    log = logging.getLogger('status_handle')
    if debug:
        log.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
    else:
        log.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_log = logging.StreamHandler()
    console_log.setFormatter(formatter)
    console_log.setLevel(logging.DEBUG)
    log.addHandler(console_log)
    return log


def get_file_log(name,debug):
    """日志器的初始化，该日志写在name的文件中，按要求返回一个日志器

    Args:
        name (str): 调用时传入调用页面的类名
        debug (bool):是否设为debug级别，否则设为INFO级别

    Returns:
        logger: 返回一个logger对象
    """
    # 如果log文件夹不存在 就创建log文件夹
    if not os.path.exists("log"): 
        os.mkdir("log")
    # 创建logger对象
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 创建文件Handler并添加到logger对象中
    path="log/"+name+".txt"
    file_handler = logging.handlers.RotatingFileHandler(
        filename=path, maxBytes=10 * 1024 * 1024, backupCount=50, encoding="utf-8"
    )

    # 创建Formatter对象，设置日志输出格式，包含时间、日志器名字、行号、日志级别、日志信息
    if debug:
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s')
    else:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

