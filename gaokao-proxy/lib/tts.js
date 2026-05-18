const WebSocket = require('ws');
const uuid = require('uuid');
const zlib = require('zlib');
const util = require('util');

const gzip = util.promisify(zlib.gzip);

const APPID = process.env.VOLC_TTS_APPID;
const TOKEN = process.env.VOLC_TTS_TOKEN;
const WS_URL = "wss://openspeech.bytedance.com/api/v1/tts/ws_binary";
const VOICE_TYPE = "zh_female_yingyujiaoxue_uranus_bigtts";

async function textToSpeech(text) {
  if (!APPID || !TOKEN) {
    throw new Error('VOLC_TTS_APPID and VOLC_TTS_TOKEN must be set');
  }
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(WS_URL, {
      headers: { "Authorization": `Bearer; ${TOKEN}` }
    });

    const audioChunks = [];
    const requestId = uuid.v4();

    ws.on('open', async () => {
      try {
        const request = {
          app: { appid: APPID, token: TOKEN, cluster: "volcano_tts" },
          user: { uid: "user_client" },
          audio: {
            voice_type: VOICE_TYPE,
            encoding: "mp3",
            speed_ratio: 1.0,
            volume_ratio: 1.0,
            pitch_ratio: 1.0
          },
          request: {
            reqid: requestId,
            text: text,
            text_type: "plain",
            operation: "query"
          }
        };

        const header = Buffer.from([0x11, 0x10, 0x11, 0x01]);
        const payload = await gzip(JSON.stringify(request));
        const payloadSize = Buffer.alloc(4);
        payloadSize.writeUInt32BE(payload.length);

        ws.send(Buffer.concat([header, payloadSize, payload]));
      } catch (err) {
        ws.close();
        reject(err);
      }
    });

    ws.on('message', (data) => {
      if (!Buffer.isBuffer(data)) return;

      const msgType = (data[1] >> 4) & 0x0f;
      const flags = data[1] & 0x0f;
      
      if (msgType === 0x0f) {
        const code = data.readUInt32BE(4);
        ws.close();
        reject(new Error(`TTS Server Error: ${code}`));
        return;
      }

      // According to working python script:
      // Offset 8-12 is payload size
      // Offset 12+ is data
      if (data.length >= 12) {
        const payloadSize = data.readUInt32BE(8);
        const payload = data.slice(12, 12 + payloadSize);
        
        // Only collect if it's likely audio data (Type 11 usually is, or Type 9 with no serialization)
        // In our tests, Type 11 worked best.
        if (msgType === 0x0b || msgType === 0x09) {
           // We avoid JSON description packets by checking size or simple heuristics
           // But actually the python script just extended everything.
           // Let's check if it's NOT JSON
           if (payload.length > 0 && payload[0] !== 123) { // 123 is '{'
             audioChunks.push(payload);
           }
        }
      }

      if (flags & 0x02) {
        ws.close();
        resolve(Buffer.concat(audioChunks));
      }
    });

    ws.on('error', (err) => reject(err));
    ws.on('close', () => {
      if (audioChunks.length > 0) {
        resolve(Buffer.concat(audioChunks));
      } else {
        reject(new Error("TTS Connection closed without data"));
      }
    });

    setTimeout(() => {
      ws.close();
      if (audioChunks.length > 0) resolve(Buffer.concat(audioChunks));
      else reject(new Error("TTS Timeout"));
    }, 15000);
  });
}

module.exports = { textToSpeech };
