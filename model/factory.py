from abc import ABC,abstractmethod
from typing import Optional
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel

from langchain_openai import ChatOpenAI
from model.qwen_vl_embeddings import QwenVLEmbeddings
from utils.config_handler import rag_conf


class BaseModelFactory(ABC):
    @abstractmethod
    def generator(self)->Optional[Embeddings | BaseChatModel]:
        pass

class ChatModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return ChatOpenAI(
            model=rag_conf["chat_model_name"],
            api_key=rag_conf["chat_model_api_key"],
            base_url=rag_conf["chat_model_url"]
        )

class EmbeddingsModelFactory(BaseModelFactory):
    def generator(self) -> Optional[Embeddings | BaseChatModel]:
        return QwenVLEmbeddings(
            model=rag_conf["embedding_model_name"],
            api_key=rag_conf["embedding_model_api_key"],
        )

chat_model=ChatModelFactory().generator()
embedding_model=EmbeddingsModelFactory().generator()