/**
 * Redis 客户端封装
 * 
 * 只有在环境变量配置了 REDIS_HOST 时才会启用 Redis。
 * 否则会导出一个 null，业务代码需据此做降级处理。
 */
const Redis = require('ioredis');

let redis = null;

if (process.env.REDIS_HOST) {
  redis = new Redis({
    host: process.env.REDIS_HOST,
    port: process.env.REDIS_PORT || 6379,
    password: process.env.REDIS_PASSWORD || undefined,
    keyPrefix: 'gaokao:',
    // 限制重试策略，防止 Redis 连不上时阻塞服务启动
    retryStrategy(times) {
      const delay = Math.min(times * 50, 2000);
      return delay;
    }
  });

  redis.on('error', (err) => {
    console.error('Redis Client Error:', err.message);
  });

  redis.on('connect', () => {
    console.log('✅ Redis Connected');
  });
} else {
  console.log('ℹ️ Redis Not Configured, using In-Memory Fallback');
}

module.exports = redis;
