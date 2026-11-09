'''日志工具'''
import logging
from utils.path_tool import get_abs_path
from datetime import datetime
import os

#日志保存的根目录
LOG_ROOT=get_abs_path("logs")

#确保日志目录存在
os.makedirs(LOG_ROOT,exist_ok=True)

#日志的格式配置
DEDAULT_LOG_FORMAT=logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

def get_logger(
        name:str="Agent",
        console_level:int=logging.INFO,
        file_level:int=logging.DEBUG,
        log_file=None
)->logging.Logger:
    
    logger=logging.getLogger(name)
    logger.setLevel(logging.DEBUG) #设置日志记录器的最低级别为DEBUG

    #避免重复添加handler
    if logger.handlers:     #logger的处理器列表，初始为空，再次调用相同名称时如果已有处理器，则直接返回
        return logger
    
    #控制台handler(处理器)
    console_handler=logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(DEDAULT_LOG_FORMAT)
    logger.addHandler(console_handler)  #把处理器绑定到loggers

    #文件handler
    if not log_file:    #日志文件的存放路径
        log_file=os.path.join(LOG_ROOT,f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    file_handler=logging.FileHandler(log_file,encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(DEDAULT_LOG_FORMAT)
    logger.addHandler(file_handler)

    return logger

#快速获取
logger=get_logger()

if __name__=="__main__":
    logger.info("这是一个信息日志")