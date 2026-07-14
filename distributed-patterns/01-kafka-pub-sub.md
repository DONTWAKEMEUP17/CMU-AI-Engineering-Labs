# 01 · Kafka — Pub/Sub + Append-Only Log

> **本章核心问题**：Kafka 是消息队列吗？为什么"队列"这个词其实是误称？为什么这套设计能扛 LinkedIn 那种规模？
>
> **本章配套实操代码**：[`lab02/mlip-lab-1/KafkaDemo.ipynb`](../lab02/mlip-lab-1/KafkaDemo.ipynb) —— 本章每讲到一个机制，都会指回这个 notebook 里对应的 cell。

## 1. Motivation —— Kafka 当年要解决的痛

回到 2010 年的 LinkedIn。月活 7000 万 - 1 亿，用户每秒都在产生事件：

- profile 更新（"张三把职位从软件工程师改成高级软件工程师"）
- 建立连接、私信、登录登出
- 页面浏览、搜索、点击
- 广告 impression / click / conversion

汇总下来，每天几十亿到几百亿条事件。这些事件后端有一堆系统等着吃：

- **搜索索引**：立刻更新，否则搜不到张三的新职位
- **推荐 / People You May Know**：要重算张三的人脉网络
- **数据仓库**：分析师明天要看"上周改职位人数"
- **风控**：一天改 50 次职位的可能是机器人
- **邮件触达 / A/B 实验 / 监控 / ML 训练数据 / 合规审计** —— 一条事件，10+ 个下游想要

最痛的不是事件多，是 **N 个上游 × M 个下游的对接关系**。每加一个新下游，要去找每个数据源对接一次；每加一个新数据源，要通知所有下游。当 LinkedIn 内部有 50 个事件源 × 30 个下游时，理论上 1500 条对接，每天都有人在 debug 哪根线又断了。

Jay Kreps（Kafka 作者）后来在《The Log: What every software engineer should know about real-time data's unifying abstraction》里把这件事叫 **"the integration problem"**。Kafka 的核心 motivation 不是"做个更快的消息队列"，是：

> **把所有事件变成一根总线 —— 上游只管往总线写一次，下游各自从总线读，互不知道彼此。N × M 变 N + M。**

记住这一句话。下面所有机制都是这个 motivation 的自然推论。

## 2. Pub/Sub —— 解耦怎么实现

实现"上下游互不知道"的通信模型叫 **publish-subscribe (pub/sub)**：

```
publisher  →  [ broker ]  →  subscriber_1
                         →  subscriber_2
                         →  subscriber_3
```

三个角色：

- **publisher**：发消息的人。只管把消息扔进 broker，**不知道**有谁会读
- **subscriber**：收消息的人。从 broker 拿消息，**不知道**消息是谁发的
- **broker**：中间那个家伙。它存在的全部意义就是让两边谁都不知道对面是谁

关键反直觉点：publisher 调 `send` 时 **根本不指定要发给谁**，只说"我要发到 `profile-updates` 这个 topic"。谁订阅了这个 topic，谁就能收到。这就是 N × M → N + M 的魔法发生的地方 —— publisher 不需要知道下游存在。

把 LinkedIn 套进去：

```
profile 服务  →  [ broker ]  →  搜索索引服务
                            →  推荐系统
                            →  风控
                            →  数据仓库 ETL
                            →  ...
```

profile 团队哪怕加 10 个新下游，他们的代码一行不用改。新下游团队自己去 broker 订阅 `profile-updates` 就完事。

**Lab 锚点**：[`KafkaDemo.ipynb`](../lab02/mlip-lab-1/KafkaDemo.ipynb) cell `560fd2bb` 定义了 topic 名 `f"lab02-{andrew_id}"`，cell `aa4679a1` 创建 producer，cell `a5e2f59f` 创建 consumer。producer 和 consumer 之间没有任何代码引用，只通过 topic 名字解耦 —— 这就是 pub/sub 在代码里长什么样。

## 3. "消息队列" 是历史误称 —— 内部是 append-only log

很多人脑子里把 Kafka 当"消息队列"，画面是 LeetCode 的 FIFO queue：push 进来、pop 出去就消失。或者像把 MySQL 当队列那种 `UPDATE status='done'` 模式。

**Kafka 内部根本不是队列**。它是一段 **append-only 日志（append-only log）**：

