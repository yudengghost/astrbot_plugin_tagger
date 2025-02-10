from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.core.message.components import Image
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
import time
import aiohttp
import uuid
import json
import ssl

API_URL = "https://smilingwolf-wd-tagger.hf.space/gradio_api"

@register("tagger", "yudengghost", "一个用于识别图像tag标签的插件", "1.0.0", "https://github.com/yudengghost/astrbot_plugin_tagger")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.waiting_info = None
        self.session_id = str(uuid.uuid4())
    
    # 获取图片数据
    async def get_image_data(self, event: AstrMessageEvent, file_id: str) -> bytes:
        """从协议端API获取图片数据"""
        try:
            # 调用协议端API
            if event.get_platform_name() != "aiocqhttp":
                raise Exception("当前只支持QQ平台")
                
            assert isinstance(event, AiocqhttpMessageEvent)
            client = event.bot
            
            # 准备请求参数
            payloads = {
                "file_id": file_id
            }
            
            # 调用协议端API
            result = await client.api.call_action('get_image', **payloads)
            
            if not isinstance(result, dict):
                raise Exception("API返回格式错误")
                
            # 尝试从文件读取
            file_path = result.get('file')
            if file_path:
                try:
                    with open(file_path, 'rb') as f:
                        return f.read()
                except Exception as e:
                    raise Exception(f"从文件读取失败: {e}")
                    
            # 如果文件读取失败，尝试从URL下载
            url = result.get('url')
            if url:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                return await response.read()
                            else:
                                raise Exception(f"下载失败: {response.status}")
                except Exception as e:
                    raise Exception(f"从URL下载失败: {e}")
                    
            raise Exception("无法获取图片数据")
        except Exception as e:
            raise Exception(f"获取图片数据失败: {str(e)}")
    
    # 上传图片
    async def upload_image(self, session: aiohttp.ClientSession, image_bytes: bytes) -> str:
        """上传图片到API服务器"""
        try:
            # 准备文件数据
            form = aiohttp.FormData()
            form.add_field('files', image_bytes, filename='image.png')
            
            # 上传图片
            async with session.post(f"{API_URL}/upload", data=form) as response:
                if response.status != 200:
                    raise Exception(f"上传失败: HTTP {response.status}")
                    
                result = await response.json()
                return result[0]  # 返回图片的相对路径
                
        except Exception as e:
            raise Exception(f"上传图片失败: {str(e)}")
    
    # 加入分析队列
    async def join_queue(self, session: aiohttp.ClientSession, image_path: str) -> str:
        """加入分析队列"""
        try:
            # 准备请求数据
            data = {
                "data": [
                    {
                        "path": image_path,
                        "url": f"{API_URL}/file={image_path}",
                        "size": None,
                        "mime_type": ""
                    },
                    "SmilingWolf/wd-swinv2-tagger-v3",  # 模型名称
                    0.35,  # 阈值
                    False,
                    0.85,
                    False
                ],
                "event_data": None,
                "fn_index": 2,
                "trigger_id": 18, 
                "session_hash": self.session_id  # 生成一个随机session_hash
            }
            
            # 发送请求
            async with session.post(f"{API_URL}/queue/join", json=data) as response:
                if response.status != 200:
                    raise Exception(f"加入队列失败: HTTP {response.status}")
                    
                return 
                
        except Exception as e:
            raise Exception(f"加入队列失败: {str(e)}")
    
    # 获取分析结果
    async def get_result(self, session: aiohttp.ClientSession) -> str:
        """获取分析结果"""
        try:
            url = f"{API_URL}/queue/data"
            params = {
                "session_hash": self.session_id
            }
            
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"获取结果失败: HTTP {response.status}")
                
                # 读取SSE响应
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    if not line or not line.startswith('data: '):
                        continue
                        
                    # 解析JSON数据
                    try:
                        data = json.loads(line[6:])  # 跳过'data: '前缀
                        
                        # 检查是否是最终结果
                        if data.get('msg') == 'process_completed':
                            output = data.get('output', {})
                            result_data = output.get('data', [])
                            
                            if result_data and len(result_data) > 0:
                                return result_data[0]
                            return "❌ 未找到标签数据"
                            
                        elif data.get('msg') == 'close_stream':
                            break
                            
                    except json.JSONDecodeError:
                        continue
                
            return "❌ 未收到有效的分析结果"
            
        except Exception as e:
            raise Exception(f"获取结果失败: {str(e)}")
    
    # 分析图片
    async def analyze_image(self, image_bytes: bytes) -> str:
        """使用API分析图片标签"""
        try:
            # 创建不验证SSL的客户端
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                # 1. 上传图片
                image_path = await self.upload_image(session, image_bytes)
                
                # 2. 加入分析队列
                await self.join_queue(session, image_path)
                
                # 3. 获取结果
                return await self.get_result(session)
                
        except Exception as e:
            return f"❌ 调用API时出错：{str(e)}"
    
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
        yield event.make_result().message(f"{user_name}，请在60秒内发送一张图片，我将识别图像标签喵~")
        
    @filter.regex(".*")
    async def handle_message(self, event: AstrMessageEvent):
        """处理所有消息"""
        try:
            # 如果是tag命令，直接返回
            if event.get_message_str().strip().startswith("tag"):
                return
                
            # 检查是否有等待图片的状态
            if not self.waiting_info:
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
                return
                
            # 清除等待状态
            self.waiting_info = None
            
            # 发送处理中的提示
            yield (event.make_result()
                  .message("✅ 已收到图片")
                  .message("\n正在分析中..."))
            
            try:
                # 获取图片file_id
                file_id = image.file
                if not file_id:
                    yield event.make_result().message("❌ 无法获取图片ID")
                    return
                
                # 从协议端API获取图片数据
                image_data = await self.get_image_data(event, file_id)
                
                # 调用API分析图片
                tags = await self.analyze_image(image_data)
                
                # 返回分析结果
                yield event.make_result().message(f"分析结果：\n{tags}")
                
            except Exception as e:
                # 使用make_result创建错误提示
                yield (event.make_result()
                      .message("❌ 处理过程中出现错误")
                      .message(f"\n错误信息：{str(e)}"))
        except Exception as e:
            # 使用make_result创建错误提示
            yield (event.make_result()
                  .message("❌ 处理过程中出现错误")
                  .message(f"\n错误信息：{str(e)}"))
