import os
import sys
from pathlib import Path

if __name__ == "__main__" and not __package__:
    # 直接运行脚本时，让 Python 能找到项目根目录下的模块。
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.logger_handler import logger
from langchain_chroma import Chroma
from utils.config_handler import chroma_conf
from model.factory import embedding_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from utils.file_handler import get_file_md5_hex, listdir_with_allowed_type, txt_loader, md_loader
from utils.path_tool import get_abs_path

class VectorStoreService:
    def __init__(self) :
        self.vector_store=Chroma(
            collection_name=chroma_conf["collection_name"],
            embedding_function=embedding_model,
            persist_directory=get_abs_path(chroma_conf["persist_directory"])
        )

        self.spliter=RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
            length_function=len
        )
    
    def get_retriever(self):    #向量检索器
        return self.vector_store.as_retriever(search_kwargs={"k":chroma_conf["k"]})
    
    def load_document(self):
        '''从数据文件夹中读取数据文件，转为向量存入向量数据库'''
        def check_md5_hex(md5_for_check:str):
            if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
                open(get_abs_path(chroma_conf["md5_hex_store"]),'w',encoding='utf-8').close()
                return False

            with open(get_abs_path(chroma_conf["md5_hex_store"]),'r',encoding='utf-8') as f:
                for line in f.readlines():
                    line=line.strip()
                    if line==md5_for_check:
                        return True
            return False
        
        def save_md5_hex(md5_for_check:str):
            with open(get_abs_path(chroma_conf["md5_hex_store"]),'a',encoding='utf-8') as f:
                f.write(md5_for_check+'\n')

        def get_file_documents(read_path:str):
            if read_path.endswith("txt"):
                return txt_loader(read_path)

            if read_path.endswith("md"):
                return md_loader(read_path)
            
            return []
        
        allowed_files_path:tuple[str]=listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]),
            tuple(chroma_conf["allow_knowledge_file_type"])
        )

        for path in allowed_files_path: #遍历文件夹中的文件
            md5_hex=get_file_md5_hex(path)
            if check_md5_hex(md5_hex):  #检查文件md5是否已经存在
                logger.info(f"[加载知识库]{path}内容已经存在于知识库中，跳过")
                continue

            try:    #如果文件的md5不存在，则加载文件内容到向量库中
                documents:list[Document]=get_file_documents(path)   

                if not documents:   #检查文件是否不空
                    logger.error(f"[加载知识库]{path}内没有有效的文本内容，跳过")
                    continue

                split_document=self.spliter.split_documents(documents)  #文本分割

                if not split_document:
                    logger.error(f"[加载知识库]{path}分片没有有效的文本内容，跳过")

                self.vector_store.add_documents(split_document) #将分片内容存入向量库

                save_md5_hex(md5_hex)
            
                logger.info(f"[加载知识库]{path}内容加载成功")
            except Exception as e:
                logger.error(f"[加载知识库]{path}加载失败：{str(e)}",exc_info=True) #exc_info=True会记录详细的报错堆栈

if __name__=="__main__":
    vs=VectorStoreService()
    vs.load_document()