- 新消息只往末尾追加
- 中间的消息从不被修改 / 删除（直到过期）
- 每个 consumer 自己带一个 **offset（书签）** 指向"我读到第几条"
- 多个 consumer 各自独立读，互不影响

"消息队列"这个名字是营销词。RabbitMQ / ActiveMQ 那种确实是 FIFO 取走即消失的队列；Kafka 借用了这个词，但内部完全不一样。

这种 append-only 结构在工程里跨系统通用：

| 系统               | append-only 的部分                              |
| ------------------ | ----------------------------------------------- |
| MySQL              | binlog（每笔事务追加写）                        |
| LevelDB / RocksDB  | SSTable（LSM-tree 的 immutable segment）        |
| Raft / Paxos       | 共识 log（每条日志条目按 index 追加）           |
| 区块链             | 链上 block（每个 block 追加，前一个不可改）     |
| **Kafka**          | **topic 内部的 segment 文件**                   |

这一家思想还有 **WAL (Write-Ahead Log)**：状态变化先追加写到日志，再去改主数据，崩溃恢复时 replay 这段日志。Kafka 把整个系统建在这一个思想上。

**Lab 锚点**：[`KafkaDemo.ipynb`](../lab02/mlip-lab-1/KafkaDemo.ipynb) cell `a5e2f59f` 里设的 `auto_offset_reset='earliest'` 就是在说"我这个 consumer 的 offset 书签从最早一条开始"。如果设 `'latest'`，书签从最新追加位置开始，老消息一律跳过 —— 同一份日志在那躺着，consumer 选自己想读的位置即可。这就是 append-only 的精髓。

## 4. Append-only 的 trade-off

天下没有白吃的午餐。append-only 用 **失去某些能力** 换 **极致的写吞吐**。

**失去的**：

- **不能原地修改** 一条已写入的记录。想"修改 user_123 的 profile"只能再写一条新的，旧的还躺在那
- **不能高效按 key 随机查** 单条记录。log 是时间序、不是 key 序，要按 key 查得另建外部索引

**换来的**：

- **顺序写性能**：磁盘顺序写远比随机写快（SSD 上差几十倍，HDD 上差上百倍）。Kafka 写入吞吐能到 GB/s 量级就是因为这个
- **持久化简单**：append-only 就是 WAL 本体。崩溃恢复只需要 replay 日志，不需要复杂的回滚 / 撤销逻辑。具体能挡住多狠的断电，由 `acks` + `flush.messages` + `flush.ms` 这些 fsync 频率旋钮决定
- **分布式复制简单**：顺序写没并发冲突，复制起来天然简单。Raft / Paxos / Kafka 的 partition replication / 区块链 P2P 全吃这套

这条 trade-off 决定了 Kafka 适合什么、不适合什么：

- **适合**：事件流 / 日志 / 实时数据管道 / 解耦异步任务
- **不适合**：当数据库用（按主键查最新记录），当 KV 缓存用（`GET key` 立即返回）

## 5. 日志膨胀怎么办 —— retention 和 compaction

经典 follow-up：log 只追加不删，磁盘不爆吗？

LinkedIn 每天几百亿条事件，每条 1 KB ≈ 几 GB/s 写入，一周就是几百 TB。显然不能永远存下去。Kafka 提供 **两种正交的清理策略**：

### Retention（保留期）

> 到点就删，不管有没有 subscriber 读过。

配置项：

- `log.retention.hours`（默认 168 = 7 天）—— 按时间
- `log.retention.bytes` —— 按总大小

适合 **可丢失 / 可重算** 的数据：用户行为日志、监控指标、临时缓冲。"7 天前的数据没人在乎"是这类数据的本质。

### Log Compaction（日志压实）

> 按消息的 key 保留最新一份，旧的清掉。

适合 **状态快照** 数据。典型场景：你有个 topic 叫 `user-profile-updates`，每次用户改 profile 就发一条。下游推荐系统重启时，想知道 **每个用户当前最新的 profile**，不关心他过去 100 次修改。

开 compaction 后，broker 只保留每个 `user_id` 的最新一条；下游重启只需重读"每人最新一份"，省时间也省磁盘。这是搜广推系统里的常见用法。

两种策略可以混用：基础数据 topic 用 retention，状态快照 topic 用 compaction。

**反例 / 错误答案**：让 broker 维护一个"所有 subscriber 都读到哪了"的全局表，等所有人都读过的消息才删 —— 这违反了 pub/sub 解耦原则。subscriber 会动态增减，broker 不该知道有多少 subscriber 存在，否则就回到了 N × M 的耦合。**机制必须服从 motivation**。

