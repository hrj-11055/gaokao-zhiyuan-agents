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
# 切换为女声：Tina老师 2.0
VOICE_TYPE = "zh_female_yingyujiaoxue_uranus_bigtts" 
WS_URL = "wss://openspeech.bytedance.com/api/v1/tts/ws_binary"
OUTPUT_DIR = "tmp/audio_test"
CONCURRENCY = 10

def build_request(text):
    return {
        "app": {"appid": APPID, "token": TOKEN, "cluster": "volcano_tts"},
        "user": {"uid": str(uuid.uuid4())},
        "audio": {"voice_type": VOICE_TYPE, "encoding": "mp3"},
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "text_type": "plain",
            "operation": "query"
        }
    }

async def generate_audio(user_id):
    text = f"同学你好，我是你的 AI 升学助手 Tina。这是第{user_id + 1}号并发测试音频。我会陪伴你一起规划高考志愿。"
    file_path = f"{OUTPUT_DIR}/tina_user_{user_id}.mp3"
    headers = {"Authorization": f"Bearer; {TOKEN}"}
    
    try:
        async with websockets.connect(WS_URL, additional_headers=headers) as ws:
            header = bytes([0x11, 0x10, 0x11, 0x01])
            req_json = build_request(text)
            payload = gzip.compress(json.dumps(req_json).encode('utf-8'))
            await ws.send(header + len(payload).to_bytes(4, 'big') + payload)
            
            audio_data = bytearray()
            while True:
                response = await asyncio.wait_for(ws.recv(), timeout=10.0)
                if not isinstance(response, bytes): continue
                
                msg_type = (response[1] >> 4) & 0x0f
                flags = response[1] & 0x0f
                
                payload_size = int.from_bytes(response[8:12], 'big')
                data = response[12 : 12 + payload_size]
                
                if msg_type == 0x0f: break
                
                audio_data.extend(data)
                if flags & 0x02: break

            if audio_data:
                with open(file_path, "wb") as f:
                    f.write(audio_data)
                print(f"Tina 用户 {user_id}: ✅ 生成成功 ({len(audio_data)} 字节)")
                return True
    except Exception as e:
        print(f"Tina 用户 {user_id} 失败: {e}")
        return False

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"--- 启动 10 路 Tina老师(女声) TTS 生产测试 ---")
    start = time.time()
    
    tasks = []
    for i in range(CONCURRENCY):
        tasks.append(generate_audio(i))
        await asyncio.sleep(0.5)
    
    results = await asyncio.gather(*tasks)
    end = time.time()
    
    print(f"\n结果: 成功 {sum(1 for r in results if r)}/{CONCURRENCY}, 耗时 {end-start:.2f}s")
    print(f"Tina 音频文件位于: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    asyncio.run(main())
