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

def build_request(text):
    return {
        "app": {
            "appid": APPID,
            "token": TOKEN,
            "cluster": "volcano_tts" # 尝试默认 cluster
        },
        "user": {"uid": "test_debug"},
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

async def debug_tts():
    text = "测试连接"
    # 尝试 ASR 风格的 Header，有时在火山引擎中通用
    headers = {
        "X-Api-App-Key": APPID,
        "X-Api-Access-Key": TOKEN,
        "X-Api-Resource-Id": "volc.bigtts.sauc.duration"
    }
    
    print(f"尝试连接: {WS_URL}")
    try:
        async with websockets.connect(WS_URL, additional_headers=headers) as ws:
            print("连接已建立，正在发送请求...")
            
            # Type 1: Full Client Request, Serialization: JSON, Compression: Gzip
            header = bytes([0x11, 0x10, 0x11, 0x01]) # 最后一个字节 0x01 表示 Gzip
            
            req_json = build_request(text)
            payload = gzip.compress(json.dumps(req_json).encode('utf-8'))
            
            await ws.send(header + len(payload).to_bytes(4, 'big') + payload)
            
            print("请求已发送，等待响应...")
            
            # 设置一个超时，防止挂起
            response = await asyncio.wait_for(ws.recv(), timeout=10.0)
            
            print(f"收到响应，长度: {len(response)}")
            print(f"Header: {response[:4].hex()}")
            
            # 解析响应类型
            msg_type = (response[1] >> 4) & 0x0f
            if msg_type == 0x0f:
                print("服务端返回错误帧")
                err_code = int.from_bytes(response[4:8], 'big')
                print(f"错误码: {err_code}")
                
            return True
    except Exception as e:
        print(f"异常: {type(e).__name__} - {e}")
        return False

if __name__ == "__main__":
    asyncio.run(debug_tts())
