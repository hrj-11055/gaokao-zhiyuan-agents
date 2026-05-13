const { textToSpeech } = require('./gaokao-proxy/lib/tts');
const fs = require('fs');

async function test() {
  console.log('Testing TTS logic...');
  try {
    const buffer = await textToSpeech('你好，我是雪峰老师。');
    console.log('Success! Buffer size:', buffer.length);
    fs.writeFileSync('test_tts_isolated.mp3', buffer);
    console.log('Saved to test_tts_isolated.mp3');
  } catch (err) {
    console.error('TTS Failed:', err);
  }
}

test();