## 6. 分布式 —— partition + replication

到这里讲的还是单机版 Kafka。但 LinkedIn 那种规模单机扛不住：

- **写入吞吐**：几 GB/s，单网卡塞死（10 Gbps 网卡顶天 1.25 GB/s）
- **存储**：几百 TB，单 SSD 装不下（20 TB 上限）
- **可用性**：单机宕机整条事件流断了
- **可靠性**：硬盘坏盘几天数据全没

所以 Kafka **从设计第一天就必须是分布式**。这不是"性能瓶颈"问题，是"单机根本不可能完成任务"。

### 撕日记的比喻

把一个 topic 想象成一本巨厚的日记本。一台服务器装不下，怎么办？

**第一步：撕成 N 本小册子（partition）**

```
profile-updates 这本巨厚日记
   ↓ 撕成 4 份
   ├── 小册子 0 → broker A
   ├── 小册子 1 → broker B
   ├── 小册子 2 → broker C
   └── 小册子 3 → broker D
```

producer 写新事件时按规则决定塞进哪本小册子。最常用规则：`hash(user_id) % 4`。这样 **同一个 user 的所有事件保证落到同一本册子里** —— 同 user 的事件能保证顺序（这个性质在 user-level 状态机里非常关键）。

consumer 想读全部？分别去 4 个 broker 上读自己负责的册子，并行 4 路。这是横向扩展的来源。

**第二步：每本小册子复印 K 份（replication）**

```
小册子 0：主本（leader）在 A，副本（follower）在 B 和 D
小册子 1：主本在 B，副本在 C 和 A
...
```

读写都走 leader。leader 挂了（broker A 宕机），剩下两个 follower 里推选一个当新 leader，继续读写。等 A 恢复，从新 leader 同步缺的内容追上。这就是 leader failover。

### Append-only + 分布式 = 最佳搭档

append-only 的"顺序写无并发冲突"性质在分布式里特别值钱：

- leader 把新消息追加写到自己 log，然后把这段 log 同步给 followers
- followers 也是 append 到自己 log 末尾，不需要复杂的 merge / conflict resolution
- 任何一台机器宕机重启，从 last known offset 继续 replay 就能追上

Raft / Paxos / 区块链 P2P / Kafka replication 都吃这套。这就是为什么 ResilientDB 那种 BFT 区块链系统底层也用 LevelDB（也是 append-only）—— 不是巧合，是 append-only 这套思想跨系统通用。**第 02 章会展开 BFT 那一支** 在节点不互信场景下怎么改这套。

## 7. 接 lab02 的最小实操

本章理论的最小实操就在这个 repo 的 [`lab02/mlip-lab-1/KafkaDemo.ipynb`](../lab02/mlip-lab-1/KafkaDemo.ipynb)。一一对应：

| 本章概念                         | KafkaDemo.ipynb 对应位置 |
| -------------------------------- | ------------------------ |
| **Topic 命名 + 隔离**            | cell `560fd2bb` —— `f"lab02-{andrew_id}"`（多人共享 broker 时用前缀防冲突） |
| **消息 schema + JSON 序列化**    | cell `3ace33c5` `make_city_data()` + cell `aa4679a1` `value_serializer` |
| **Producer 发消息 → broker**     | cell `aa4679a1` + cell `b67582ee`（`producer.flush()` 在退出前强制把缓冲全部送出 —— 不调用会丢消息） |
| **Consumer 拉消息 + offset**     | cell `a5e2f59f` —— `auto_offset_reset='earliest'` 控书签起点，`enable_auto_commit=True` 控书签提交频率 |
| **用 kcat 把 offset 看在眼里**   | cell `e19b63da` —— `-f "%o: %s\n"` 直接打印 offset，"按位置读"这件事看在眼里 |

把本章理论和这个 notebook 对照着看一遍，整个 Kafka 心智模型就立起来了。

---

## 一句话收口

> Kafka = **pub/sub 通信模型** + **append-only log 存储** + **partition / replication 分布式扩展**。三件事分别解决：解耦、写吞吐、扛规模。

下一章 [02 ResilientDB / BFT](./02-resilientdb-bft.md) 会跳到完全不同的信任模型 —— 当节点之间互相不信任时，partition + replication 这套不够了。
