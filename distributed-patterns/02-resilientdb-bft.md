# 02 · ResilientDB / PBFT — 不信任的节点之间怎么达成共识

> **本章状态：占位骨架。完整稿待写。**

## 本章要回答的核心问题

1. 为什么普通的主从复制（Raft / Paxos）在区块链场景下不够用？—— Byzantine fault 跟 crash fault 的区别
2. PBFT 三轮投票（pre-prepare → prepare → commit）每一步在防什么？
3. 为什么 PBFT 在节点数 N 增大时性能急剧下降？后来的 HotStuff / DAG-BFT 怎么改进？
4. ResilientDB 在 PBFT 之上加了什么（GeoBFT 跨地域共识 / PoE / RCC / RingBFT / SpotLess）？
5. 跟 Kafka 的对比：信任模型从 honest 变成 Byzantine 之后，复杂度成本指数级上升 —— 业务场景必须值这个钱。

## 引用素材

- `incubator-resilientdb/README.md` —— 项目顶层介绍
- `incubator-resilientdb/raft_cpp_interview_questions.md` —— Raft 对比基线
- `incubator-resilientdb/raft_snapshot_plan.md` —— 快照机制
- PBFT 原论文（Castro & Liskov 1999）+ ResilientDB / HotStuff 论文

## 跟前面章节的关系

- 跟 [01 Kafka](./01-kafka-pub-sub.md)：Kafka 假设节点 honest，partition + replication 就够；BFT 假设节点可能恶意，要 3f+1 副本 + 多轮投票 + 数字签名。这两套机制不是"哪个更先进"，是 **解决不同信任模型** 的不同方案。
