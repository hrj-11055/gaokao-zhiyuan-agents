import asyncio
import websockets
import uuid
import json
import gzip

# --- 用户提供的数据 ---
APPID = "3933647087"
TOKEN_1 = "1AX3n-Z-QU9X2nBJT3s9IN7dzFV-TK42" # 用户标注为 token
TOKEN_2 = "FfNecpmVNolVappmC8uvQL__A5GCEq0l" # 用户标注为 key
WS_URL = "wss://openspeech.bytedance.com/api/v1/tts/ws_binary"

async def test_auth(label, headers, token_to_use):
    print(f"--- 测试: {label} ---")
    try:
        async with websockets.connect(WS_URL, additional_headers=headers) as ws:
            header = bytes([0x11, 0x10, 0x11, 0x01])
            req = {
                "app": {"appid": APPID, "token": token_to_use, "cluster": "volcano_tts"},
                "user": {"uid": "debug"},
                "audio": {"voice_type": "zh_male_m191_uranus_bigtts", "encoding": "mp3"},
                "request": {"reqid": str(uuid.uuid4()), "text": "测试", "text_type": "plain", "operation": "query"}
            }
            payload = gzip.compress(json.dumps(req).encode('utf-8'))
            await ws.send(header + len(payload).to_bytes(4, 'big') + payload)
            
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            msg_type = (response[1] >> 4) & 0x0f
            if msg_type == 0x0f:
                err_code = int.from_bytes(response[4:8], 'big')
                print(f"结果: 失败 (错误码 {err_code})")
                return False
            else:
                print("结果: ✅ 成功!")
                return True
    except Exception as e:
        print(f"结果: 异常 ({type(e).__name__})")
        return False

async def main():
    # 组合 1: Bearer; Token1 (Bearer 风格)
    await test_auth("Bearer; Token1", {"Authorization": f"Bearer; {TOKEN_1}"}, TOKEN_1)
    
    # 组合 2: Bearer; Token2
    await test_auth("Bearer; Token2", {"Authorization": f"Bearer; {TOKEN_2}"}, TOKEN_2)
    
    # 组合 3: X-Api-App-Key (ASR 风格)
    await test_auth("X-Api-Headers Token1", {
        "X-Api-App-Key": APPID,
        "X-Api-Access-Key": TOKEN_1,
        "X-Api-Resource-Id": "volc.bigtts.sauc.duration"
    }, TOKEN_1)

    # 组合 4: X-Api-Headers Token2
    await test_auth("X-Api-Headers Token2", {
        "X-Api-App-Key": APPID,
        "X-Api-Access-Key": TOKEN_2,
        "X-Api-Resource-Id": "volc.bigtts.sauc.duration"
    }, TOKEN_2)

if __name__ == "__main__":
    asyncio.run(main())
