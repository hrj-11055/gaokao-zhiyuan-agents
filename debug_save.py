import asyncio
import websockets
import uuid
import json
import gzip
import os

APPID = "3933647087"
TOKEN = "1AX3n-Z-QU9X2nBJT3s9IN7dzFV-TK42"
VOICE_TYPE = "zh_male_m191_uranus_bigtts" 
WS_URL = "wss://openspeech.bytedance.com/api/v1/tts/ws_binary"

async def test_and_save():
    text = "你好，我是高考志愿填报专家云舟。欢迎使用语音咨询服务。"
    headers = {"Authorization": f"Bearer; {TOKEN}"}
    file_path = "tmp/audio_test/debug_output.mp3"
    os.makedirs("tmp/audio_test", exist_ok=True)
    
    print(f"Connecting...")
    async with websockets.connect(WS_URL, additional_headers=headers) as ws:
        header = bytes([0x11, 0x10, 0x11, 0x01])
        req = {
            "app": {"appid": APPID, "token": TOKEN, "cluster": "volcano_tts"},
            "user": {"uid": "debug"},
            "audio": {"voice_type": VOICE_TYPE, "encoding": "mp3"},
            "request": {"reqid": str(uuid.uuid4()), "text": text, "text_type": "plain", "operation": "query"}
        }
        await ws.send(header + len(gzip.compress(json.dumps(req).encode())).to_bytes(4, 'big') + gzip.compress(json.dumps(req).encode()))
        
        audio_data = bytearray()
        while True:
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                h1 = response[1]
                msg_type = (h1 >> 4) & 0x0f
                flags = h1 & 0x0f
                
                # 跳过 4字节 Header 和可能的 4字节 Sequence
                # 根据之前 Size=41292 来看，数据偏移很可能在 8 之后 (如果是 Type 11)
                # 我们尝试探测数据起始
                data = response[8:] # 默认尝试跳过 8 字节
                
                if msg_type == 0x0f:
                    print("Error received.")
                    break
                
                print(f"Received Type={msg_type}, Flags={flags}, Size={len(response)}")
                audio_data.extend(data)
                
                if flags & 0x02: # Last packet
                    print("Last packet detected.")
                    break
            except asyncio.TimeoutError:
                break
        
        if audio_data:
            with open(file_path, "wb") as f:
                f.write(audio_data)
            print(f"Saved to {file_path}")
            return True
    return False

if __name__ == "__main__":
    asyncio.run(test_and_save())
