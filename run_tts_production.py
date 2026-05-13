import asyncio
import websockets
import uuid
import json
import gzip
import os
import time

# --- 配置 ---
APPID = "3933647087"
TOKEN = "1AX3n-Z-QU9X2nBJT3s9IN7dzFV-TK42"
VOICE_TYPE = "zh_male_m191_uranus_bigtts" # 云舟 2.0
WS_URL = "wss://openspeech.bytedance.com/api/v1/tts/ws_binary"
OUTPUT_DIR = "tmp/audio_test"
CONCURRENCY = 10

def build_request(text):
    return {
        "app": {
            "appid": APPID,
            "token": TOKEN,
            "cluster": "volcano_tts"
        },
        "user": {"uid": str(uuid.uuid4())},
        "audio": {
            "voice_type": VOICE_TYPE,
            "encoding": "mp3", 
            "speed_ratio": 1.0,
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0,
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "text_type": "plain",
            "operation": "query"
        }
    }

async def generate_audio(user_id):
    text = f"你好，我是高考志愿填报专家云舟。这是第{user_id + 1}号并发测试音频。很高兴能为你提供咨询服务。"
    file_path = f"{OUTPUT_DIR}/result_user_{user_id}.mp3"
    
    # 修正：websockets.connect 的参数名应为 additional_headers
    headers = {"Authorization": f"Bearer; {TOKEN}"}
    
    try:
        async with websockets.connect(WS_URL, additional_headers=headers) as ws:
            # 协议头: version=1, header_size=1, message_type=1 (Full Client Request), serialization=json(1), compression=gzip(1)
            header = bytes([0x11, 0x11, 0x11, 0x00])
            
            req_json = build_request(text)
            payload = gzip.compress(json.dumps(req_json).encode('utf-8'))
            
            # 发送请求: Header(4b) + PayloadSize(4b) + Payload
            await ws.send(header + len(payload).to_bytes(4, 'big') + payload)
            
            audio_data = bytearray()
            
            while True:
                response = await ws.recv()
                if not isinstance(response, bytes):
                    continue
                
                # 响应协议: Header(4b) | Sequence(4b) | PayloadSize(4b) | Payload
                msg_type = (response[1] >> 4) & 0x0f
                
                if msg_type == 0x0f: # Error Message
                    err_code = int.from_bytes(response[4:8], 'big')
                    err_msg_size = int.from_bytes(response[8:12], 'big')
                    err_msg = response[12:12+err_msg_size].decode('utf-8')
                    print(f"用户 {user_id} 报错: {err_code} - {err_msg}")
                    return False
                
                if msg_type == 0x09: # Full Server Response
                    payload_size = int.from_bytes(response[8:12], 'big')
                    payload = response[12:12+payload_size]
                    
                    # 检查是否压缩 (header byte 2 low 4 bits)
                    compression = response[2] & 0x0f
                    if compression == 0x01:
                        payload = gzip.decompress(payload)
                    
                    # TTS 协议中，如果是音频数据，直接累加
                    # 注意：如果是 JSON 响应（结束包），这里会报错，所以要判断
                    try:
                        # 尝试解析 JSON，如果成功说明是元数据包
                        json.loads(payload)
                        # 收到 JSON 响应通常意味着结束
                        break 
                    except:
                        # 解析失败，说明是二进制音频数据
                        audio_data.extend(payload)
            
            if audio_data:
                with open(file_path, "wb") as f:
                    f.write(audio_data)
                print(f"用户 {user_id}: 成功生成 {file_path}")
                return True
            else:
                print(f"用户 {user_id}: 未收到音频数据")
                return False
                
    except Exception as e:
        print(f"用户 {user_id} 异常: {e}")
        return False

async def main():
    print(f"--- 开始 10 并发 TTS 生产测试 ---")
    start = time.time()
    tasks = [generate_audio(i) for i in range(CONCURRENCY)]
    results = await asyncio.gather(*tasks)
    end = time.time()
    
    success = sum(1 for r in results if r)
    print(f"\n结果统计:")
    print(f"成功: {success}/{CONCURRENCY}")
    print(f"总耗时: {end - start:.2f}s")
    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    asyncio.run(main())
