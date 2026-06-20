# Distributed Patterns Album

> 一本对比业界主流分布式方案的小书。从 Kafka 的 pub/sub + append-only log，到 Redis 的主从复制，到 MySQL 的 binlog 流复制，再到 ResilientDB 的 BFT 共识 —— 同一个"分布式"的标签底下，每家在解决的痛点、付出的代价、适合的业务场景完全不同。

## 这本专辑的目标读者

- 已经会写后端，能 ship 一个能跑的 Web 服务
- 听说过 Kafka / Redis / MySQL / Raft / Paxos 这些词，但说不清它们为什么各自存在
- 想在面试 / 设计评审 / 看一份新系统源码时，能立刻定位"这是哪一家分布式哲学"

## 这本专辑不打算做的事

- 教你从零搭一个 Kafka 集群（去看官方 docs）
- 系统性讲共识算法证明（去看 *Designing Data-Intensive Applications* / Raft 论文）
- 给你一份框架推荐排行榜

## 章节列表

| #  | 主题                  | 一句话                                                       | 状态 |
| -- | --------------------- | ------------------------------------------------------------ | ---- |
| [00](./00-overview.md) | Overview              | 为什么"都叫分布式"但每家不同 + 本系列的 5 个对比维度        | done |
| [01](./01-kafka-pub-sub.md) | Kafka                 | Pub/sub + append-only log + partition/replication：用解耦换工程极简 | done |
| [02](./02-resilientdb-bft.md) | ResilientDB / BFT     | 不信任的节点之间怎么达成共识：从 PBFT 到 HotStuff           | TODO |
| [03](./03-redis-master-slave.md) | Redis 主从            | 单线程事件循环 + 异步复制：读扩展的极致代价                  | TODO |
| [04](./04-mysql-replication.md) | MySQL 复制            | binlog 流复制 + GTID：从 row-based 到 statement-based 的选择题 | TODO |
| [05](./05-comparison-matrix.md) | 横向对比              | 一致性 / 可用性 / 吞吐 / 容错 / 业务场景：一张表收口         | TODO |

## 怎么读

按章节顺序读最舒服 —— 00 给统一坐标系，01 之后每章都用同一组维度回答同一组问题。

不想全读：

- **求职面试**：01 + 05
- **判断"该不该上 Kafka"**：00 + 01
- **看懂区块链 / 共识算法**：02
- **设计高读 / 多写少系统**：03 + 04

## 关于这个 PR

这是一个 **discussion-only PR**，不期待 merge。GitHub PR 的 review 界面被当成这本专辑的展示页 + 评论入口。任何行级评论都欢迎；不 merge 是默认状态。

## 关于这个 repo

本专辑写在 `CMU-AI-Engineering-Labs` 这个 repo 的 `distributed-patterns-album` 分支上 —— 选择这个 repo 是因为它的 `lab02/mlip-lab-1/KafkaDemo.ipynb` 恰好是第 01 章的最小实操代码，本章会直接锚到那里。

## 术语表

- **broker**：消息系统里的"中间那个家伙"，把上游和下游解耦
- **partition**：把一个 topic / 表 / 文件切成 N 份，分摊到多机
- **replication**：把同一份数据复制 K 份到不同机器，挂一台从另一台读
- **leader / follower**：复制组里的主副本和从副本
- **WAL (Write-Ahead Log)**：状态变化先追加写到日志，再去改主数据
- **append-only**：只在末尾追加、从不修改中间的存储/日志结构
- **fsync**：把内核缓冲强制刷到物理磁盘的系统调用
- **offset**：consumer 在日志里的"读到第几条"的位置指针
