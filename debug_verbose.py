import asyncio
import websockets
import uuid
import json
import gzip
import time

# --- 验证成功的配置 ---
APPID = "3933647087"
TOKEN = "1AX3n-Z-QU9X2nBJT3s9IN7dzFV-TK42"
VOICE_TYPE = "zh_male_m191_uranus_bigtts" 
WS_URL = "wss://openspeech.bytedance.com/api/v1/tts/ws_binary"

async def debug_single_tts():
    text = "测试语音合成"
    headers = {"Authorization": f"Bearer; {TOKEN}"}
    
    print(f"Connecting to {WS_URL}...")
    try:
        async with websockets.connect(WS_URL, additional_headers=headers) as ws:
            header = bytes([0x11, 0x10, 0x11, 0x01])
            req = {
                "app": {"appid": APPID, "token": TOKEN, "cluster": "volcano_tts"},
                "user": {"uid": "debug_user"},
                "audio": {"voice_type": VOICE_TYPE, "encoding": "mp3"},
                "request": {"reqid": str(uuid.uuid4()), "text": text, "text_type": "plain", "operation": "query"}
            }
            payload = gzip.compress(json.dumps(req).encode('utf-8'))
            await ws.send(header + len(payload).to_bytes(4, 'big') + payload)
            print("Request sent.")
            
            while True:
                response = await asyncio.wait_for(ws.recv(), timeout=10.0)
                if not isinstance(response, bytes):
                    print(f"Received non-binary message: {response}")
                    continue
                
                # 解析头
                h0 = response[0]
                h1 = response[1]
                h2 = response[2]
                msg_type = (h1 >> 4) & 0x0f
                flags = h1 & 0x0f
                serialization = (h2 >> 4) & 0x0f
                compression = h2 & 0x0f
                
                print(f"Msg: Type={msg_type}, Flags={flags}, Serial={serialization}, Comp={compression}, Size={len(response)}")
                
                if msg_type == 0x0f:
                    err_code = int.from_bytes(response[4:8], 'big')
                    print(f"Error Code: {err_code}")
                    break
                
                if msg_type == 0x09: # Full Server Response
                    has_sequence = (flags & 0x01) or (flags & 0x02)
                    data_offset = 8 if has_sequence else 4
                    payload_size = int.from_bytes(response[data_offset : data_offset + 4], 'big')
                    print(f"  Payload Size: {payload_size}")
                    
                    if flags & 0x02:
                        print("  Last packet flag detected.")
                        break
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(debug_single_tts())
