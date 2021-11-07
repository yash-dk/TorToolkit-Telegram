class TtkUpload:
    # Common across all the objs
    cache_store = []

    def __init__(self,dburl=None):
        pass
        

    def register_upload(self,chat_id,mes_id,is_batch=False):

        chat_id = str(chat_id)
        mes_id = str(mes_id)

        record = {
            "chat_id":chat_id,
            "message_id":mes_id,
            "cancel":False,
            "is_batch":is_batch
        }

        self.cache_store.append(record)

    def cancel_download(self,chat_id,mes_id):
        chat_id = str(chat_id)
        mes_id = str(mes_id)

        for i in self.cache_store:
            if i["chat_id"] == chat_id and i["message_id"] == mes_id:
                i["cancel"] = True
                return True

        return False

    def get_cancel_status(self,chat_id,mes_id):
        chat_id = str(chat_id)
        mes_id = str(mes_id)

        for i in self.cache_store:
            if i["chat_id"] == chat_id and i["message_id"] == mes_id:
                return i["cancel"]

        return False


    def deregister_upload(self,chat_id,mes_id):
        chat_id = str(chat_id)
        mes_id = str(mes_id)
        
        for i in self.cache_store:
            if i["chat_id"] == chat_id and i["message_id"] == mes_id:
                try:
                    self.cache_store.remove(i)
                except:
                    pass

