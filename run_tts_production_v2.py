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
VOICE_TYPE = "zh_male_m191_uranus_bigtts" 
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
    text = f"你好，我是高考志愿填报专家云舟。这是第{user_id + 1}号测试。我们正在验证并发性能。"
    file_path = f"{OUTPUT_DIR}/result_user_{user_id}.mp3"
    
    # 鉴权头
    headers = {"Authorization": f"Bearer; {TOKEN}"}
    
    try:
        # 强制使用 binary 模式
        async with websockets.connect(WS_URL, additional_headers=headers) as ws:
            # 1. 构造 Full Client Request
            # [0x11, 0x10, 0x11, 0x00] -> Version 1, Header Size 1, Type 1, No Sequence, JSON, Gzip
            header = bytes([0x11, 0x10, 0x11, 0x00])
            
            req_json = build_request(text)
            json_str = json.dumps(req_json)
            payload = gzip.compress(json_str.encode('utf-8'))
            payload_size = len(payload).to_bytes(4, 'big')
            
            # 发送二进制包
            await ws.send(header + payload_size + payload)
            
            audio_data = bytearray()
            
            while True:
                response = await ws.recv()
                if not isinstance(response, bytes):
                    continue
                
                # 解析头 (4字节)
                # response[0]: version & header_size
                # response[1]: message_type & specific_flags
                # response[2]: serialization & compression
                msg_type = (response[1] >> 4) & 0x0f
                
                if msg_type == 0x0f: # Error
                    print(f"用户 {user_id} 收到服务端错误")
                    break
                
                # 对于 TTS，通常返回的是 Full Server Response (Type 9)
                # 这种包有 4字节 Sequence (如果是特定 flag)
                # 我们先跳过 header(4b) 和可能的 sequence(4b)
                
                # 检查特定 flag 是否包含 sequence
                has_sequence = (response[1] & 0x01) or (response[1] & 0x02)
                data_offset = 8 if has_sequence else 4
                
                payload_size = int.from_bytes(response[data_offset : data_offset + 4], 'big')
                payload = response[data_offset + 4 : data_offset + 4 + payload_size]
                
                # 处理压缩
                compression = response[2] & 0x0f
                if compression == 0x01:
                    payload = gzip.decompress(payload)
                
                # 检查是否是 JSON (结果描述) 还是二进制音频
                if response[2] >> 4 == 0x01: # JSON 序列化
                    try:
                        resp_json = json.loads(payload)
                        if "code" in resp_json and resp_json["code"] != 3000:
                            print(f"用户 {user_id} 业务错误: {resp_json}")
                        if msg_type == 0x09 and (response[1] & 0x02): # 最后一包标识
                            break
                    except:
                        pass
                else:
                    # 二进制音频数据
                    audio_data.extend(payload)
                    
                # 如果是最后一包 (Type 9, flags include bit 1)
                if msg_type == 0x09 and (response[1] & 0x02):
                    break

            if audio_data:
                with open(file_path, "wb") as f:
                    f.write(audio_data)
                print(f"用户 {user_id}: 成功 -> {file_path} ({len(audio_data)} 字节)")
                return True
            else:
                print(f"用户 {user_id}: 未收集到音频")
                return False
                
    except Exception as e:
        print(f"用户 {user_id} 异常: {type(e).__name__} - {e}")
        return False

async def main():
    print(f"--- 启动 10 并发生产级 TTS 测试 ---")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    start = time.time()
    tasks = [generate_audio(i) for i in range(CONCURRENCY)]
    results = await asyncio.gather(*tasks)
    end = time.time()
    
    print(f"\n测试汇总: 成功 {sum(1 for r in results if r)}/{CONCURRENCY}, 耗时 {end-start:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())
