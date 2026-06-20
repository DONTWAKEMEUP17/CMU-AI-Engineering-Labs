# 03 · Redis 主从 — 单线程事件循环 + 异步复制

> **本章状态：占位骨架。完整稿待写（可吸入 `redis_demo/REDIS_EVENT_MODEL.md` 134 行已成稿作为起点）。**

## 本章要回答的核心问题

1. Redis 为什么单线程还能扛几十万 QPS？—— epoll + IO 多路复用 + 内存数据结构
2. 主从复制是同步的还是异步的？为什么 Redis 选了异步默认？
3. 主挂了怎么 failover？Sentinel 和 Cluster 的差别？
4. 异步复制带来的数据丢失风险：业务可接受的边界在哪？
5. 读写分离实战：什么场景该走主、什么场景能容忍 stale read？

## 引用素材

- `redis_demo/REDIS_EVENT_MODEL.md` —— 已经写好的单线程事件循环讲解（134 行）
- `redis_demo/demo/` —— 配套示例代码
- Redis 官方 `replication.md` / `sentinel.md`

## 跟前面章节的关系

- 跟 [01 Kafka](./01-kafka-pub-sub.md)：Kafka 追求 **写吞吐**（顺序追加 log），Redis 追求 **读吞吐**（多个 slave 服务读）。设计哲学正好相反。
- 跟 [02 ResilientDB](./02-resilientdb-bft.md)：Redis 假设 master honest，failover 是 crash-recovery；BFT 假设 master 可能恶意，failover 走多轮共识。
