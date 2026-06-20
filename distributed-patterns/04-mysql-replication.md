# 04 · MySQL 复制 — binlog 流复制 + GTID

> **本章状态：占位骨架。完整稿待写。**

## 本章要回答的核心问题

1. binlog 到底是什么？为什么它是 MySQL 主从复制 + 时间点恢复 + CDC 全链路的核心？
2. row-based / statement-based / mixed binlog format 三选一：每种的代价是什么？
3. 异步复制 vs 半同步复制 vs 组复制（Group Replication）：CAP 上分别在哪？
4. GTID 出现之前 binlog position 切主有多痛？GTID 解决了什么？
5. CDC (Change Data Capture) 怎么把 binlog 喂给 Kafka / 下游搜索 / 数仓？（伏笔回 01）

## 引用素材

- MySQL 官方 replication 章节
- Maxwell / Debezium / Canal 三个 binlog 解析工具的对比
- 在第 01 章里提到过的"Kafka topic ≈ MySQL binlog" —— 这里把这个类比讲透

## 跟前面章节的关系

- 跟 [01 Kafka](./01-kafka-pub-sub.md)：第 01 章用 "MySQL binlog" 当 Kafka topic 的概念锚点；本章反过来讲 MySQL binlog 怎么变成 Kafka topic 的上游数据源（CDC 链路）。
- 跟 [03 Redis 主从](./03-redis-master-slave.md)：复制粒度从 Redis 的"逻辑命令"换成 MySQL 的"binlog event"；一致性保证升级，代价是吞吐下降。
