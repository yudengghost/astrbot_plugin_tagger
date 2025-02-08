from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.core.message.components import Image
import time

@register("tagger", "图片标签插件", "一个用于给图片添加标签的插件", "1.0.0", "repo url")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.waiting_info = None
    
    @filter.command("tag")
    async def tag(self, event: AstrMessageEvent):
        """给图片添加标签。发送此命令后，请在60秒内发送一张图片。"""
        user_id = event.get_sender_id()
        user_name = event.get_sender_name()
        
        # 设置等待图片的状态
        self.waiting_info = {
            'user_id': user_id,
            'start_time': time.time()
        }
        
        # 发送等待提示
        yield event.make_result().message(f"{user_name}，请在60秒内发送一张图片，我将为其添加标签")
        
    @filter.regex(".*")
    async def handle_message(self, event: AstrMessageEvent):
        print("触发")
        """处理所有消息"""
        # 如果是tag命令，直接返回
        if event.get_message_str().strip().startswith("tag"):
            print("tag")
            return
            
        # 检查是否有等待图片的状态
        if not self.waiting_info:
            print("no waiting")
            return
            
        # 检查是否是同一用户且在60秒内
        current_time = time.time()
        if (event.get_sender_id() != self.waiting_info['user_id'] or 
            current_time - self.waiting_info['start_time'] > 60):
            # 清除等待状态
            self.waiting_info = None
            yield event.make_result().message("❌ 超时了，请重新发送 /tag 命令")
            return
            
        # 检查消息中是否包含图片
        messages = event.get_messages()
        image = next((msg for msg in messages if isinstance(msg, Image)), None)
        if not image:
            print("no image")
            return
            
        # 清除等待状态
        self.waiting_info = None
        
        try:
            # 创建包含多个组件的响应
            yield (event.make_result()
                  .message("✅ 已收到图片")
                  .message("\n正在处理中..."))
            
            # TODO: 在这里添加图片标签处理逻辑
            # image.url 或 image.path 可以获取图片路径
            yield event.make_result().message("✅ 测试结果")
            
        except Exception as e:
            # 使用make_result创建错误提示
            yield (event.make_result()
                  .message("❌ 处理过程中出现错误")
                  .message(f"\n错误信息：{str(e)}"))