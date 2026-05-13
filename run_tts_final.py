import asyncio
import websockets
import uuid
import json
import gzip
import os
import time

# --- 验证成功的配置 ---
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
            "encoding": "mp3"
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "text_type": "plain",
            "operation": "query"
        }
    }

async def generate_audio(user_id):
    text = f"你好，我是高考志愿填报专家云舟。这是并发测试中的第{user_id + 1}号音频。希望能对你的升学之路有所帮助。"
    file_path = f"{OUTPUT_DIR}/result_user_{user_id}.mp3"
    headers = {"Authorization": f"Bearer; {TOKEN}"}
    
    try:
        async with websockets.connect(WS_URL, additional_headers=headers) as ws:
            # Type 1: Full Client Request, Serialization: JSON, Compression: Gzip
            header = bytes([0x11, 0x10, 0x11, 0x01])
            req_json = build_request(text)
            payload = gzip.compress(json.dumps(req_json).encode('utf-8'))
            await ws.send(header + len(payload).to_bytes(4, 'big') + payload)
            
            audio_data = bytearray()
            while True:
                response = await ws.recv()
                if not isinstance(response, bytes): continue
                
                msg_type = (response[1] >> 4) & 0x0f
                if msg_type == 0x0f:
                    print(f"用户 {user_id} 收到错误")
                    break
                
                # 跳过 header(4b) 和可能的 sequence(4b)
                has_sequence = (response[1] & 0x01) or (response[1] & 0x02)
                data_offset = 8 if has_sequence else 4
                
                payload_size = int.from_bytes(response[data_offset : data_offset + 4], 'big')
                payload = response[data_offset + 4 : data_offset + 4 + payload_size]
                
                # 检查压缩
                if (response[2] & 0x0f) == 0x01:
                    payload = gzip.decompress(payload)
                
                # 检查序列化 (高 4 位)
                serialization = (response[2] >> 4) & 0x0f
                if serialization == 0x01: # JSON (通常是结束包或状态包)
                    try:
                        res = json.loads(payload)
                        if msg_type == 0x09 and (response[1] & 0x02): # 最后一包标识
                            break
                    except: pass
                else:
                    audio_data.extend(payload)
                
                if msg_type == 0x09 and (response[1] & 0x02):
                    break

            if audio_data:
                with open(file_path, "wb") as f:
                    f.write(audio_data)
                print(f"用户 {user_id}: ✅ 已保存 {file_path}")
                return True
    except Exception as e:
        print(f"用户 {user_id} 异常: {e}")
        return False

async def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    print(f"--- 启动 10 路语音合成 (带 0.5s 启动间隔) ---")
    start = time.time()
    
    tasks = []
    for i in range(CONCURRENCY):
        tasks.append(generate_audio(i))
        await asyncio.sleep(0.5) # 错开启动时间，避免 QPS 瞬时超限
    
    results = await asyncio.gather(*tasks)
    end = time.time()
    
    print(f"\n结果: 成功 {sum(1 for r in results if r)}/{CONCURRENCY}, 耗时 {end-start:.2f}s")
    print(f"音频文件已存储在 {OUTPUT_DIR}/ 目录下。")

if __name__ == "__main__":
    asyncio.run(main())
